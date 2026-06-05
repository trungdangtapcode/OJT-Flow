from pathlib import Path
from datetime import datetime, timezone
import json
import re

import httpx
import pytest
from fastapi.routing import APIRoute

from ojtflow.config import clear_settings_cache, get_settings
from ojtflow.core.contracts.auth import (
    AuthenticatedSession,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.contracts.enums import DataFormat, ReviewDecision
from ojtflow.core.errors import DependencyUnavailableError
from ojtflow.data_tools.hashing import sha256_text
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import (
    bearer_scheme,
    clear_workflow_service_cache,
    get_auth_service,
    get_medical_evidence_service,
    get_retrieval_judgment_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.routes import runtime as runtime_routes


ROOT = Path(__file__).resolve().parents[1]


def _authenticated_session(
    user_id: str = "usr_api_test",
    email: str = "reviewer@example.com",
) -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    return AuthenticatedSession(
        user=UserRecord(
            user_id=user_id,
            google_sub=f"google-{user_id}",
            email=email,
            email_verified=True,
            display_name="API Reviewer",
            avatar_url=None,
            created_at=now,
            updated_at=now,
            last_login_at=now,
        ),
        session=SessionRecord(
            session_id=f"ses_{user_id}",
            user_id=user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


async def _authenticated_dependency() -> AuthenticatedSession:
    return _authenticated_session()


class FakeAuthService:
    def __init__(self) -> None:
        self.logged_out_token: str | None = None

    def google_authorization_url(self, redirect_uri=None):
        del redirect_uri
        return {
            "authorization_url": (
                "https://accounts.google.com/o/oauth2/v2/auth"
                "?client_id=test&state=fake-state"
            ),
            "state": "fake-state",
        }

    async def complete_google_login(self, code, state, user_agent=None, ip_address=None):
        del code, state, user_agent, ip_address
        return {
            "token_type": "bearer",
            "access_token": "raw-session-token",
            "expires_at": "2026-01-01T00:00:00+00:00",
            "user": {
                "user_id": "usr_test",
                "email": "user@example.com",
                "email_verified": True,
                "display_name": "Example User",
                "avatar_url": None,
            },
        }

    def logout(self, token: str) -> None:
        self.logged_out_token = token


async def _client() -> httpx.AsyncClient:
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


def _assert_success_envelope(response: httpx.Response) -> dict:
    body = response.json()
    assert set(body) >= {"data", "error"}
    assert body["error"] is None
    assert body["data"] is not None
    return body


def _assert_error_envelope(
    response: httpx.Response,
    *,
    expected_code: str,
    expected_workflow_id: str | None = None,
) -> dict:
    body = response.json()
    assert set(body) >= {"data", "error"}
    assert body["data"] is None
    assert body["error"]["code"] == expected_code
    assert isinstance(body["error"]["message"], str)
    assert isinstance(body["error"]["details"], dict)
    assert "workflow_id" in body["error"]
    assert body["error"]["workflow_id"] == expected_workflow_id
    return body


def _assert_no_store_headers(response: httpx.Response) -> None:
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"


def _route_dependency_calls(route: APIRoute) -> set[object]:
    calls: set[object] = set()
    stack = list(route.dependant.dependencies)
    while stack:
        dependency = stack.pop()
        calls.add(dependency.call)
        stack.extend(dependency.dependencies)
    return calls


def _route_for(app, method: str, path: str) -> APIRoute:
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            return route
    raise AssertionError(f"Route not found: {method} {path}")


def test_api_v1_route_handlers_use_response_envelopes() -> None:
    app = create_app()
    violations: list[str] = []

    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/v1"):
            continue
        source_file = Path(route.endpoint.__code__.co_filename)
        source = source_file.read_text(encoding="utf-8")
        function_source = _function_source(source, route.endpoint.__name__)
        if "return ok(" not in function_source:
            methods = ",".join(sorted(route.methods or []))
            violations.append(f"{methods} {route.path} -> {route.endpoint.__name__}")

    assert violations == []


def test_openapi_exposes_core_request_examples() -> None:
    schemas = create_app().openapi()["components"]["schemas"]

    workflow_examples = schemas["StartWorkflowRequest"]["examples"]
    assert any("2026/01/02" in example["data"] for example in workflow_examples)
    assert any(example["input_format"] == "csv" for example in workflow_examples)

    review_examples = schemas["SubmitReviewRequest"]["examples"]
    assert any(example["decision"] == "approve" for example in review_examples)
    assert any(example["decision"] == "clarify" for example in review_examples)

    conversion_examples = schemas["ConvertRequest"]["examples"]
    assert any(
        example["input_format"] == "csv" and example["target_format"] == "json"
        for example in conversion_examples
    )
    assert any(
        example["input_format"] == "json" and example["target_format"] == "yaml"
        for example in conversion_examples
    )

    validation_examples = schemas["ValidateRequest"]["examples"]
    assert any("2026/01/02" in example["data"] for example in validation_examples)
    assert any(example["schema_id"] == "lab_result_v1" for example in validation_examples)

    fhir_examples = schemas["FhirProfileRequest"]["examples"]
    assert any('"resourceType":"Observation"' in example["data"] for example in fhir_examples)
    assert any('"status":"final"' in example["data"] for example in fhir_examples)

    retrieval_examples = schemas["RetrievalSearchRequest"]["examples"]
    assert any("FHIR Observation" in example["query"] for example in retrieval_examples)
    assert any(example["schema_id"] == "lab_result_v1" for example in retrieval_examples)
    assert any("patient_id" in example["fields"] for example in retrieval_examples)
    assert any(example["clinical_domain"] == "laboratory" for example in retrieval_examples)
    assert any(example["trust_level"] == "approved" for example in retrieval_examples)

    ocr_examples = schemas["OcrEvidenceRequest"]["examples"]
    assert ocr_examples[0]["fields"][0]["confidence"] < 0.8
    assert ocr_examples[0]["fields"][0]["bbox"] == [72.0, 144.0, 96.0, 18.0]

    assistant_examples = schemas["AssistantChatRequest"]["examples"]
    assert any("HbA1c" in example["message"] for example in assistant_examples)
    assert any("data" in example["context"] for example in assistant_examples)


def test_api_contract_doc_covers_current_route_surface() -> None:
    route_pattern = re.compile(r"`(GET|POST|PUT|PATCH|DELETE) ([^`\s]+)`")
    documented_routes = {
        (method, path.split("?", 1)[0])
        for method, path in route_pattern.findall(
            (ROOT / "docs/api_contract_v0.md").read_text(encoding="utf-8")
        )
    }
    actual_routes: set[tuple[str, str]] = set()
    for route in create_app().routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or set():
            if method in {"HEAD", "OPTIONS"}:
                continue
            actual_routes.add((method, route.path))

    assert actual_routes - documented_routes == set()


@pytest.mark.asyncio
async def test_api_rejects_blank_medical_and_retrieval_boundary_strings(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        blank_requests = [
            await client.post(
                "/api/v1/retrieval/search",
                json={"query": "   ", "top_k": 2},
            ),
            await client.post(
                "/api/v1/assistant/chat",
                json={"message": "   "},
            ),
            await client.post("/api/v1/fhir/profile", json={"data": " \n\t "}),
            await client.post(
                "/api/v1/ocr/evidence",
                json={
                    "fields": [
                        {
                            "page": 1,
                            "name": "   ",
                            "value": "P001",
                            "bbox": [0, 0, 10, 10],
                            "confidence": 0.9,
                            "source_ref": "storage://doc/demo",
                        }
                    ]
                },
            ),
            await client.post(
                "/api/v1/ocr/evidence",
                json={
                    "fields": [
                        {
                            "page": 1,
                            "name": "patient_id",
                            "value": "P001",
                            "bbox": [0, 0, 10, 10],
                            "confidence": 0.9,
                            "source_ref": "   ",
                        }
                    ]
                },
            ),
        ]

        for response in blank_requests:
            assert response.status_code == 422
            _assert_error_envelope(response, expected_code="request_validation_error")

        normalized = await client.post(
            "/api/v1/ocr/evidence",
            json={
                "fields": [
                    {
                        "page": 1,
                        "name": "  patient_id  ",
                        "value": "P001",
                        "bbox": [0, 0, 10, 10],
                        "confidence": 0.9,
                        "source_ref": "  storage://doc/demo  ",
                    }
                ]
            },
        )

    assert normalized.status_code == 200
    body = normalized.json()["data"]
    assert body["fields"][0]["name"] == "patient_id"
    assert body["fields"][0]["source_ref"] == "storage://doc/demo"


@pytest.mark.asyncio
async def test_api_rejects_blank_workflow_and_direct_data_boundary_strings(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        blank_requests = [
            await client.post(
                "/api/v1/workflows",
                json={
                    "instruction": "   ",
                    "data": "date,patient_id,lab_name,value,unit\n",
                    "input_format": "csv",
                    "target_format": "json",
                    "schema_id": "lab_result_v1",
                    "require_human_review": True,
                },
            ),
            await client.post(
                "/api/v1/workflows",
                json={
                    "instruction": "Clean this CSV.",
                    "data": " \n\t ",
                    "input_format": "csv",
                    "target_format": "json",
                    "schema_id": "lab_result_v1",
                    "require_human_review": True,
                },
            ),
            await client.post(
                "/api/v1/convert",
                json={"data": " \n\t ", "input_format": "csv", "target_format": "json"},
            ),
            await client.post(
                "/api/v1/validate",
                json={"data": " \n\t ", "input_format": "csv", "schema_id": "lab_result_v1"},
            ),
        ]

    for response in blank_requests:
        assert response.status_code == 422
        _assert_error_envelope(response, expected_code="request_validation_error")


@pytest.mark.asyncio
async def test_request_validation_errors_do_not_echo_payload_input(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    sensitive_payload = {
        "patient_id": "P001",
        "patient_name": "Jane Example",
        "note": "HbA1c result should not be echoed in validation details",
    }

    async with await _client() as client:
        response = await client.post(
            "/api/v1/workflows",
            json={
                "instruction": "Clean this CSV.",
                "data": sensitive_payload,
                "input_format": "csv",
                "target_format": "json",
                "schema_id": "lab_result_v1",
                "require_human_review": True,
            },
        )

    assert response.status_code == 422
    body = _assert_error_envelope(response, expected_code="request_validation_error")
    response_text = response.text
    assert "P001" not in response_text
    assert "Jane Example" not in response_text
    assert "HbA1c result should not be echoed" not in response_text
    errors = body["error"]["details"]["errors"]
    assert errors
    assert all(error.get("input") == "<redacted>" for error in errors if "input" in error)


@pytest.mark.asyncio
async def test_path_identifiers_reject_encoded_blank_values(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        responses = [
            await client.get("/api/v1/workflows/%20"),
            await client.get("/api/v1/workflows/%20/events"),
            await client.get("/api/v1/workflows/%20/output"),
            await client.post("/api/v1/review/%20", json={"decision": "approve"}),
        ]

    for response in responses:
        assert response.status_code == 422
        body = _assert_error_envelope(response, expected_code="request_validation_error")
        assert body["error"]["workflow_id"] is None


@pytest.mark.asyncio
async def test_api_rejects_blank_optional_identifiers_and_filters(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        blank_requests = [
            await client.post(
                "/api/v1/workflows",
                json={
                    "instruction": "Clean this CSV.",
                    "data": "date,patient_id,lab_name,value,unit\n",
                    "input_format": "csv",
                    "target_format": "json",
                    "schema_id": "   ",
                    "require_human_review": True,
                },
            ),
            await client.post(
                "/api/v1/validate",
                json={
                    "data": "date,patient_id,lab_name,value,unit\n",
                    "input_format": "csv",
                    "schema_id": "   ",
                },
            ),
            await client.post(
                "/api/v1/retrieval/search",
                json={"query": "lab result schema", "schema_id": "   "},
            ),
            await client.post(
                "/api/v1/retrieval/search",
                json={"query": "lab result schema", "workflow_id": "   "},
            ),
            await client.post(
                "/api/v1/retrieval/search",
                json={"query": "lab result schema", "fields": ["date", "   "]},
            ),
            await client.post(
                "/api/v1/retrieval/search",
                json={"query": "lab result schema", "clinical_domain": "   "},
            ),
        ]

    for response in blank_requests:
        assert response.status_code == 422
        _assert_error_envelope(response, expected_code="request_validation_error")


@pytest.mark.asyncio
async def test_retrieval_route_trims_optional_query_context(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FakeWorkflowService:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def search_retrieval(self, query, owner_user_id=None):
            self.calls.append(
                {
                    "query": query.model_dump(mode="json"),
                    "owner_user_id": owner_user_id,
                }
            )
            return {
                "hits": [],
                "evidence": [],
                "trace": {
                    "strategy": "fake",
                    "query_variants": [],
                    "filters_applied": query.filters,
                    "candidates_seen": 0,
                    "final_hit_ids": [],
                    "warnings": [],
                },
                "handoff_context": {},
            }

    fake_service = FakeWorkflowService()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def fake_workflow_service() -> FakeWorkflowService:
        return fake_service

    app.dependency_overrides[get_workflow_service] = fake_workflow_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/retrieval/search",
            json={
                "query": "  lab result schema  ",
                "workflow_id": "  wf_example  ",
                "schema_id": "  lab_result_v1  ",
                "fields": ["  date  ", "  unit  "],
                "detected_format": "  csv  ",
                "resource_type": "  Observation  ",
                "clinical_domain": "  laboratory  ",
                "standard_system": "  UCUM  ",
                "trust_level": "approved",
                "filters": {
                    "source_type": "terminology_system",
                },
            },
        )

    assert response.status_code == 200
    assert fake_service.calls == [
        {
            "query": {
                "query": "lab result schema",
                "workflow_id": "wf_example",
                "fields": ["date", "unit"],
                "schema_id": "lab_result_v1",
                "detected_format": "csv",
                "resource_type": "Observation",
                "top_k": 5,
                "filters": {
                    "clinical_domain": "laboratory",
                    "standard_system": "UCUM",
                    "source_type": "terminology_system",
                    "trust_level": "approved",
                },
            },
            "owner_user_id": "usr_api_test",
        }
    ]


@pytest.mark.asyncio
async def test_retrieval_judgment_routes_use_authenticated_owner(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FakeRetrievalJudgmentService:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def list(self, **kwargs):
            self.calls.append({"method": "list", **kwargs})
            return [
                {
                    "judgment_id": "rj_existing",
                    "owner_user_id": kwargs["owner_user_id"],
                    "query": kwargs["query"],
                    "query_hash": "0" * 64,
                    "evidence_id": "ev_schema",
                    "source_id": "schema:lab_result_v1",
                    "source_type": "schema",
                    "source_version": None,
                    "run_id": kwargs["run_id"],
                    "search_signature": None,
                    "value": "relevant",
                    "rating": 3,
                    "metadata": {},
                    "created_at": "2026-06-04T00:00:00+00:00",
                    "updated_at": "2026-06-04T00:00:00+00:00",
                }
            ]

        def summary(self, **kwargs):
            self.calls.append({"method": "summary", **kwargs})
            return {
                "total_count": 1,
                "query_count": 1,
                "evidence_count": 1,
                "source_count": 1,
                "relevant_count": 1,
                "partial_count": 0,
                "not_relevant_count": 0,
                "average_rating": 3.0,
                "latest_updated_at": "2026-06-04T00:00:00+00:00",
                "sample_limit": kwargs["limit"],
                "value_counts": {
                    "relevant": 1,
                    "partial": 0,
                    "not_relevant": 0,
                },
            }

        def evaluate_ranked_results(self, **kwargs):
            self.calls.append({"method": "evaluate", **kwargs})
            return {
                "query": kwargs["query"],
                "ranked_evidence_ids": kwargs["ranked_evidence_ids"],
                "cutoff": kwargs["cutoff"],
                "judged_count": 1,
                "unjudged_count": 1,
                "relevant_count": 1,
                "partial_count": 0,
                "not_relevant_count": 0,
                "coverage_at_k": 0.5,
                "hit_rate_at_k": 1.0,
                "precision_at_k": 0.5,
                "judged_precision": 1.0,
                "average_precision_at_k": 1.0,
                "mrr_at_k": 1.0,
                "ndcg_at_k": 1.0,
                "average_rating": 3.0,
                "unjudged_evidence_ids": ["ev_missing"],
                "judgment_ids": ["rj_existing"],
                "recommendations": [],
            }

        def upsert(self, **kwargs):
            self.calls.append({"method": "upsert", **kwargs})
            return {
                "judgment_id": "rj_saved",
                "owner_user_id": kwargs["owner_user_id"],
                "query": kwargs["query"],
                "query_hash": "1" * 64,
                "evidence_id": kwargs["evidence_id"],
                "source_id": kwargs["source_id"],
                "source_type": kwargs["source_type"],
                "source_version": kwargs["source_version"],
                "run_id": kwargs["run_id"],
                "search_signature": kwargs["search_signature"],
                "value": kwargs["value"],
                "rating": kwargs["rating"],
                "metadata": kwargs["metadata"],
                "created_at": "2026-06-04T00:00:00+00:00",
                "updated_at": "2026-06-04T00:00:00+00:00",
            }

        def delete(self, **kwargs):
            self.calls.append({"method": "delete", **kwargs})

    fake_service = FakeRetrievalJudgmentService()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def fake_judgment_service() -> FakeRetrievalJudgmentService:
        return fake_service

    app.dependency_overrides[get_retrieval_judgment_service] = fake_judgment_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        listed = await client.get(
            "/api/v1/retrieval/judgments",
            params={"query": "FHIR Observation HbA1c", "run_id": "run_1"},
        )
        summary = await client.get(
            "/api/v1/retrieval/judgments/summary",
            params={"query": "FHIR Observation HbA1c", "limit": 100},
        )
        evaluated = await client.post(
            "/api/v1/retrieval/judgments/evaluate",
            json={
                "query": "FHIR Observation HbA1c",
                "ranked_evidence_ids": ["ev_schema", "ev_missing"],
                "cutoff": 2,
            },
        )
        saved = await client.put(
            "/api/v1/retrieval/judgments",
            json={
                "query": "FHIR Observation HbA1c",
                "evidence_id": "ev_schema",
                "source_id": "schema:lab_result_v1",
                "source_type": "schema",
                "value": "relevant",
                "rating": 3,
                "run_id": "run_1",
                "search_signature": "signature",
                "metadata": {"review_surface": "retrieval_console"},
            },
        )
        deleted = await client.delete("/api/v1/retrieval/judgments/rj_saved")

    assert listed.status_code == 200
    assert listed.json()["data"][0]["judgment_id"] == "rj_existing"
    assert summary.status_code == 200
    assert summary.json()["data"]["total_count"] == 1
    assert evaluated.status_code == 200
    assert evaluated.json()["data"]["coverage_at_k"] == 0.5
    assert evaluated.json()["data"]["hit_rate_at_k"] == 1.0
    assert evaluated.json()["data"]["mrr_at_k"] == 1.0
    assert evaluated.json()["data"]["ndcg_at_k"] == 1.0
    assert saved.status_code == 200
    assert saved.json()["data"]["judgment_id"] == "rj_saved"
    assert deleted.status_code == 200
    assert deleted.json()["data"] == {"deleted": True, "judgment_id": "rj_saved"}
    assert fake_service.calls[0] == {
        "method": "list",
        "owner_user_id": "usr_api_test",
        "query": "FHIR Observation HbA1c",
        "run_id": "run_1",
        "evidence_id": None,
        "limit": 500,
    }
    assert fake_service.calls[1] == {
        "method": "summary",
        "owner_user_id": "usr_api_test",
        "query": "FHIR Observation HbA1c",
        "limit": 100,
    }
    assert fake_service.calls[2] == {
        "method": "evaluate",
        "owner_user_id": "usr_api_test",
        "query": "FHIR Observation HbA1c",
        "ranked_evidence_ids": ["ev_schema", "ev_missing"],
        "cutoff": 2,
    }
    assert fake_service.calls[3]["method"] == "upsert"
    assert fake_service.calls[3]["owner_user_id"] == "usr_api_test"
    assert fake_service.calls[3]["value"] == "relevant"
    assert fake_service.calls[3]["metadata"] == {"review_surface": "retrieval_console"}
    assert fake_service.calls[4] == {
        "method": "delete",
        "owner_user_id": "usr_api_test",
        "judgment_id": "rj_saved",
    }


@pytest.mark.asyncio
async def test_retrieval_route_rejects_unknown_or_invalid_filter_keys(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FakeWorkflowService:
        def __init__(self) -> None:
            self.calls = 0

        def search_retrieval(self, query, owner_user_id=None):
            del query, owner_user_id
            self.calls += 1
            return {}

    fake_service = FakeWorkflowService()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def fake_workflow_service() -> FakeWorkflowService:
        return fake_service

    app.dependency_overrides[get_workflow_service] = fake_workflow_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        unknown_filter = await client.post(
            "/api/v1/retrieval/search",
            json={
                "query": "lab result schema",
                "filters": {"unsupported": "value"},
            },
        )
        invalid_filter_enum = await client.post(
            "/api/v1/retrieval/search",
            json={
                "query": "lab result schema",
                "filters": {"trust_level": "not_a_trust_level"},
            },
        )

    assert unknown_filter.status_code == 422
    _assert_error_envelope(unknown_filter, expected_code="request_validation_error")
    assert invalid_filter_enum.status_code == 422
    _assert_error_envelope(invalid_filter_enum, expected_code="request_validation_error")
    assert fake_service.calls == 0


@pytest.mark.asyncio
async def test_retrieval_reindex_route_delegates_to_workflow_service(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FakeWorkflowService:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def reindex_retrieval(self, *, include_seeded=True, include_corpus=True):
            self.calls.append(
                {
                    "include_seeded": include_seeded,
                    "include_corpus": include_corpus,
                }
            )
            return {
                "repository": "fake",
                "chunks_indexed": 3,
                "include_seeded": include_seeded,
                "include_corpus": include_corpus,
            }

    fake_service = FakeWorkflowService()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def fake_workflow_service() -> FakeWorkflowService:
        return fake_service

    app.dependency_overrides[get_workflow_service] = fake_workflow_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/retrieval/reindex",
            json={"include_seeded": False, "include_corpus": True},
        )

    assert response.status_code == 200
    assert _assert_success_envelope(response)["data"]["chunks_indexed"] == 3
    assert fake_service.calls == [
        {
            "include_seeded": False,
            "include_corpus": True,
        }
    ]


@pytest.mark.asyncio
async def test_retrieval_integrity_route_delegates_to_workflow_service(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FakeWorkflowService:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def retrieval_integrity_report(self, *, include_seeded=True, include_corpus=False):
            self.calls.append(
                {
                    "include_seeded": include_seeded,
                    "include_corpus": include_corpus,
                }
            )
            return {
                "repository": "fake",
                "status": "ok",
                "checked_scope": "seeded+corpus",
                "expected_source_count": 1,
                "indexed_source_count": 1,
                "ok_count": 1,
                "stale_count": 0,
                "missing_count": 0,
                "extra_count": 0,
                "checks": [],
                "warnings": [],
            }

    fake_service = FakeWorkflowService()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def fake_workflow_service() -> FakeWorkflowService:
        return fake_service

    app.dependency_overrides[get_workflow_service] = fake_workflow_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/api/v1/retrieval/integrity",
            params={"include_seeded": "true", "include_corpus": "true"},
        )

    assert response.status_code == 200
    assert _assert_success_envelope(response)["data"]["status"] == "ok"
    assert fake_service.calls == [
        {
            "include_seeded": True,
            "include_corpus": True,
        }
    ]


@pytest.mark.asyncio
async def test_health_route_is_raw_liveness_probe() -> None:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "data" not in response.json()
    assert "error" not in response.json()


def _function_source(source: str, function_name: str) -> str:
    marker = f"async def {function_name}("
    start = source.find(marker)
    if start == -1:
        marker = f"def {function_name}("
        start = source.find(marker)
    if start == -1:
        raise AssertionError(f"Function source not found: {function_name}")

    next_function = len(source)
    for next_marker in ("\nasync def ", "\ndef "):
        index = source.find(next_marker, start + len(marker))
        if index != -1:
            next_function = min(next_function, index)
    return source[start:next_function]


def test_private_api_routes_have_auth_dependency() -> None:
    app = create_app()
    public_routes = {
        ("GET", "/health"),
        ("GET", "/api/v1/auth/google/url"),
        ("GET", "/api/v1/auth/google/callback"),
    }
    violations: list[str] = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or set():
            if method in {"HEAD", "OPTIONS"}:
                continue
            route_key = (method, route.path)
            if route_key in public_routes:
                continue
            if require_authentication not in _route_dependency_calls(route):
                violations.append(f"{method} {route.path}")

    assert violations == []


def test_token_revocation_routes_keep_token_security_dependency() -> None:
    app = create_app()
    logout_route = _route_for(app, "POST", "/api/v1/auth/logout")

    assert bearer_scheme in _route_dependency_calls(logout_route)


def test_runtime_routes_use_api_settings_dependency() -> None:
    runtime_source = (ROOT / "src/ojtflow/interfaces/api/routes/runtime.py").read_text(
        encoding="utf-8",
    )

    assert "get_api_settings" in runtime_source
    assert "Depends(get_api_settings)" in runtime_source
    assert "get_settings(" not in runtime_source


@pytest.mark.asyncio
async def test_unhandled_api_errors_do_not_expose_internal_exception_types() -> None:
    app = create_app()

    @app.get("/api/v1/_test/unhandled")
    async def _unhandled_test_route() -> None:
        raise RuntimeError("database password leaked in stack detail")

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/_test/unhandled")

    assert response.status_code == 500
    body = _assert_error_envelope(response, expected_code="internal_error")
    assert body["error"]["message"] == "Internal server error"
    assert body["error"]["details"] == {}
    assert "RuntimeError" not in response.text
    assert "database password" not in response.text


@pytest.mark.asyncio
async def test_api_routes_require_session_envelope(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/workflows")
        workflow_summary = await client.get("/api/v1/workflows/summary")
        workflow_stats = await client.get("/api/v1/workflows/stats")
        reviews = await client.get("/api/v1/reviews")
        review_summary = await client.get("/api/v1/reviews/summary")
        schemas = await client.get("/api/v1/schemas")
        convert = await client.post(
            "/api/v1/convert",
            json={"data": "a,b\n1,2\n", "input_format": "csv", "target_format": "json"},
        )
        validate = await client.post(
            "/api/v1/validate",
            json={"data": "a,b\n1,2\n", "input_format": "csv"},
        )
        fhir = await client.post(
            "/api/v1/fhir/profile",
            json={"data": '{"resourceType":"Observation","status":"final"}'},
        )
        ocr = await client.post(
            "/api/v1/ocr/evidence",
            json={
                "fields": [
                    {
                        "page": 1,
                        "name": "patient_id",
                        "value": "P001",
                        "bbox": [0, 0, 10, 10],
                        "confidence": 0.9,
                        "source_ref": "storage://doc/demo",
                    }
                ]
            },
        )
        parse_extract = await client.post(
            "/api/v1/parse/extract",
            files={"file": ("demo.txt", b"hello", "text/plain")},
        )
        parse_upload_workflow = await client.post(
            "/api/v1/parse/upload/workflow",
            data={"instruction": "Extract text", "target_format": "json"},
            files={"file": ("demo.txt", b"hello", "text/plain")},
        )
        extractors = await client.get("/api/v1/parse/extractors")
        runtime_config = await client.get("/api/v1/runtime/config")
        runtime_readiness = await client.get("/api/v1/runtime/readiness")
        assistant_tools = await client.get("/api/v1/assistant/tools")
        retrieval = await client.post(
            "/api/v1/retrieval/search",
            json={"query": "lab result schema", "top_k": 1},
        )
        retrieval_presets = await client.get("/api/v1/retrieval/presets")
        retrieval_search_options = await client.get("/api/v1/retrieval/search-options")
        retrieval_reindex = await client.post(
            "/api/v1/retrieval/reindex",
            json={"include_seeded": True, "include_corpus": True},
        )
        retrieval_sources = await client.get("/api/v1/retrieval/sources")
        retrieval_integrity = await client.get("/api/v1/retrieval/integrity")
        review = await client.post(
            "/api/v1/review/rev_missing",
            json={"decision": "approve"},
        )
        logout = await client.post("/api/v1/auth/logout")
        current_user = await client.get("/api/v1/auth/me")
        invalid = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid"},
        )

    assert response.status_code == 401
    _assert_error_envelope(response, expected_code="unauthorized")
    assert workflow_summary.status_code == 401
    _assert_error_envelope(workflow_summary, expected_code="unauthorized")
    assert workflow_stats.status_code == 401
    _assert_error_envelope(workflow_stats, expected_code="unauthorized")
    assert reviews.status_code == 401
    _assert_error_envelope(reviews, expected_code="unauthorized")
    assert review_summary.status_code == 401
    _assert_error_envelope(review_summary, expected_code="unauthorized")
    assert schemas.status_code == 401
    _assert_error_envelope(schemas, expected_code="unauthorized")
    assert convert.status_code == 401
    _assert_error_envelope(convert, expected_code="unauthorized")
    assert validate.status_code == 401
    _assert_error_envelope(validate, expected_code="unauthorized")
    assert fhir.status_code == 401
    _assert_error_envelope(fhir, expected_code="unauthorized")
    assert ocr.status_code == 401
    _assert_error_envelope(ocr, expected_code="unauthorized")
    assert parse_extract.status_code == 401
    _assert_error_envelope(parse_extract, expected_code="unauthorized")
    assert parse_upload_workflow.status_code == 401
    _assert_error_envelope(parse_upload_workflow, expected_code="unauthorized")
    assert extractors.status_code == 401
    _assert_error_envelope(extractors, expected_code="unauthorized")
    assert runtime_config.status_code == 401
    _assert_error_envelope(runtime_config, expected_code="unauthorized")
    assert runtime_readiness.status_code == 401
    _assert_error_envelope(runtime_readiness, expected_code="unauthorized")
    assert assistant_tools.status_code == 401
    _assert_error_envelope(assistant_tools, expected_code="unauthorized")
    assert retrieval.status_code == 401
    _assert_error_envelope(retrieval, expected_code="unauthorized")
    assert retrieval_presets.status_code == 401
    _assert_error_envelope(retrieval_presets, expected_code="unauthorized")
    assert retrieval_search_options.status_code == 401
    _assert_error_envelope(retrieval_search_options, expected_code="unauthorized")
    assert retrieval_reindex.status_code == 401
    _assert_error_envelope(retrieval_reindex, expected_code="unauthorized")
    assert retrieval_sources.status_code == 401
    _assert_error_envelope(retrieval_sources, expected_code="unauthorized")
    assert retrieval_integrity.status_code == 401
    _assert_error_envelope(retrieval_integrity, expected_code="unauthorized")
    assert review.status_code == 401
    _assert_error_envelope(review, expected_code="unauthorized")
    assert logout.status_code == 401
    _assert_error_envelope(logout, expected_code="unauthorized")
    _assert_no_store_headers(logout)
    assert current_user.status_code == 401
    _assert_error_envelope(current_user, expected_code="unauthorized")
    _assert_no_store_headers(current_user)
    assert invalid.status_code == 401
    _assert_error_envelope(invalid, expected_code="unauthorized")
    _assert_no_store_headers(invalid)


@pytest.mark.asyncio
async def test_workflow_routes_resolve_authentication_once(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()
    app = create_app()
    calls = 0

    async def authenticated_once() -> AuthenticatedSession:
        nonlocal calls
        calls += 1
        return _authenticated_session()

    app.dependency_overrides[require_authentication] = authenticated_once
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/workflows/stats")

    assert response.status_code == 200
    assert calls == 1


@pytest.mark.asyncio
async def test_runtime_config_exposes_sanitized_operational_settings(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "postgres")
    monkeypatch.setenv("OJT_DATABASE_URL", "postgresql://user:secret@example.test/db")
    monkeypatch.setenv("OJT_REDIS_URL", "redis://example.test:6379/0")
    monkeypatch.setenv("OJT_GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("OJT_GOOGLE_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("OJT_AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("OJT_AUTH_COOKIE_SAMESITE", "strict")
    monkeypatch.setenv("OJT_EMBEDDING_PROVIDER", "deterministic")
    monkeypatch.setenv("OJT_EMBEDDING_MODEL", "deterministic-hash-v0")
    monkeypatch.setenv("OJT_EMBEDDING_DIMENSIONS", "64")
    monkeypatch.setenv("OJT_RERANK_PROVIDER", "huggingface")
    monkeypatch.setenv("OJT_RERANK_MODEL", "BAAI/bge-reranker-base")
    monkeypatch.setenv("OJT_RERANK_DEVICE", "cuda")
    monkeypatch.setenv("OJT_RERANK_BATCH_SIZE", "4")
    monkeypatch.setenv("OJT_RERANK_CANDIDATE_LIMIT", "12")
    monkeypatch.setenv("OJT_RERANK_SCORE_WEIGHT", "0.2")
    monkeypatch.setenv("OJT_RETRIEVAL_DIVERSITY_ENABLED", "true")
    monkeypatch.setenv("OJT_RETRIEVAL_DIVERSITY_LAMBDA", "0.6")
    monkeypatch.setenv("OJT_RETRIEVAL_HNSW_EF_SEARCH", "150")
    monkeypatch.setenv("OJT_MAX_INLINE_DATA_BYTES", "4096")
    clear_settings_cache()
    clear_workflow_service_cache()

    try:
        async with await _client() as client:
            response = await client.get("/api/v1/runtime/config")

        assert response.status_code == 200
        body = _assert_success_envelope(response)["data"]
        assert body["status"] == "ok"
        assert body["storage_backend"] == "postgres"
        assert body["persistent_storage"] is True
        assert body["postgres_configured"] is True
        assert body["redis_configured"] is True
        assert body["knowledge_dir_configured"] is True
        assert body["migrations_dir_configured"] is True
        assert body["auth"]["google_oauth_configured"] is True
        assert body["auth"]["cookie_secure"] is True
        assert body["auth"]["cookie_effective_secure"] is True
        assert body["auth"]["cookie_samesite"] == "strict"
        assert body["embedding"]["provider"] == "deterministic"
        assert body["rerank"] == {
            "provider": "huggingface",
            "enabled": True,
            "model": "BAAI/bge-reranker-base",
            "device": "cuda",
            "batch_size": 4,
            "candidate_limit": 12,
            "score_weight": 0.2,
        }
        assert body["retrieval"]["diversity_enabled"] is True
        assert body["retrieval"]["diversity_lambda"] == 0.6
        assert body["retrieval"]["hnsw_ef_search"] == 150
        rule_packs = {pack["name"]: pack for pack in body["retrieval"]["rule_packs"]}
        assert rule_packs["query_expansion"]["status"] == "ok"
        assert rule_packs["query_expansion"]["rule_count"] > 0
        assert rule_packs["query_expansion"]["version"] == "retrieval_query_expansion_rules.v1"
        assert len(rule_packs["query_expansion"]["content_hash"]) == 64
        assert rule_packs["query_diagnostics"]["status"] == "ok"
        assert rule_packs["query_diagnostics"]["env_var"] == "OJT_QUERY_DIAGNOSTIC_RULES_PATH"
        assert rule_packs["query_diagnostics"]["source"] == "knowledge"
        assert rule_packs["query_diagnostics"]["version"] == (
            "retrieval_query_diagnostic_rules.v1"
        )
        assert len(rule_packs["query_diagnostics"]["content_hash"]) == 64
        assert body["upload"]["max_inline_data_bytes"] == 4096
        assert body["upload"]["allowed_extensions"]
        response_text = response.text
        assert "client-secret" not in response_text
        assert "secret@example" not in response_text
        assert "knowledge/" not in response_text
        assert "sql/postgres" not in response_text
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_runtime_retrieval_settings_endpoint_persists_and_reloads(
    monkeypatch,
    tmp_path,
) -> None:
    runtime_path = tmp_path / "runtime_settings.json"
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_RUNTIME_SETTINGS_PATH", str(runtime_path))
    clear_settings_cache()
    clear_workflow_service_cache()

    try:
        async with await _client() as client:
            response = await client.put(
                "/api/v1/runtime/retrieval-settings",
                json={
                    "retrieval_framework": "llamaindex",
                    "retrieval_candidate_multiplier": 3,
                    "retrieval_min_candidates": 9,
                    "retrieval_vector_weight": 0.7,
                    "retrieval_bm25_weight": 0.3,
                    "retrieval_diversity_enabled": False,
                    "retrieval_diversity_lambda": 0.5,
                    "retrieval_hnsw_ef_search": 80,
                },
            )
            runtime_config = await client.get("/api/v1/runtime/config")

        assert response.status_code == 200
        data = _assert_success_envelope(response)["data"]
        assert data["reloaded"] is True
        assert data["settings"]["retrieval_framework"] == "llamaindex"
        assert data["settings"]["retrieval_candidate_multiplier"] == 3
        assert data["settings"]["retrieval_min_candidates"] == 9
        assert data["settings"]["retrieval_vector_weight"] == 0.7
        assert data["settings"]["retrieval_bm25_weight"] == 0.3
        assert data["settings"]["retrieval_diversity_enabled"] is False
        assert data["settings"]["retrieval_diversity_lambda"] == 0.5
        assert data["settings"]["retrieval_hnsw_ef_search"] == 80

        assert runtime_path.exists()
        saved = json.loads(runtime_path.read_text(encoding="utf-8"))
        assert saved == data["settings"]

        config = _assert_success_envelope(runtime_config)["data"]
        assert config["retrieval"]["framework"] == "llamaindex"
        assert config["retrieval"]["candidate_multiplier"] == 3
        assert config["retrieval"]["runtime_settings"] == data["settings"]
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_runtime_assistant_settings_endpoint_persists_and_reloads(
    monkeypatch,
    tmp_path,
) -> None:
    runtime_path = tmp_path / "runtime_settings.json"
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_RUNTIME_SETTINGS_PATH", str(runtime_path))
    clear_settings_cache()
    clear_workflow_service_cache()

    try:
        async with await _client() as client:
            response = await client.put(
                "/api/v1/runtime/assistant-settings",
                json={
                    "llm_provider": "openai",
                    "llm_model": "gpt-4.1-mini",
                    "llm_timeout_seconds": 45.0,
                    "llm_max_tool_calls": 6,
                },
            )
            runtime_config = await client.get("/api/v1/runtime/config")

        assert response.status_code == 200
        data = _assert_success_envelope(response)["data"]
        assert data["reloaded"] is True
        assert data["settings"]["llm_provider"] == "openai"
        assert data["settings"]["llm_model"] == "gpt-4.1-mini"
        assert data["settings"]["llm_timeout_seconds"] == 45.0
        assert data["settings"]["llm_max_tool_calls"] == 6

        assert runtime_path.exists()
        saved = json.loads(runtime_path.read_text(encoding="utf-8"))
        assert saved == data["settings"]

        config = _assert_success_envelope(runtime_config)["data"]
        assert config["llm"]["provider"] == "openai"
        assert config["llm"]["model"] == "gpt-4.1-mini"
        assert config["llm"]["timeout_seconds"] == 45.0
        assert config["llm"]["max_tool_calls"] == 6
        assert config["llm"]["runtime_settings"] == data["settings"]
        assert "openai_api_key" not in runtime_config.text
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_runtime_readiness_returns_sanitized_operational_checks(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_DATABASE_URL", "postgresql://user:secret@example.test/db")
    monkeypatch.setenv("OJT_REDIS_URL", "redis://secret-cache.example.test:6379/0")
    clear_settings_cache()
    clear_workflow_service_cache()

    try:
        async with await _client() as client:
            response = await client.get("/api/v1/runtime/readiness")

        assert response.status_code == 200
        body = _assert_success_envelope(response)["data"]
        assert body["status"] == "ready"
        checks = {check["name"]: check for check in body["checks"]}
        assert checks["settings"]["status"] == "ok"
        assert checks["artifact_directory"]["status"] == "ok"
        assert checks["retrieval_rule_packs"]["status"] == "ok"
        assert checks["retrieval_rule_packs"]["details"]["pack_count"] >= 6
        assert checks["retrieval_rule_packs"]["details"]["issue_count"] == 0
        assert checks["workflow_repository"]["status"] == "ok"
        assert checks["schema_inventory"]["details"]["schema_count"] >= 1
        assert checks["retrieval_inventory"]["details"]["source_count"] >= 1
        assert checks["retrieval_inventory"]["details"]["probe_hit_count"] >= 1
        assert checks["retrieval_inventory"]["details"]["probe_candidates_seen"] >= 1
        assert checks["retrieval_inventory"]["details"]["probe_strategy"] == "static_hybrid_rrf"
        assert isinstance(checks["retrieval_inventory"]["details"]["probe_warning_count"], int)
        assert checks["retrieval_inventory"]["details"]["probe_warning_count"] >= 0
        assert checks["session_cache"]["details"]["mode"] == "process_local"
        response_text = response.text
        assert "secret@example" not in response_text
        assert "secret-cache" not in response_text
        assert "/home/" not in response_text
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_runtime_readiness_requires_retrieval_rule_packs(
    monkeypatch,
    tmp_path,
) -> None:
    missing_registry = tmp_path / "missing_query_expansion_rules.json"
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_QUERY_EXPANSION_RULES_PATH", str(missing_registry))
    clear_settings_cache()
    clear_workflow_service_cache()

    try:
        async with await _client() as client:
            response = await client.get("/api/v1/runtime/readiness")

        assert response.status_code == 200
        body = _assert_success_envelope(response)["data"]
        checks = {check["name"]: check for check in body["checks"]}

        assert body["status"] == "not_ready"
        assert checks["retrieval_rule_packs"]["status"] == "error"
        assert checks["retrieval_rule_packs"]["details"]["issue_count"] == 1
        issue = checks["retrieval_rule_packs"]["details"]["packs"][0]
        assert issue["name"] == "query_expansion"
        assert issue["status"] == "missing"
        assert issue["source"] == "override"
        assert issue["env_var"] == "OJT_QUERY_EXPANSION_RULES_PATH"
        response_text = response.text
        assert str(missing_registry) not in response_text
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_runtime_readiness_requires_trusted_schema_inventory(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class ReadyWorkflowRepository:
        def stats(self, owner_user_id=None):
            del owner_user_id

            class Stats:
                total = 0

            return Stats()

    class EmptySchemaWorkflowService:
        workflows = ReadyWorkflowRepository()

        def list_schemas(self):
            return []

        def list_retrieval_sources(self):
            return []

        def search_retrieval(self, query):
            del query

            class Trace:
                strategy = "test"
                warnings = []
                candidates_seen = 0

            class Package:
                hits = []
                trace = Trace()

            return Package()

    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def empty_schema_workflow_service() -> EmptySchemaWorkflowService:
        return EmptySchemaWorkflowService()

    app.dependency_overrides[get_workflow_service] = empty_schema_workflow_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/runtime/readiness")

    assert response.status_code == 200
    body = _assert_success_envelope(response)["data"]
    assert body["status"] == "not_ready"
    checks = {check["name"]: check for check in body["checks"]}
    assert checks["schema_inventory"]["status"] == "error"
    assert checks["schema_inventory"]["details"] == {"schema_count": 0}


@pytest.mark.asyncio
async def test_runtime_readiness_requires_retrieval_sources(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class ReadyWorkflowRepository:
        def stats(self, owner_user_id=None):
            del owner_user_id

            class Stats:
                total = 0

            return Stats()

    class MissingRetrievalWorkflowService:
        workflows = ReadyWorkflowRepository()

        def list_schemas(self):
            return [{"schema_id": "lab_result_v1"}]

        def list_retrieval_sources(self):
            return []

        def search_retrieval(self, query):
            del query

            class Trace:
                strategy = "test"
                warnings = ["No retrieval chunks matched filters."]
                candidates_seen = 0

            class Package:
                hits = []
                trace = Trace()

            return Package()

    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def missing_retrieval_workflow_service() -> MissingRetrievalWorkflowService:
        return MissingRetrievalWorkflowService()

    app.dependency_overrides[get_workflow_service] = missing_retrieval_workflow_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/runtime/readiness")

    assert response.status_code == 200
    body = _assert_success_envelope(response)["data"]
    assert body["status"] == "not_ready"
    checks = {check["name"]: check for check in body["checks"]}
    assert checks["schema_inventory"]["status"] == "ok"
    assert checks["retrieval_inventory"]["status"] == "error"
    assert checks["retrieval_inventory"]["details"]["source_count"] == 0
    assert checks["retrieval_inventory"]["details"]["probe_hit_count"] == 0


def test_runtime_readiness_session_cache_checks_redis_reachability(monkeypatch) -> None:
    class ReachableRedisClient:
        def ping(self) -> bool:
            return True

    class ReachableRedisModule:
        @staticmethod
        def from_url(url: str, **kwargs):
            assert url == "redis://secret-cache.example.test:6379/0"
            assert kwargs["socket_connect_timeout"] == 1
            assert kwargs["socket_timeout"] == 1
            return ReachableRedisClient()

    monkeypatch.setattr(runtime_routes, "redis_client", ReachableRedisModule)

    check = runtime_routes._session_cache_check(
        "postgres",
        "redis://secret-cache.example.test:6379/0",
    )

    assert check["status"] == "ok"
    assert check["details"] == {"mode": "redis", "reachable": True}
    assert "secret-cache" not in json.dumps(check)


def test_runtime_readiness_session_cache_errors_when_redis_is_not_configured() -> None:
    check = runtime_routes._session_cache_check("postgres", "")

    assert check["status"] == "error"
    assert check["details"] == {"mode": "fallback"}


def test_runtime_readiness_session_cache_errors_for_invalid_redis_url(monkeypatch) -> None:
    class ValidatingRedisModule:
        @staticmethod
        def from_url(url: str, **kwargs):
            del url, kwargs
            raise ValueError("invalid Redis URL with secret details")

    monkeypatch.setattr(runtime_routes, "redis_client", ValidatingRedisModule)

    check = runtime_routes._session_cache_check("postgres", "redis://:bad-port")

    assert check["status"] == "error"
    assert check["details"] == {
        "mode": "fallback",
        "error_type": "ValueError",
    }
    assert "secret details" not in json.dumps(check)


def test_runtime_readiness_session_cache_errors_when_redis_is_unreachable(monkeypatch) -> None:
    class FailingRedisClient:
        def ping(self) -> bool:
            raise runtime_routes.RedisError("secret-cache.example.test refused connection")

    class FailingRedisModule:
        @staticmethod
        def from_url(url: str, **kwargs):
            del url, kwargs
            return FailingRedisClient()

    monkeypatch.setattr(runtime_routes, "redis_client", FailingRedisModule)

    check = runtime_routes._session_cache_check(
        "postgres",
        "redis://secret-cache.example.test:6379/0",
    )

    assert check["status"] == "error"
    assert check["details"] == {
        "mode": "fallback",
        "error_type": "RedisError",
    }
    assert "secret-cache" not in json.dumps(check)


def test_runtime_readiness_artifact_directory_probes_writable_dirs(
    monkeypatch,
    tmp_path,
) -> None:
    data_dir = tmp_path / "var"
    (data_dir / "datasets").mkdir(parents=True)
    (data_dir / "outputs").mkdir()
    monkeypatch.setenv("OJT_DATA_DIR", str(data_dir))
    clear_settings_cache()

    try:
        check = runtime_routes._artifact_directory_check(get_settings())
    finally:
        clear_settings_cache()

    assert check["status"] == "ok"
    assert check["summary"] == "Artifact directories are writable."
    assert check["details"]["data_dir"]["writable"] is True
    assert check["details"]["datasets_dir"]["writable"] is True
    assert check["details"]["outputs_dir"]["writable"] is True
    assert list(data_dir.rglob(".ojtflow-readiness-*.tmp")) == []


def test_runtime_readiness_artifact_directory_reports_missing_dirs(
    monkeypatch,
    tmp_path,
) -> None:
    data_dir = tmp_path / "missing-var"
    monkeypatch.setenv("OJT_DATA_DIR", str(data_dir))
    clear_settings_cache()

    try:
        check = runtime_routes._artifact_directory_check(get_settings())
    finally:
        clear_settings_cache()

    assert check["status"] == "error"
    assert check["details"]["required"] is True
    assert check["details"]["data_dir"] == {
        "exists": False,
        "is_dir": False,
        "writable": False,
    }
    assert check["details"]["datasets_dir"]["writable"] is False
    assert check["details"]["outputs_dir"]["writable"] is False
    assert str(data_dir) not in json.dumps(check)


@pytest.mark.asyncio
async def test_runtime_readiness_service_failures_are_sanitized(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FailingWorkflowRepository:
        def stats(self, owner_user_id=None):
            del owner_user_id
            raise RuntimeError("postgresql://user:secret@example.test/ojtflow failed")

    class FailingWorkflowService:
        workflows = FailingWorkflowRepository()

        def list_schemas(self):
            raise RuntimeError("schema file /home/operator/secret/schema.json failed")

        def list_retrieval_sources(self):
            raise RuntimeError("redis://secret-cache.example.test:6379/0 failed")

    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def failing_workflow_service() -> FailingWorkflowService:
        return FailingWorkflowService()

    app.dependency_overrides[get_workflow_service] = failing_workflow_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/runtime/readiness")

    assert response.status_code == 200
    body = _assert_success_envelope(response)["data"]
    assert body["status"] == "not_ready"
    checks = {check["name"]: check for check in body["checks"]}
    assert checks["workflow_repository"]["details"] == {"error_type": "RuntimeError"}
    assert checks["schema_inventory"]["details"] == {"error_type": "RuntimeError"}
    assert checks["retrieval_inventory"]["details"] == {"error_type": "RuntimeError"}
    response_text = response.text
    assert "secret@example" not in response_text
    assert "secret-cache" not in response_text
    assert "/home/operator" not in response_text


@pytest.mark.asyncio
async def test_inline_api_payloads_are_size_limited(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_MAX_INLINE_DATA_BYTES", "96")
    clear_settings_cache()
    clear_workflow_service_cache()

    oversized = "x" * 97

    try:
        async with await _client() as client:
            responses = [
                await client.post(
                    "/api/v1/workflows",
                    json={
                        "instruction": "Reject oversized inline workflow data.",
                        "data": oversized,
                        "input_format": "csv",
                        "target_format": "json",
                    },
                ),
                await client.post(
                    "/api/v1/convert",
                    json={"data": oversized, "input_format": "csv", "target_format": "json"},
                ),
                await client.post(
                    "/api/v1/validate",
                    json={"data": oversized, "input_format": "csv"},
                ),
                await client.post(
                    "/api/v1/fhir/profile",
                    json={"data": oversized},
                ),
                await client.post(
                    "/api/v1/ocr/evidence",
                    json={
                        "fields": [
                            {
                                "page": 1,
                                "name": "patient_id",
                                "value": oversized,
                                "bbox": [0, 0, 10, 10],
                                "confidence": 0.9,
                                "source_ref": "storage://doc/demo",
                            }
                        ]
                    },
                ),
                await client.post(
                    "/api/v1/retrieval/search",
                    json={"query": oversized, "top_k": 1},
                ),
            ]

        for response in responses:
            assert response.status_code == 413
            body = _assert_error_envelope(response, expected_code="upload_too_large")
            assert body["error"]["details"]["limit"] == 96
            assert body["error"]["details"]["byte_size"] > 96
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_auth_callback_sets_and_logout_clears_cookie() -> None:
    fake_service = FakeAuthService()
    app = create_app()
    async def fake_auth_service() -> FakeAuthService:
        return fake_service

    app.dependency_overrides[get_auth_service] = fake_auth_service
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        callback = await client.get("/api/v1/auth/google/callback?code=code&state=state")
        client.cookies.set("ojtflow_session", "raw-session-token")
        logout = await client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://localhost:5173"},
        )

    assert callback.status_code == 200
    callback_body = _assert_success_envelope(callback)["data"]
    assert callback_body["user"]["email"] == "user@example.com"
    assert callback_body["expires_at"] == "2026-01-01T00:00:00+00:00"
    assert "access_token" not in callback_body
    assert "token_type" not in callback_body
    callback_cookie = callback.headers["set-cookie"]
    assert "ojtflow_session=raw-session-token" in callback_cookie
    assert "HttpOnly" in callback_cookie
    assert "SameSite=lax" in callback_cookie
    _assert_no_store_headers(callback)
    assert logout.status_code == 200
    assert fake_service.logged_out_token == "raw-session-token"
    assert "ojtflow_session=" in logout.headers["set-cookie"]
    _assert_no_store_headers(logout)


@pytest.mark.asyncio
async def test_auth_callback_can_return_bearer_token_when_requested() -> None:
    fake_service = FakeAuthService()
    app = create_app()
    async def fake_auth_service() -> FakeAuthService:
        return fake_service

    app.dependency_overrides[get_auth_service] = fake_auth_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/api/v1/auth/google/callback?code=code&state=state&include_token=true"
        )

    assert response.status_code == 200
    body = _assert_success_envelope(response)["data"]
    assert body["token_type"] == "bearer"
    assert body["access_token"] == "raw-session-token"
    assert body["user"]["email"] == "user@example.com"
    _assert_no_store_headers(response)


@pytest.mark.asyncio
async def test_auth_dependency_failures_return_service_unavailable_envelope() -> None:
    class CacheUnavailableAuthService:
        def google_authorization_url(self, redirect_uri=None):
            del redirect_uri
            raise DependencyUnavailableError(
                "Redis session cache is unavailable.",
                details={"dependency": "redis", "operation": "set_oauth_state"},
            )

    app = create_app()
    async def unavailable_auth_service() -> CacheUnavailableAuthService:
        return CacheUnavailableAuthService()

    app.dependency_overrides[get_auth_service] = unavailable_auth_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/auth/google/url")

    assert response.status_code == 503
    body = _assert_error_envelope(response, expected_code="dependency_unavailable")
    assert body["error"]["details"] == {
        "dependency": "redis",
        "operation": "set_oauth_state",
    }


@pytest.mark.asyncio
async def test_auth_url_and_session_responses_are_not_cacheable() -> None:
    fake_service = FakeAuthService()
    app = create_app()
    async def fake_auth_service() -> FakeAuthService:
        return fake_service

    app.dependency_overrides[get_auth_service] = fake_auth_service
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        authorization_url = await client.get(
            "/api/v1/auth/google/url?redirect_uri=http://localhost:5173/auth/callback"
        )
        current_user = await client.get("/api/v1/auth/me")
        invalid_callback = await client.get("/api/v1/auth/google/callback?code=code")

    assert authorization_url.status_code == 200
    assert _assert_success_envelope(authorization_url)["data"]["state"] == "fake-state"
    _assert_no_store_headers(authorization_url)

    assert current_user.status_code == 200
    assert _assert_success_envelope(current_user)["data"]["user"]["email"] == (
        "reviewer@example.com"
    )
    _assert_no_store_headers(current_user)

    assert invalid_callback.status_code == 422
    _assert_error_envelope(invalid_callback, expected_code="request_validation_error")
    _assert_no_store_headers(invalid_callback)


@pytest.mark.asyncio
async def test_auth_cookie_samesite_none_forces_secure_cookie(monkeypatch) -> None:
    monkeypatch.setenv("OJT_AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("OJT_AUTH_COOKIE_SAMESITE", "none")
    clear_settings_cache()
    clear_workflow_service_cache()
    fake_service = FakeAuthService()
    app = create_app()
    async def fake_auth_service() -> FakeAuthService:
        return fake_service

    app.dependency_overrides[get_auth_service] = fake_auth_service
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    transport = httpx.ASGITransport(app=app)

    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            runtime = await client.get("/api/v1/runtime/config")
            callback = await client.get("/api/v1/auth/google/callback?code=code&state=state")
            client.cookies.set("ojtflow_session", "raw-session-token")
            logout = await client.post(
                "/api/v1/auth/logout",
                headers={"Origin": "http://localhost:5173"},
            )

        assert runtime.status_code == 200
        runtime_body = _assert_success_envelope(runtime)["data"]
        assert runtime_body["auth"]["cookie_secure"] is False
        assert runtime_body["auth"]["cookie_effective_secure"] is True
        assert runtime_body["auth"]["cookie_samesite"] == "none"

        assert callback.status_code == 200
        callback_cookie = callback.headers["set-cookie"]
        assert "SameSite=none" in callback_cookie
        assert "Secure" in callback_cookie

        assert logout.status_code == 200
        logout_cookie = logout.headers["set-cookie"]
        assert "SameSite=none" in logout_cookie
        assert "Secure" in logout_cookie
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_cookie_authenticated_writes_require_trusted_origin(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    try:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("ojtflow_session", "raw-session-token")
            missing_origin = await client.post("/api/v1/auth/logout")
            untrusted_origin = await client.post(
                "/api/v1/auth/logout",
                headers={"Origin": "https://attacker.example"},
            )
            malformed_origin = await client.post(
                "/api/v1/auth/logout",
                headers={"Origin": "https://example.test:badport"},
            )

        for response in [missing_origin, untrusted_origin, malformed_origin]:
            assert response.status_code == 401
            _assert_error_envelope(response, expected_code="unauthorized")
            assert "set-cookie" not in response.headers
            _assert_no_store_headers(response)
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_logout_rejects_invalid_session_token(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    try:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": "Bearer invalid-session-token"},
            )

        assert response.status_code == 401
        _assert_error_envelope(response, expected_code="unauthorized")
        assert "set-cookie" not in response.headers
        _assert_no_store_headers(response)
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_public_api_success_and_error_envelope_contracts(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    csv_text = "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n"

    async with await _client() as client:
        success_calls = [
            await client.post(
                "/api/v1/workflows",
                json={
                    "instruction": "Convert one clean lab row.",
                    "data": csv_text,
                    "input_format": "csv",
                    "target_format": "json",
                    "schema_id": "lab_result_v1",
                    "require_human_review": False,
                },
            ),
            await client.get("/api/v1/workflows"),
            await client.get("/api/v1/workflows/summary?page=1&page_size=5"),
            await client.get("/api/v1/workflows/stats"),
            await client.get("/api/v1/reviews"),
            await client.get("/api/v1/reviews/summary?status=all"),
            await client.get("/api/v1/schemas"),
            await client.post(
                "/api/v1/convert",
                json={"data": "a,b\n1,2\n", "input_format": "csv", "target_format": "json"},
            ),
            await client.post(
                "/api/v1/validate",
                json={"data": csv_text, "input_format": "csv", "schema_id": "lab_result_v1"},
            ),
            await client.post(
                "/api/v1/fhir/profile",
                json={"data": '{"resourceType":"Observation","status":"final"}'},
            ),
            await client.post(
                "/api/v1/ocr/evidence",
                json={
                    "fields": [
                        {
                            "page": 1,
                            "name": "patient_id",
                            "value": "P001",
                            "bbox": [0, 0, 10, 10],
                            "confidence": 0.9,
                            "source_ref": "storage://doc/demo",
                        }
                    ]
                },
            ),
            await client.post(
                "/api/v1/retrieval/search",
                json={"query": "lab result schema", "top_k": 2},
            ),
            await client.get("/api/v1/retrieval/sources"),
            await client.get("/api/v1/parse/extractors"),
        ]

        for response in success_calls:
            assert response.status_code == 200, response.text
            _assert_success_envelope(response)

        error_calls = [
            (await client.get("/api/v1/workflows/wf_missing"), 404, "not_found"),
            (
                await client.get("/api/v1/workflows?limit=0"),
                422,
                "request_validation_error",
            ),
            (
                await client.get("/api/v1/workflows?limit=101"),
                422,
                "request_validation_error",
            ),
            (
                await client.get("/api/v1/workflows/summary?page=0"),
                422,
                "request_validation_error",
            ),
            (
                await client.get("/api/v1/reviews?limit=0"),
                422,
                "request_validation_error",
            ),
            (
                await client.get("/api/v1/reviews?limit=101"),
                422,
                "request_validation_error",
            ),
            (
                await client.post("/api/v1/retrieval/search", json={"query": "", "top_k": 2}),
                422,
                "request_validation_error",
            ),
            (
                await client.post("/api/v1/convert", json={"data": "x", "target_format": "bad"}),
                422,
                "request_validation_error",
            ),
        ]

        for response, expected_status, expected_code in error_calls:
            assert response.status_code == expected_status
            _assert_error_envelope(response, expected_code=expected_code)


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

        summaries = await client.get("/api/v1/workflows/summary?page=1&page_size=10")
        assert summaries.status_code == 200
        summary_body = summaries.json()["data"]
        assert summary_body["total"] >= 1
        assert summary_body["items"][0]["workflow_id"] == body["workflow_id"]
        assert summary_body["items"][0]["issue_count"] > 0

        stats = await client.get("/api/v1/workflows/stats")
        assert stats.status_code == 200
        assert stats.json()["data"]["pending_reviews"] >= 1

        reviews = await client.get("/api/v1/reviews")
        assert reviews.status_code == 200
        assert reviews.json()["data"][0]["review"]["review_id"] == body["review"]["review_id"]

        review_summaries = await client.get("/api/v1/reviews/summary?status=pending")
        assert review_summaries.status_code == 200
        assert review_summaries.json()["data"]["items"][0]["review_id"] == body["review"]["review_id"]

        all_review_summaries = await client.get("/api/v1/reviews/summary?status=all")
        assert all_review_summaries.status_code == 200
        assert all_review_summaries.json()["data"]["total"] >= review_summaries.json()["data"]["total"]

        invalid_summary_sort = await client.get("/api/v1/workflows/summary?sort=bad")
        assert invalid_summary_sort.status_code == 422
        assert invalid_summary_sort.json()["error"]["code"] == "request_validation_error"

        schemas = await client.get("/api/v1/schemas")
        assert schemas.status_code == 200
        assert schemas.json()["data"][0]["schema_id"] == "lab_result_v1"

        review_id = body["review"]["review_id"]
        output_before_review = await client.get(f"/api/v1/workflows/{body['workflow_id']}/output")
        assert output_before_review.status_code == 404
        assert output_before_review.json()["error"]["code"] == "not_found"

        approved = await client.post(
            f"/api/v1/review/{review_id}",
            json={"decision": "approve", "decided_by": "spoofed-client-user"},
        )
        assert approved.status_code == 200
        approved_body = approved.json()["data"]
        assert approved_body["status"] == "completed"
        assert approved_body["review"]["decided_by"] == "usr_api_test"

        output = await client.get(f"/api/v1/workflows/{body['workflow_id']}/output")
        assert output.status_code == 200
        output_body = output.json()["data"]
        assert output_body["workflow_id"] == body["workflow_id"]
        assert output_body["output_format"] == "json"
        assert output_body["output_hash"] == approved_body["output"]["transformation"]["output_hash"]
        assert output_body["byte_size"] == len(output_body["content"].encode("utf-8"))
        assert "[MASKED]" in output_body["content"]
        assert output_body["diff_summary"]["target_row_count"] == 3

        service = await get_workflow_service()
        output_ref = approved_body["output"]["transformation"]["output_ref"]
        service.datasets._text_by_ref[output_ref] = "tampered output"
        corrupted_output = await client.get(f"/api/v1/workflows/{body['workflow_id']}/output")
        assert corrupted_output.status_code == 409
        corrupted_body = _assert_error_envelope(
            corrupted_output,
            expected_code="artifact_integrity_error",
            expected_workflow_id=body["workflow_id"],
        )
        assert corrupted_body["error"]["details"]["artifact"] == "output"

        events = await client.get(f"/api/v1/workflows/{body['workflow_id']}/events")
        assert events.status_code == 200
        review_event = [
            event for event in events.json()["data"]
            if event["event_type"] == "review.decided"
        ][-1]
        assert review_event["actor_id"] == "usr_api_test"


@pytest.mark.asyncio
async def test_api_redacts_local_file_artifact_refs_from_public_payloads(monkeypatch, tmp_path) -> None:
    data_dir = tmp_path / "var"
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("OJT_DATABASE_PATH", str(tmp_path / "ojtflow.db"))
    monkeypatch.setenv("OJT_DATA_DIR", str(data_dir))
    clear_settings_cache()
    clear_workflow_service_cache()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()

    def assert_public_payload(payload: object) -> None:
        serialized = json.dumps(payload)
        assert "file://" not in serialized
        assert str(tmp_path) not in serialized

    try:
        async with await _client() as client:
            response = await client.post(
                "/api/v1/workflows",
                json={
                    "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
                    "data": text,
                    "input_format": "csv",
                    "target_format": "json",
                    "schema_id": "lab_result_v1",
                    "require_human_review": False,
                },
            )
            assert response.status_code == 200
            body = response.json()["data"]
            assert body["status"] == "completed"
            assert_public_payload(response.json())
            assert body["input"]["dataset_ref"].startswith("artifact://local/")
            assert body["output"]["transformation"]["output_ref"].startswith("artifact://local/")
            issue_refs = [
                issue["location"]["source_ref"]
                for issue in body["validation_report"]["issues"]
                if issue.get("location", {}).get("source_ref")
            ]
            assert issue_refs
            assert all(ref.startswith("artifact://local/") for ref in issue_refs)

            workflow = await client.get(f"/api/v1/workflows/{body['workflow_id']}")
            events = await client.get(f"/api/v1/workflows/{body['workflow_id']}/events")
            workflows = await client.get("/api/v1/workflows")
            assert workflow.status_code == 200
            assert events.status_code == 200
            assert workflows.status_code == 200
            assert_public_payload(workflow.json())
            assert_public_payload(events.json())
            assert_public_payload(workflows.json())

            internal_service = await get_workflow_service()
            internal_workflow = internal_service.get_workflow(
                body["workflow_id"],
                owner_user_id="usr_api_test",
            )
            assert internal_workflow.input is not None
            assert internal_workflow.input.dataset_ref.startswith("file://")
            assert internal_workflow.output is not None
            assert internal_workflow.output.transformation is not None
            assert internal_workflow.output.transformation.output_ref is not None
            assert internal_workflow.output.transformation.output_ref.startswith("file://")
    finally:
        clear_settings_cache()
        clear_workflow_service_cache()


@pytest.mark.asyncio
async def test_api_start_workflow_returns_structured_error_for_parse_failure(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/workflows",
            json={
                "instruction": "Parse this JSON.",
                "data": "{not valid json",
                "input_format": "json",
                "target_format": "json",
                "schema_id": "lab_result_v1",
                "require_human_review": True,
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert body["data"] is None
        assert body["error"]["code"] == "tool_execution_error"
        workflow_id = body["error"]["workflow_id"]
        assert workflow_id
        assert body["error"]["details"]["status"] == "failed"
        assert body["error"]["details"]["failure_code"] == "tool_execution_error"
        assert body["error"]["details"]["error_type"] == "ToolExecutionError"

        persisted = await client.get(f"/api/v1/workflows/{workflow_id}")
        assert persisted.status_code == 200
        workflow_body = persisted.json()["data"]
        assert workflow_body["status"] == "failed"
        assert workflow_body["failure"]["code"] == "tool_execution_error"
        assert "Invalid JSON" in workflow_body["failure"]["message"]
        assert workflow_body["output"] is None

        events = await client.get(f"/api/v1/workflows/{workflow_id}/events")
        assert events.status_code == 200
        assert any(event["event_type"] == "workflow.failed" for event in events.json()["data"])


@pytest.mark.asyncio
async def test_api_rejects_missing_requested_schema_and_persists_failed_workflow(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        validate_response = await client.post(
            "/api/v1/validate",
            json={
                "data": "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.1,%\n",
                "input_format": "csv",
                "schema_id": "missing_lab_schema",
            },
        )
        assert validate_response.status_code == 404
        validate_body = _assert_error_envelope(validate_response, expected_code="not_found")
        assert validate_body["error"]["details"]["schema_id"] == "missing_lab_schema"

        retrieval_response = await client.post(
            "/api/v1/retrieval/search",
            json={
                "query": "lab result schema",
                "schema_id": "missing_lab_schema",
            },
        )
        assert retrieval_response.status_code == 404
        retrieval_body = _assert_error_envelope(
            retrieval_response,
            expected_code="not_found",
        )
        assert retrieval_body["error"]["details"]["schema_id"] == "missing_lab_schema"

        workflow_response = await client.post(
            "/api/v1/workflows",
            json={
                "instruction": "Clean and validate this CSV.",
                "data": "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.1,%\n",
                "input_format": "csv",
                "target_format": "json",
                "schema_id": "missing_lab_schema",
                "require_human_review": True,
            },
        )
        assert workflow_response.status_code == 404
        workflow_error = workflow_response.json()
        assert workflow_error["data"] is None
        assert workflow_error["error"]["code"] == "not_found"
        workflow_id = workflow_error["error"]["workflow_id"]
        assert workflow_id
        assert isinstance(workflow_error["error"]["details"], dict)
        assert workflow_error["error"]["details"]["schema_id"] == "missing_lab_schema"
        assert workflow_error["error"]["details"]["failure_code"] == "not_found"

        persisted = await client.get(f"/api/v1/workflows/{workflow_id}")
        assert persisted.status_code == 200
        workflow_body = persisted.json()["data"]
        assert workflow_body["status"] == "failed"
        assert workflow_body["failure"]["code"] == "not_found"
        assert workflow_body["failure"]["details"]["schema_id"] == "missing_lab_schema"
        assert workflow_body["validation_report"] is None
        assert workflow_body["output"] is None
        assert not any(step["name"] == "retrieval" for step in workflow_body["steps"])

        events = await client.get(f"/api/v1/workflows/{workflow_id}/events")
        assert events.status_code == 200
        assert any(event["event_type"] == "workflow.failed" for event in events.json()["data"])


@pytest.mark.asyncio
async def test_api_review_approval_rejects_tampered_input_artifact(monkeypatch) -> None:
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

        service = await get_workflow_service()
        service.datasets._text_by_ref[body["input"]["dataset_ref"]] = text.replace("P001", "P999")

        approved = await client.post(
            f"/api/v1/review/{body['review']['review_id']}",
            json={"decision": "approve"},
        )
        assert approved.status_code == 409
        approved_body = _assert_error_envelope(
            approved,
            expected_code="artifact_integrity_error",
            expected_workflow_id=body["workflow_id"],
        )
        assert approved_body["error"]["details"]["artifact"] == "input"

        workflow = await client.get(f"/api/v1/workflows/{body['workflow_id']}")
        assert workflow.status_code == 200
        workflow_body = workflow.json()["data"]
        assert workflow_body["status"] == "failed"
        assert "ArtifactIntegrityError" in workflow_body["risk_flags"]
        assert workflow_body["output"] is None


@pytest.mark.asyncio
async def test_api_review_approval_returns_structured_error_for_resume_tool_failure(monkeypatch) -> None:
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

        service = await get_workflow_service()
        workflow = service.get_workflow(body["workflow_id"], owner_user_id="usr_api_test")
        bad_json = "{not valid json"
        service.datasets._text_by_ref[workflow.input.dataset_ref] = bad_json
        workflow.input.input_hash = sha256_text(bad_json)
        workflow.input.declared_format = DataFormat.JSON
        service.workflows.save(workflow)

        approved = await client.post(
            f"/api/v1/review/{body['review']['review_id']}",
            json={"decision": "approve"},
        )
        assert approved.status_code == 422
        approved_body = _assert_error_envelope(
            approved,
            expected_code="tool_execution_error",
            expected_workflow_id=body["workflow_id"],
        )
        assert approved_body["error"]["details"]["status"] == "failed"
        assert approved_body["error"]["details"]["failure_code"] == "tool_execution_error"

        workflow_response = await client.get(f"/api/v1/workflows/{body['workflow_id']}")
        assert workflow_response.status_code == 200
        workflow_body = workflow_response.json()["data"]
        assert workflow_body["status"] == "failed"
        assert workflow_body["review"]["status"] == "approved"
        assert workflow_body["failure"]["code"] == "tool_execution_error"
        assert "Invalid JSON" in workflow_body["failure"]["message"]
        assert workflow_body["output"] is None


@pytest.mark.asyncio
async def test_api_review_decision_cannot_be_applied_twice(monkeypatch) -> None:
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

        approved = await client.post(
            f"/api/v1/review/{body['review']['review_id']}",
            json={"decision": "approve"},
        )
        assert approved.status_code == 200

        duplicate = await client.post(
            f"/api/v1/review/{body['review']['review_id']}",
            json={"decision": "reject"},
        )
        assert duplicate.status_code == 403
        duplicate_body = _assert_error_envelope(
            duplicate,
            expected_code="policy_blocked",
            expected_workflow_id=body["workflow_id"],
        )
        assert duplicate_body["error"]["details"]["review_status"] == "approved"

        workflow = await client.get(f"/api/v1/workflows/{body['workflow_id']}")
        assert workflow.status_code == 200
        workflow_body = workflow.json()["data"]
        assert workflow_body["status"] == "completed"
        assert workflow_body["review"]["decision"] == "approve"


@pytest.mark.asyncio
async def test_api_clarify_keeps_review_pending_and_allows_later_approval(monkeypatch) -> None:
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
        review_id = body["review"]["review_id"]

        clarified = await client.post(
            f"/api/v1/review/{review_id}",
            json={
                "decision": "clarify",
                "payload": {"question": "Confirm unit normalization before approving."},
            },
        )
        assert clarified.status_code == 200
        clarified_body = clarified.json()["data"]
        assert clarified_body["status"] == "needs_human_review"
        assert clarified_body["review"]["status"] == "pending"
        assert clarified_body["review"]["decision"] is None
        assert clarified_body["review"]["clarification_requests"][0]["requested_by"] == "usr_api_test"
        assert clarified_body["output"] is None

        pending_reviews = await client.get("/api/v1/reviews/summary?status=pending")
        assert pending_reviews.status_code == 200
        assert pending_reviews.json()["data"]["items"][0]["review_id"] == review_id

        approved = await client.post(
            f"/api/v1/review/{review_id}",
            json={"decision": "approve"},
        )
        assert approved.status_code == 200
        approved_body = approved.json()["data"]
        assert approved_body["status"] == "completed"
        assert approved_body["review"]["status"] == "approved"
        assert approved_body["review"]["decision"] == "approve"
        assert approved_body["review"]["clarification_requests"]
        assert approved_body["output"] is not None


@pytest.mark.asyncio
async def test_api_review_decision_must_be_allowed_by_review_contract(monkeypatch) -> None:
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

        service = await get_workflow_service()
        workflow = service.get_workflow(body["workflow_id"], owner_user_id="usr_api_test")
        workflow.review.allowed_decisions = [ReviewDecision.REJECT]
        service.workflows.save(workflow)

        rejected = await client.post(
            f"/api/v1/review/{body['review']['review_id']}",
            json={"decision": "approve"},
        )
        assert rejected.status_code == 403
        rejected_body = _assert_error_envelope(
            rejected,
            expected_code="policy_blocked",
            expected_workflow_id=body["workflow_id"],
        )
        assert rejected_body["error"]["details"]["decision"] == "approve"
        assert rejected_body["error"]["details"]["allowed_decisions"] == ["reject"]

        workflow_response = await client.get(f"/api/v1/workflows/{body['workflow_id']}")
        assert workflow_response.status_code == 200
        workflow_body = workflow_response.json()["data"]
        assert workflow_body["status"] == "needs_human_review"
        assert workflow_body["review"]["status"] == "pending"
        assert workflow_body["output"] is None


@pytest.mark.asyncio
async def test_api_approve_with_edits_requires_explicit_action_payload(monkeypatch) -> None:
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

        edited = await client.post(
            f"/api/v1/review/{body['review']['review_id']}",
            json={"decision": "approve_with_edits"},
        )
        assert edited.status_code == 403
        edited_body = _assert_error_envelope(
            edited,
            expected_code="policy_blocked",
            expected_workflow_id=body["workflow_id"],
        )
        assert edited_body["error"]["details"]["required"] == "payload.actions"

        workflow_response = await client.get(f"/api/v1/workflows/{body['workflow_id']}")
        assert workflow_response.status_code == 200
        workflow_body = workflow_response.json()["data"]
        assert workflow_body["status"] == "needs_human_review"
        assert workflow_body["review"]["status"] == "pending"
        assert workflow_body["review"]["decision"] is None
        assert workflow_body["output"] is None


@pytest.mark.asyncio
async def test_api_approve_with_edits_applies_supported_action_payload(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()
    edited_action = {
        "action": "mask_sensitive_field_for_explanation",
        "field": "patient_id",
        "reason": "Keep patient identifiers masked in generated output.",
        "requires_review": True,
    }

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

        edited = await client.post(
            f"/api/v1/review/{body['review']['review_id']}",
            json={
                "decision": "approve_with_edits",
                "payload": {"actions": [edited_action]},
            },
        )
        assert edited.status_code == 200
        edited_body = edited.json()["data"]
        assert edited_body["status"] == "completed"
        assert edited_body["review"]["status"] == "approved_with_edits"
        assert edited_body["review"]["decision"] == "approve_with_edits"
        assert edited_body["review"]["decision_payload"] == {"actions": [edited_action]}
        assert [action["action"] for action in edited_body["transformation_plan"]["actions"]] == [
            "mask_sensitive_field_for_explanation"
        ]
        assert edited_body["output"]["transformation"]["diff_summary"]["actions_applied"] == [
            "mask_sensitive_field_for_explanation"
        ]

        output = await client.get(f"/api/v1/workflows/{body['workflow_id']}/output")
        assert output.status_code == 200
        assert "[MASKED]" in output.json()["data"]["content"]


@pytest.mark.asyncio
async def test_api_workflows_are_scoped_to_authenticated_user(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    csv_text = "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n"

    def authenticate_as(user_id: str) -> None:
        async def authenticated() -> AuthenticatedSession:
            return _authenticated_session(
                user_id=user_id,
                email=f"{user_id}@example.com",
            )

        app.dependency_overrides[require_authentication] = authenticated

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        authenticate_as("usr_owner_a")
        created = await client.post(
            "/api/v1/workflows",
            json={
                "instruction": "Convert one clean lab row.",
                "data": csv_text,
                "input_format": "csv",
                "target_format": "json",
                "schema_id": "lab_result_v1",
                "require_human_review": True,
            },
        )
        assert created.status_code == 200
        owner_a_workflow = created.json()["data"]
        workflow_id = owner_a_workflow["workflow_id"]
        review_id = owner_a_workflow["review"]["review_id"]
        assert owner_a_workflow["owner_user_id"] == "usr_owner_a"

        authenticate_as("usr_owner_b")
        hidden_list = await client.get("/api/v1/workflows")
        hidden_summary = await client.get("/api/v1/workflows/summary")
        hidden_summary_search = await client.get(
            "/api/v1/workflows/summary",
            params={"q": workflow_id},
        )
        hidden_stats = await client.get("/api/v1/workflows/stats")
        hidden_reviews = await client.get("/api/v1/reviews")
        hidden_review_summary = await client.get(
            "/api/v1/reviews/summary",
            params={"status": "all"},
        )
        hidden_review_summary_search = await client.get(
            "/api/v1/reviews/summary",
            params={"status": "all", "q": workflow_id},
        )
        hidden_workflow = await client.get(f"/api/v1/workflows/{workflow_id}")
        hidden_events = await client.get(f"/api/v1/workflows/{workflow_id}/events")
        hidden_review_decision = await client.post(
            f"/api/v1/review/{review_id}",
            json={"decision": "approve"},
        )
        hidden_retrieval = await client.post(
            "/api/v1/retrieval/search",
            json={
                "query": "lab result schema",
                "workflow_id": workflow_id,
                "top_k": 1,
            },
        )
        global_retrieval = await client.post(
            "/api/v1/retrieval/search",
            json={"query": "lab result schema", "top_k": 1},
        )

        assert hidden_list.status_code == 200
        assert hidden_list.json()["data"] == []
        assert hidden_summary.status_code == 200
        assert hidden_summary.json()["data"]["total"] == 0
        assert hidden_summary_search.status_code == 200
        assert hidden_summary_search.json()["data"]["total"] == 0
        assert hidden_stats.status_code == 200
        assert hidden_stats.json()["data"]["total"] == 0
        assert hidden_reviews.status_code == 200
        assert hidden_reviews.json()["data"] == []
        assert hidden_review_summary.status_code == 200
        assert hidden_review_summary.json()["data"]["total"] == 0
        assert hidden_review_summary_search.status_code == 200
        assert hidden_review_summary_search.json()["data"]["total"] == 0
        assert hidden_workflow.status_code == 404
        assert hidden_workflow.json()["error"]["code"] == "not_found"
        assert hidden_events.status_code == 404
        assert hidden_events.json()["error"]["code"] == "not_found"
        assert hidden_review_decision.status_code == 404
        assert hidden_review_decision.json()["error"]["code"] == "not_found"
        assert hidden_retrieval.status_code == 404
        assert hidden_retrieval.json()["error"]["code"] == "not_found"
        assert global_retrieval.status_code == 200
        assert global_retrieval.json()["data"]["evidence"]

        authenticate_as("usr_owner_a")
        visible_workflow = await client.get(f"/api/v1/workflows/{workflow_id}")
        visible_reviews = await client.get("/api/v1/reviews")
        visible_summary_search = await client.get(
            "/api/v1/workflows/summary",
            params={"q": workflow_id},
        )
        visible_review_summary_search = await client.get(
            "/api/v1/reviews/summary",
            params={"status": "all", "q": workflow_id},
        )
        approved = await client.post(
            f"/api/v1/review/{review_id}",
            json={"decision": "approve"},
        )
        owner_retrieval = await client.post(
            "/api/v1/retrieval/search",
            json={
                "query": "lab result schema",
                "workflow_id": workflow_id,
                "top_k": 1,
            },
        )

        assert visible_workflow.status_code == 200
        assert visible_workflow.json()["data"]["workflow_id"] == workflow_id
        assert visible_reviews.status_code == 200
        assert visible_reviews.json()["data"][0]["review"]["review_id"] == review_id
        assert visible_summary_search.status_code == 200
        assert visible_summary_search.json()["data"]["total"] == 1
        assert visible_summary_search.json()["data"]["items"][0]["workflow_id"] == workflow_id
        assert visible_review_summary_search.status_code == 200
        assert visible_review_summary_search.json()["data"]["total"] == 1
        assert visible_review_summary_search.json()["data"]["items"][0]["review_id"] == review_id
        assert owner_retrieval.status_code == 200
        assert owner_retrieval.json()["data"]["evidence"]
        assert approved.status_code == 200
        assert approved.json()["data"]["review"]["decided_by"] == "usr_owner_a"

        owner_output = await client.get(f"/api/v1/workflows/{workflow_id}/output")
        assert owner_output.status_code == 200
        assert owner_output.json()["data"]["workflow_id"] == workflow_id

        authenticate_as("usr_owner_b")
        hidden_completed_output = await client.get(f"/api/v1/workflows/{workflow_id}/output")
        assert hidden_completed_output.status_code == 404
        assert hidden_completed_output.json()["error"]["code"] == "not_found"


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
        convert_metadata = converted.json()["data"]["metadata"]
        assert convert_metadata["source_format"] == "csv"
        assert convert_metadata["target_format"] == "json"
        assert convert_metadata["source_row_count"] == 1
        assert convert_metadata["target_row_count"] == 1
        assert convert_metadata["output_hash"]
        assert convert_metadata["lossy"] is False
        assert convert_metadata["actions_applied"] == []

        lossy_csv = await client.post(
            "/api/v1/convert",
            json={
                "data": json.dumps([{"id": "one", "nested": {"value": 1}}]),
                "input_format": "json",
                "target_format": "csv",
            },
        )
        assert lossy_csv.status_code == 200
        assert lossy_csv.json()["data"]["metadata"]["lossy"] is True

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
        assert "Observation[0] is missing 'code'" in fhir.json()["data"]["profile"]["issues"]

        fhir_workflow = await client.post(
            "/api/v1/workflows",
            json={
                "instruction": "Profile this FHIR-like Observation and explain evidence.",
                "data": json.dumps(
                    {
                        "resourceType": "Observation",
                        "status": "final",
                        "code": {"text": "HbA1c"},
                        "subject": {"reference": "Patient/P001"},
                        "effectiveDateTime": "2026-01-01",
                        "valueQuantity": {"value": 7.4, "unit": "%"},
                    }
                ),
                "input_format": "json",
                "target_format": "json",
                "schema_id": None,
                "require_human_review": True,
            },
        )
        assert fhir_workflow.status_code == 200
        fhir_workflow_body = fhir_workflow.json()["data"]
        assert fhir_workflow_body["status"] == "completed"
        assert fhir_workflow_body["handoff_context"]["fhir_profile"]["resource_type"] == "Observation"
        assert fhir_workflow_body["handoff_context"]["fhir_handoff"]["graphner_ready"] is True
        assert any(
            evidence["source_id"] == "fhir_like:Observation"
            for evidence in fhir_workflow_body["retrieved_context"]
        )

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

        invalid_ocr = await client.post(
            "/api/v1/ocr/evidence",
            json={
                "fields": [
                    {
                        "page": 0,
                        "name": "",
                        "value": "P001",
                        "bbox": [0, 0, 10],
                        "confidence": 1.5,
                        "source_ref": "",
                    }
                ]
            },
        )
        assert invalid_ocr.status_code == 422
        assert invalid_ocr.json()["error"]["code"] == "request_validation_error"

        retrieval = await client.post(
            "/api/v1/retrieval/search",
            json={
                "query": "HbA1c lab CSV missing unit FHIR Observation",
                "fields": ["date", "patient_id", "lab_name", "value", "unit"],
                "schema_id": "lab_result_v1",
                "top_k": 4,
            },
        )
        assert retrieval.status_code == 200
        retrieval_data = retrieval.json()["data"]
        assert retrieval_data["trace"]["strategy"] == "static_hybrid_rrf"
        assert retrieval_data["trace"]["safety_flags"] == [
            "sensitive_field_context"
        ]
        assert retrieval_data["evidence"]
        assert retrieval_data["handoff_context"]["graph_context"]["graph_contract"] == (
            "graph_ner_handoff.v0"
        )

        sources = await client.get("/api/v1/retrieval/sources")
        assert sources.status_code == 200
        assert any(
            source["source_id"] == "standard:fhir_observation_r4"
            for source in sources.json()["data"]
        )

        presets = await client.get("/api/v1/retrieval/presets")
        assert presets.status_code == 200
        preset_data = presets.json()["data"]
        assert any(
            preset["preset_id"] == "lab_csv_observation_quality"
            and preset["schema_id"] == "lab_result_v1"
            and "patient_id" in preset["fields"]
            and preset["category"] == "workflow_validation"
            and "FHIR Observation" in preset["target_sources"]
            for preset in preset_data
        )
        assert any(
            preset["preset_id"] == "drug_safety_external_search"
            and preset["standard_system"] == "RxNorm"
            and "openfda_drug_event" in preset["launch_hint_targets"]
            for preset in preset_data
        )

        search_options = await client.get("/api/v1/retrieval/search-options")
        assert search_options.status_code == 200
        option_data = search_options.json()["data"]
        assert option_data["version"] == "retrieval_search_options.v1"
        assert any(
            option["value"] == "markdown" and option["label"] == "Markdown"
            for option in option_data["detected_formats"]
        )
        assert option_data["top_k_values"] == [3, 5, 8, 10, 15, 20]

        invalid = await client.post("/api/v1/convert", json={"data": "x", "target_format": "bad"})
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "request_validation_error"


@pytest.mark.asyncio
async def test_assistant_chat_runs_retrieval_tool_without_llm_tokens(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_LLM_PROVIDER", "disabled")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        response = await client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "Find evidence for HbA1c CSV missing unit FHIR Observation",
                "context": {
                    "schema_id": "lab_result_v1",
                    "fields": ["lab_name", "value", "unit"],
                    "clinical_domain": "laboratory",
                },
            },
        )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["mode"] == "deterministic"
    assert body["tool_calls"][0]["tool_name"] == "retrieval_search"
    assert body["tool_calls"][0]["status"] == "completed"
    assert body["tool_calls"][0]["output"]["evidence"]
    assert body["findings"][0]["title"] == "Trusted evidence retrieved"
    assert body["evidence_summary"][0]["source_id"]
    assert "Retrieved" in body["message"]


@pytest.mark.asyncio
async def test_assistant_tools_endpoint_returns_allowlist(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_LLM_PROVIDER", "disabled")
    clear_settings_cache()
    clear_workflow_service_cache()

    async with await _client() as client:
        response = await client.get("/api/v1/assistant/tools")

    assert response.status_code == 200
    tools = response.json()["data"]
    tool_names = {tool["name"] for tool in tools}
    assert "validate_with_evidence" in tool_names
    assert "start_workflow" in tool_names
    start_workflow = next(tool for tool in tools if tool["name"] == "start_workflow")
    assert start_workflow["requires_approval"] is True
    assert start_workflow["permission_scope"] == "data:transform"
    assert start_workflow["input_schema"]["type"] == "object"


@pytest.mark.asyncio
async def test_assistant_chat_requires_explicit_write_execution(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_LLM_PROVIDER", "disabled")
    clear_settings_cache()
    clear_workflow_service_cache()

    payload = {
        "message": "Start workflow for this messy lab CSV",
        "context": {
            "data": "date,patient_id,lab_name,value,unit\n2026/01/02,P002,HbA1c,,\n",
            "input_format": "csv",
            "target_format": "json",
            "schema_id": "lab_result_v1",
            "require_human_review": True,
        },
    }

    async with await _client() as client:
        gated = await client.post("/api/v1/assistant/chat", json=payload)
        allowed = await client.post(
            "/api/v1/assistant/chat",
            json={**payload, "execute_write_actions": True},
        )

    assert gated.status_code == 200
    gated_call = gated.json()["data"]["tool_calls"][0]
    assert gated_call["tool_name"] == "start_workflow"
    assert gated_call["status"] == "requires_approval"
    assert gated_call["requires_approval"] is True
    assert gated.json()["data"]["findings"][0]["severity"] == "action_required"

    assert allowed.status_code == 200
    allowed_call = allowed.json()["data"]["tool_calls"][0]
    assert allowed_call["tool_name"] == "start_workflow"
    assert allowed_call["status"] == "completed"
    assert allowed_call["output"]["workflow_id"].startswith("wf_")
    assert allowed_call["output"]["owner_user_id"] == "usr_api_test"
    assert allowed.json()["data"]["findings"][0]["title"] == "Workflow created"


@pytest.mark.asyncio
async def test_validate_route_uses_workflow_service_dependency(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FakeWorkflowService:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def validate_data(self, data, declared_format=None, schema_id=None):
            self.calls.append(
                {
                    "data": data,
                    "declared_format": declared_format,
                    "schema_id": schema_id,
                }
            )
            return {
                "status": "success",
                "detected_format": "csv",
                "profile": {"row_count": 0, "fields": [], "warnings": []},
                "validation_report": {
                    "valid": True,
                    "schema_id": schema_id,
                    "schema_confidence": None,
                    "severity_summary": {},
                    "issues": [],
                    "requires_review": False,
                },
            }

    fake_service = FakeWorkflowService()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def fake_workflow_service() -> FakeWorkflowService:
        return fake_service

    app.dependency_overrides[get_workflow_service] = fake_workflow_service
    transport = httpx.ASGITransport(app=app)
    source_data = " \na,b\n1,2\n "

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/validate",
            json={"data": source_data, "input_format": "csv", "schema_id": "lab_result_v1"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "success"
    assert fake_service.calls == [
        {
            "data": source_data,
            "declared_format": DataFormat.CSV,
            "schema_id": "lab_result_v1",
        }
    ]


@pytest.mark.asyncio
async def test_convert_route_uses_workflow_service_dependency(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FakeWorkflowService:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def convert_data(self, data, declared_format=None, target_format=DataFormat.JSON):
            self.calls.append(
                {
                    "data": data,
                    "declared_format": declared_format,
                    "target_format": target_format,
                }
            )
            return {
                "status": "success",
                "detected_format": "csv",
                "output_format": "json",
                "output": "[]",
                "metadata": {
                    "source_format": "csv",
                    "target_format": "json",
                    "source_row_count": 0,
                    "target_row_count": 0,
                    "output_hash": "sha256",
                    "lossy": False,
                    "actions_applied": [],
                },
            }

    fake_service = FakeWorkflowService()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def fake_workflow_service() -> FakeWorkflowService:
        return fake_service

    app.dependency_overrides[get_workflow_service] = fake_workflow_service
    transport = httpx.ASGITransport(app=app)
    source_data = " \na,b\n1,2\n "

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/convert",
            json={"data": source_data, "input_format": "csv", "target_format": "json"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["metadata"]["source_format"] == "csv"
    assert fake_service.calls == [
        {
            "data": source_data,
            "declared_format": DataFormat.CSV,
            "target_format": DataFormat.JSON,
        }
    ]


@pytest.mark.asyncio
async def test_fhir_and_ocr_routes_use_medical_evidence_service_dependency(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    clear_workflow_service_cache()

    class FakeMedicalEvidenceService:
        def __init__(self) -> None:
            self.fhir_calls: list[str] = []
            self.ocr_calls: list[list[dict]] = []

        def profile_fhir_like(self, data: str) -> dict:
            self.fhir_calls.append(data)
            return {
                "profile": {
                    "is_fhir_like": True,
                    "resource_type": "Observation",
                    "resource_counts": {"Observation": 1},
                    "issues": [],
                    "handoff_context": {},
                },
                "evidence": [],
            }

        def normalize_ocr_evidence(self, fields) -> dict:
            self.ocr_calls.append([field.model_dump(mode="json") for field in fields])
            return {
                "fields": [],
                "evidence": [],
                "requires_review": False,
            }

    fake_service = FakeMedicalEvidenceService()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency

    async def fake_medical_evidence_service() -> FakeMedicalEvidenceService:
        return fake_service

    app.dependency_overrides[get_medical_evidence_service] = fake_medical_evidence_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        fhir = await client.post(
            "/api/v1/fhir/profile",
            json={"data": '{"resourceType":"Observation","status":"final"}'},
        )
        ocr = await client.post(
            "/api/v1/ocr/evidence",
            json={
                "fields": [
                    {
                        "page": 1,
                        "name": "patient_id",
                        "value": "P001",
                        "bbox": [0, 0, 10, 10],
                        "confidence": 0.95,
                        "source_ref": "storage://doc/demo",
                    }
                ]
            },
        )

    assert fhir.status_code == 200
    assert fhir.json()["data"]["profile"]["resource_type"] == "Observation"
    assert fake_service.fhir_calls == ['{"resourceType":"Observation","status":"final"}']
    assert ocr.status_code == 200
    assert fake_service.ocr_calls == [
        [
            {
                "page": 1,
                "name": "patient_id",
                "value": "P001",
                "bbox": [0.0, 0.0, 10.0, 10.0],
                "confidence": 0.95,
                "source_ref": "storage://doc/demo",
                "normalized_to": None,
            }
        ]
    ]
