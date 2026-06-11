from datetime import datetime, timezone

import httpx
import pytest

from pathlib import Path

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import clear_settings_cache
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.data_tools.parse import parse_data
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import require_authentication
from ojtflow.interoperability.adapters import (
    build_document_reference,
    export_clinical_package_as_bulk_fhir_ndjson,
    map_dicom_to_imaging_study,
    map_hl7_v2_lab_observations,
    parse_bulk_fhir_ndjson,
    profile_dicom_metadata,
    validate_bulk_fhir_ndjson_lines,
)
from ojtflow.infrastructure.retrieval.static import (
    StaticKnowledgeRepository,
    StaticRetrievalRepository,
)
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryWorkflowRepository,
)


ROOT = Path(__file__).resolve().parents[1]


def make_service() -> WorkflowService:
    return WorkflowService(
        datasets=InMemoryDatasetStore(),
        workflows=InMemoryWorkflowRepository(),
        events=InMemoryEventRepository(),
        knowledge=StaticKnowledgeRepository(ROOT / "knowledge"),
        retrieval=StaticRetrievalRepository(ROOT / "knowledge"),
    )


def test_bulk_fhir_ndjson_import_and_parse_data_adapter() -> None:
    text = (
        '{"resourceType":"Patient","id":"P001"}\n'
        '{"resourceType":"Observation","id":"O001","status":"final"}\n'
        '{"resourceType":"UnsupportedThing","id":"X001"}\n'
        'not json\n'
    )

    report = parse_bulk_fhir_ndjson(
        text,
        source_ref="bulk-fhir://demo/export.ndjson",
        allowed_resource_types={"Patient", "Observation"},
    )
    parsed = parse_data(text, DataFormat.NDJSON, source_ref="bulk-fhir://demo/export.ndjson")
    streamed = validate_bulk_fhir_ndjson_lines(
        iter(text.splitlines()),
        source_ref="bulk-fhir://demo/export.ndjson",
        allowed_resource_types={"Patient", "Observation"},
    )

    assert report.resource_count == 3
    assert streamed.resource_count == report.resource_count
    assert report.resource_counts == {
        "Observation": 1,
        "Patient": 1,
        "UnsupportedThing": 1,
    }
    assert report.rejected_line_count == 1
    assert report.resources[2].warnings == [
        "resourceType UnsupportedThing is outside selected v0 scope"
    ]
    assert parsed.format == DataFormat.NDJSON
    assert parsed.records[0]["resourceType"] == "Patient"
    assert parsed.records[1]["_source_row"] == 2
    assert parsed.parser_warnings[0].startswith("line 4 is not valid JSON")


def test_approved_clinical_package_exports_bulk_fhir_ndjson() -> None:
    service = make_service()
    workflow = service.start_workflow(
        instruction="Prepare approved lab package.",
        data="date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n",
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=False,
    )

    assert workflow.clinical_package is not None
    exported = export_clinical_package_as_bulk_fhir_ndjson(workflow.clinical_package)

    assert exported.approved_for_export is True
    assert exported.resource_count == 1
    assert exported.files[0].filename == "Observation.ndjson"
    assert '"resourceType":"Observation"' in exported.files[0].ndjson
    assert exported.files[0].output_hash


def test_hl7_v2_oru_obx_maps_to_fhir_like_observation_with_provenance() -> None:
    message = (
        "MSH|^~\\&|LAB|HOSP|OJT|OJT|202606111200||ORU^R01|MSG1|P|2.5\r"
        "PID|1||P001^^^MRN||DOE^JANE\r"
        "OBR|1||ORD1|LAB^Lab panel\r"
        "OBX|1|NM|4548-4^HbA1c^LN||7.4|%^percent|4.0-5.6|H|||F|||20260611\r"
    )

    mapped = map_hl7_v2_lab_observations(message, source_ref="hl7v2://msg/1")

    assert mapped.message.patient_id == "P001"
    assert mapped.message.message_type == "ORU"
    assert mapped.observations[0].resource_type == "Observation"
    observation = mapped.observations[0].resource
    assert observation["subject"]["reference"] == "Patient/P001"
    assert observation["code"]["coding"][0]["system"] == "http://loinc.org"
    assert observation["code"]["text"] == "HbA1c"
    assert observation["valueQuantity"]["value"] == 7.4
    assert observation["effectiveDateTime"] == "2026-06-11"
    provenance_fields = {item.source_field for item in mapped.observations[0].field_provenance}
    assert {"PID-3", "OBX-3", "OBX-5", "OBX-6", "OBX-14"}.issubset(provenance_fields)


def test_dicom_metadata_profiles_and_maps_without_pixel_data() -> None:
    profile = profile_dicom_metadata(
        {
            "StudyInstanceUID": "1.2.3",
            "SeriesInstanceUID": "1.2.3.4",
            "SOPInstanceUID": "1.2.3.4.5",
            "Modality": "MR",
            "AccessionNumber": "ACC-001",
            "PatientIdentityRemoved": "YES",
            "PixelData": "<not loaded>",
        },
        source_ref="dicom://study/1.2.3",
    )
    mapped = map_dicom_to_imaging_study(profile)

    assert profile.deidentification_status == "deidentified"
    assert profile.modality == "MR"
    assert "PixelData" not in profile.metadata
    assert mapped.resource.resource_type == "ImagingStudy"
    assert mapped.resource.resource["series"][0]["uid"] == "1.2.3.4"
    assert any("Pixel data is intentionally not parsed" in warning for warning in mapped.warnings)


def test_document_reference_mapping_preserves_artifact_ref() -> None:
    mapped = build_document_reference(
        document_id="artifact_123",
        filename="lab-report.pdf",
        content_type="application/pdf",
        source_ref="storage://uploads/lab-report.pdf",
        description="Uploaded lab report",
    )

    assert mapped.resource.resource_type == "DocumentReference"
    attachment = mapped.resource.resource["content"][0]["attachment"]
    assert attachment["title"] == "lab-report.pdf"
    assert attachment["url"] == "storage://uploads/lab-report.pdf"


async def _authenticated_dependency() -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    user = UserRecord(
        user_id="usr_interop",
        google_sub="google-usr_interop",
        email="interop@example.com",
        email_verified=True,
        display_name="Interop User",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_interop",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


@pytest.mark.asyncio
async def test_interoperability_api_endpoints_return_envelopes(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    transport = httpx.ASGITransport(app=app)
    service = make_service()
    workflow = service.start_workflow(
        instruction="Prepare approved lab package.",
        data="date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n",
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=False,
    )
    assert workflow.clinical_package is not None

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        bulk = await client.post(
            "/api/v1/interoperability/fhir/bulk/import",
            json={
                "data": '{"resourceType":"Patient","id":"P001"}\n',
                "allowed_resource_types": ["Patient"],
            },
        )
        export = await client.post(
            "/api/v1/interoperability/fhir/bulk/export-package",
            json={"package": workflow.clinical_package.model_dump(mode="json")},
        )
        hl7 = await client.post(
            "/api/v1/interoperability/hl7v2/observations",
            json={
                "data": (
                    "MSH|^~\\&|LAB|HOSP|OJT|OJT|202606111200||ORU^R01|MSG1|P|2.5\r"
                    "PID|1||P001^^^MRN||DOE^JANE\r"
                    "OBX|1|NM|4548-4^HbA1c^LN||7.4|%^percent|||||F|||20260611\r"
                )
            },
        )
        dicom = await client.post(
            "/api/v1/interoperability/dicom/metadata",
            json={
                "metadata": {
                    "StudyInstanceUID": "1.2.3",
                    "SeriesInstanceUID": "1.2.3.4",
                    "SOPInstanceUID": "1.2.3.4.5",
                    "Modality": "CT",
                    "PatientIdentityRemoved": "YES",
                }
            },
        )
        document = await client.post(
            "/api/v1/interoperability/document-reference",
            json={
                "document_id": "artifact_123",
                "filename": "report.pdf",
                "content_type": "application/pdf",
                "source_ref": "storage://uploads/report.pdf",
            },
        )

    assert bulk.status_code == 200
    assert bulk.json()["data"]["resource_count"] == 1
    assert export.status_code == 200
    assert export.json()["data"]["files"][0]["filename"] == "Observation.ndjson"
    assert hl7.status_code == 200
    assert hl7.json()["data"]["observations"][0]["resource_type"] == "Observation"
    assert dicom.status_code == 200
    assert dicom.json()["data"]["profile"]["modality"] == "CT"
    assert document.status_code == 200
    assert document.json()["data"]["resource"]["resource_type"] == "DocumentReference"
    clear_settings_cache()
