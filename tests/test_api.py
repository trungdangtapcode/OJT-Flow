from pathlib import Path

import httpx
import pytest

from ojtflow.config import clear_settings_cache
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import clear_workflow_service_cache, require_authentication


ROOT = Path(__file__).resolve().parents[1]


async def _client() -> httpx.AsyncClient:
    app = create_app()
    app.dependency_overrides[require_authentication] = lambda: None
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.mark.asyncio
async def test_api_routes_require_bearer_token() -> None:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/workflows")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_workflow_review_roundtrip(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/workflows",
            json={
                "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
                "data": text,
                "input_format": "csv",
                "target_format": "json",
                "schema_id": "lab_result_v1",
                "require_human_review": True,
            },
        )
        assert response.status_code == 200
        body = response.json()["data"]
        assert body["status"] == "needs_human_review"
        assert body["steps"]

        workflows = await client.get("/api/v1/workflows")
        assert workflows.status_code == 200
        assert workflows.json()["data"][0]["workflow_id"] == body["workflow_id"]

        reviews = await client.get("/api/v1/reviews")
        assert reviews.status_code == 200
        assert reviews.json()["data"][0]["review"]["review_id"] == body["review"]["review_id"]

        schemas = await client.get("/api/v1/schemas")
        assert schemas.status_code == 200
        assert schemas.json()["data"][0]["schema_id"] == "lab_result_v1"

        review_id = body["review"]["review_id"]
        approved = await client.post(
            f"/api/v1/review/{review_id}",
            json={"decision": "approve", "decided_by": "tester"},
        )
        assert approved.status_code == 200
        assert approved.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_api_direct_convert_validate_fhir_ocr_and_error(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        converted = await client.post(
            "/api/v1/convert",
            json={"data": "a,b\n1,2\n", "input_format": "csv", "target_format": "json"},
        )
        assert converted.status_code == 200
        assert converted.json()["data"]["output_format"] == "json"

        validated = await client.post(
            "/api/v1/validate",
            json={
                "data": (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text(),
                "input_format": "csv",
                "schema_id": "lab_result_v1",
            },
        )
        assert validated.status_code == 200
        issue_kinds = {
            issue["kind"]
            for issue in validated.json()["data"]["validation_report"]["issues"]
        }
        assert "missing_unit" in issue_kinds

        fhir = await client.post(
            "/api/v1/fhir/profile",
            json={"data": '{"resourceType":"Observation","status":"final"}'},
        )
        assert fhir.status_code == 200
        assert fhir.json()["data"]["profile"]["is_fhir_like"] is True

        ocr = await client.post(
            "/api/v1/ocr/evidence",
            json={
                "fields": [
                    {
                        "page": 1,
                        "name": "patient_id",
                        "value": "P001",
                        "bbox": [0, 0, 10, 10],
                        "confidence": 0.5,
                        "source_ref": "storage://doc/demo",
                    }
                ]
            },
        )
        assert ocr.status_code == 200
        assert ocr.json()["data"]["requires_review"] is True

        invalid = await client.post("/api/v1/convert", json={"data": "x", "target_format": "bad"})
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "request_validation_error"
