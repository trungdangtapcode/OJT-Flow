from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import clear_settings_cache
from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import require_authentication
from ojtflow.interoperability.analytics import (
    build_etl_export_package,
    build_external_api_cache_metadata,
    build_omop_export_preview,
    evaluate_source_ingestion_candidate,
    launch_external_link,
    load_cohort_research_workflow,
    load_dqd_compatibility,
    load_external_api_cache_policy,
    load_external_link_launchers,
    load_external_source_connectors,
    load_omop_mapping_profile,
    load_omop_vocabulary_candidate_catalog,
    load_source_ingestion_approval_policy,
)
from ojtflow.infrastructure.retrieval.static import (
    StaticKnowledgeRepository,
    StaticRetrievalRepository,
)
from ojtflow.infrastructure.retrieval.catalogs import (
    load_corpus_adapter_catalog,
    load_source_trust_policy_catalog,
)
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryDatasetStore,
    InMemoryEventRepository,
    InMemoryWorkflowRepository,
)


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_ROOT = ROOT / "knowledge"


def make_service() -> WorkflowService:
    return WorkflowService(
        datasets=InMemoryDatasetStore(),
        workflows=InMemoryWorkflowRepository(),
        events=InMemoryEventRepository(),
        knowledge=StaticKnowledgeRepository(KNOWLEDGE_ROOT),
        retrieval=StaticRetrievalRepository(KNOWLEDGE_ROOT),
    )


def make_lab_clinical_package():
    service = make_service()
    workflow = service.start_workflow(
        instruction="Prepare lab package for OMOP analytics preview.",
        data="date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n",
        declared_format=DataFormat.CSV,
        target_format=DataFormat.JSON,
        schema_id="lab_result_v1",
        require_human_review=False,
    )
    assert workflow.clinical_package is not None
    return workflow.clinical_package


def test_month7_catalogs_are_data_driven_and_cover_requested_scope() -> None:
    profile = load_omop_mapping_profile(KNOWLEDGE_ROOT)
    vocabulary = load_omop_vocabulary_candidate_catalog(KNOWLEDGE_ROOT)
    dqd = load_dqd_compatibility(KNOWLEDGE_ROOT)
    cohort = load_cohort_research_workflow(KNOWLEDGE_ROOT)
    connectors = load_external_source_connectors(KNOWLEDGE_ROOT)
    cache_policy = load_external_api_cache_policy(KNOWLEDGE_ROOT)
    ingestion_policy = load_source_ingestion_approval_policy(KNOWLEDGE_ROOT)
    launchers = load_external_link_launchers(KNOWLEDGE_ROOT)

    assert set(profile.supported_tables) == {
        "person",
        "observation",
        "measurement",
        "condition_occurrence",
        "drug_exposure",
        "visit_occurrence",
        "note",
    }
    assert {rule.target_vocabulary_id for rule in vocabulary.rules} >= {
        "LOINC",
        "UCUM",
        "RxNorm",
    }
    assert "OHDSI" in dqd.target_tool
    assert "clinical decision support" in " ".join(cohort.prohibited_uses).lower()
    assert {
        "pubmed",
        "clinicaltrials_gov",
        "openfda",
        "loinc",
        "ucum",
        "rxnav",
        "hl7_fhir_docs",
    }.issubset({connector.connector_id for connector in connectors.connectors})
    assert "source_release_version" in cache_policy.required_metadata_fields
    assert ingestion_policy.searchable_states == ["approved_searchable"]
    assert {launcher.launcher_id for launcher in launchers.launchers} >= {
        "pubmed",
        "clinicaltrials_gov",
        "openfda",
        "loinc",
        "ucum",
        "rxnav",
        "hl7_fhir_docs",
    }


def test_external_connectors_have_retrieval_governance_coverage() -> None:
    connectors = load_external_source_connectors(KNOWLEDGE_ROOT)
    adapters = load_corpus_adapter_catalog(KNOWLEDGE_ROOT)
    policies = load_source_trust_policy_catalog(KNOWLEDGE_ROOT)

    expected_source_by_connector = {
        "pubmed": "ncbi_pubmed_eutilities",
        "clinicaltrials_gov": "clinicaltrials_gov",
        "openfda": "openfda",
        "loinc": "loinc_core",
        "ucum": "ucum",
        "rxnav": "nlm_rxnorm",
        "hl7_fhir_docs": "hl7_fhir_r4",
    }
    connector_ids = {connector.connector_id for connector in connectors.connectors}
    adapter_source_ids = {adapter.source_id for adapter in adapters.adapters}
    policy_source_ids = {policy.source_id for policy in policies.policies}

    assert set(expected_source_by_connector).issubset(connector_ids)
    for connector_id, source_id in expected_source_by_connector.items():
        assert source_id in adapter_source_ids, connector_id
        assert source_id in policy_source_ids, connector_id


def test_omop_preview_reports_measurement_rows_and_unresolved_concepts() -> None:
    package = make_lab_clinical_package()
    preview = build_omop_export_preview(
        package,
        profile=load_omop_mapping_profile(KNOWLEDGE_ROOT),
        vocabulary_catalog=load_omop_vocabulary_candidate_catalog(KNOWLEDGE_ROOT),
    )

    measurement = next(
        table for table in preview.table_previews if table.table_name == "measurement"
    )
    assert measurement.row_count == 1
    assert measurement.concept_candidate_count >= 1
    assert measurement.standard_concept_count == 0
    assert "measurement.measurement_concept_id" in preview.unmapped_fields
    assert preview.review_required is True
    assert any(
        candidate.target_vocabulary_id == "LOINC"
        for candidate in preview.vocabulary_candidates
    )
    assert any("DQD" in warning for warning in preview.data_quality_warnings)


def test_external_cache_metadata_and_ingestion_approval_are_governed() -> None:
    cache_policy = load_external_api_cache_policy(KNOWLEDGE_ROOT)
    connectors = load_external_source_connectors(KNOWLEDGE_ROOT)
    ingestion_policy = load_source_ingestion_approval_policy(KNOWLEDGE_ROOT)

    metadata = build_external_api_cache_metadata(
        policy=cache_policy,
        connector_id="pubmed",
        endpoint_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        query="HbA1c LOINC Observation",
        source_release_version="fetched:2026-06-11",
        response_text='{"count":"2"}',
        fetched_at="2026-06-11T00:00:00+00:00",
    )
    pending = evaluate_source_ingestion_candidate(
        policy=ingestion_policy,
        connector_ids={connector.connector_id for connector in connectors.connectors},
        connector_id="pubmed",
        document_id="pubmed-123",
        source_url="https://pubmed.ncbi.nlm.nih.gov/123/",
        source_release_version="fetched:2026-06-11",
        license_accepted=True,
        reviewer_approved=False,
    )
    approved = evaluate_source_ingestion_candidate(
        policy=ingestion_policy,
        connector_ids={connector.connector_id for connector in connectors.connectors},
        connector_id="pubmed",
        document_id="pubmed-123",
        source_url="https://pubmed.ncbi.nlm.nih.gov/123/",
        source_release_version="fetched:2026-06-11",
        license_accepted=True,
        reviewer_approved=True,
    )

    assert metadata.cache_key.startswith("extcache_")
    assert metadata.query_hash
    assert metadata.metadata["raw_query_not_returned"] is True
    assert metadata.searchable_after_approval is False
    assert pending.state == "candidate"
    assert pending.searchable is False
    assert "data_steward_approval" in pending.required_actions
    assert approved.state == "approved_searchable"
    assert approved.searchable is True


def test_external_link_launchers_are_transparent_and_do_not_fetch() -> None:
    catalog = load_external_link_launchers(KNOWLEDGE_ROOT)
    launch = launch_external_link(
        catalog=catalog,
        launcher_id="pubmed",
        query="HbA1c unit standard",
    )

    assert launch.url == "https://pubmed.ncbi.nlm.nih.gov/?term=HbA1c+unit+standard"
    assert launch.external_network_call_performed is False
    assert launch.query_transparency["backend_fetch"] is False
    assert "HbA1c+unit+standard" == launch.query_transparency["encoded_query"]
    assert any("PHI" in warning for warning in launch.warnings)


def test_etl_export_package_preserves_resource_hashes_and_provenance_refs() -> None:
    package = make_lab_clinical_package()
    preview = build_omop_export_preview(
        package,
        profile=load_omop_mapping_profile(KNOWLEDGE_ROOT),
        vocabulary_catalog=load_omop_vocabulary_candidate_catalog(KNOWLEDGE_ROOT),
    )
    export = build_etl_export_package(
        package,
        preview=preview,
        include_resources=False,
    )

    assert export.package_id == package.package_id
    assert export.workflow_id == package.workflow_id
    assert export.clinical_package_hash
    assert export.resource_manifest[0].resource_type == "Observation"
    assert export.resource_manifest[0].resource_hash
    assert export.resource_manifest[0].provenance_ref_count > 0
    assert export.included_resources == []
    assert export.package is None


async def _authenticated_dependency() -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    user = UserRecord(
        user_id="usr_analytics",
        google_sub="google-usr_analytics",
        email="analytics@example.com",
        email_verified=True,
        display_name="Analytics User",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_analytics",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


@pytest.mark.asyncio
async def test_analytics_external_api_endpoints_return_envelopes(monkeypatch) -> None:
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    clear_settings_cache()
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    transport = httpx.ASGITransport(app=app)
    package = make_lab_clinical_package()

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        mapping = await client.get("/api/v1/interoperability/analytics/omop/mapping-profile")
        preview = await client.post(
            "/api/v1/interoperability/analytics/omop/preview",
            json={"package": package.model_dump(mode="json")},
        )
        dqd = await client.get("/api/v1/interoperability/analytics/omop/dqd-compatibility")
        cohort = await client.get(
            "/api/v1/interoperability/analytics/cohort-research-workflow"
        )
        connectors = await client.get("/api/v1/interoperability/external/connectors")
        cache_policy = await client.get("/api/v1/interoperability/external/cache-policy")
        cache_metadata = await client.post(
            "/api/v1/interoperability/external/cache/metadata",
            json={
                "connector_id": "pubmed",
                "endpoint_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                "query": "HbA1c LOINC Observation",
                "source_release_version": "fetched:2026-06-11",
            },
        )
        ingestion_policy = await client.get(
            "/api/v1/interoperability/external/ingestion-approval-policy"
        )
        ingestion_preview = await client.post(
            "/api/v1/interoperability/external/ingestion/approval-preview",
            json={
                "connector_id": "pubmed",
                "document_id": "pubmed-123",
                "source_url": "https://pubmed.ncbi.nlm.nih.gov/123/",
                "source_release_version": "fetched:2026-06-11",
                "license_accepted": True,
                "reviewer_approved": True,
            },
        )
        launchers = await client.get("/api/v1/interoperability/external/link-launchers")
        launch = await client.post(
            "/api/v1/interoperability/external/link-launch",
            json={"launcher_id": "pubmed", "query": "HbA1c unit standard"},
        )
        etl = await client.post(
            "/api/v1/interoperability/export/etl-package",
            json={"package": package.model_dump(mode="json"), "include_resources": False},
        )

    responses = [
        mapping,
        preview,
        dqd,
        cohort,
        connectors,
        cache_policy,
        cache_metadata,
        ingestion_policy,
        ingestion_preview,
        launchers,
        launch,
        etl,
    ]
    assert all(response.status_code == 200 for response in responses)
    assert mapping.json()["data"]["profile_id"] == "ojtflow_omop_preview_v0"
    assert preview.json()["data"]["total_rows"] == 1
    assert "Data Quality Dashboard" in dqd.json()["data"]["target_tool"]
    assert "clinical decision support" in " ".join(cohort.json()["data"]["prohibited_uses"]).lower()
    assert len(connectors.json()["data"]["connectors"]) >= 7
    assert cache_policy.json()["data"]["policy_id"] == "external_api_cache_policy_v0"
    assert cache_metadata.json()["data"]["cache_key"].startswith("extcache_")
    assert ingestion_policy.json()["data"]["policy_id"] == "source_ingestion_approval_policy_v0"
    assert ingestion_preview.json()["data"]["searchable"] is True
    assert len(launchers.json()["data"]["launchers"]) >= 7
    assert launch.json()["data"]["external_network_call_performed"] is False
    assert etl.json()["data"]["resource_manifest"][0]["resource_type"] == "Observation"
