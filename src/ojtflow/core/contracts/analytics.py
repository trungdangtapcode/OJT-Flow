"""Analytics, OMOP, and external-source workflow contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.clinical import ClinicalPackage
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


OmopTargetTable = Literal[
    "person",
    "observation",
    "measurement",
    "condition_occurrence",
    "drug_exposure",
    "visit_occurrence",
    "note",
]

OmopRowCondition = Literal[
    "resource_type_match",
    "has_numeric_value_quantity",
    "observation_without_numeric_value_quantity",
    "has_document_content",
]

ExternalSourceType = Literal[
    "literature",
    "clinical_trials",
    "regulatory",
    "terminology",
    "interoperability_standard",
]

ExternalAuthRequirement = Literal[
    "none",
    "optional_api_key",
    "account_or_license_required",
    "configured_secret_required",
]

SourceIngestionState = Literal[
    "candidate",
    "blocked",
    "approved_searchable",
    "rejected",
]


class OmopFieldMapping(ContractModel):
    target_table: OmopTargetTable
    target_field: NonBlankStr
    source_resource_type: NonBlankStr
    source_path: NonBlankStr
    transformation: NonBlankStr
    required: bool = False
    review_required: bool = True
    notes: list[NonBlankStr] = Field(default_factory=list)


class OmopRowRule(ContractModel):
    target_table: OmopTargetTable
    source_resource_types: list[NonBlankStr] = Field(min_length=1)
    condition: OmopRowCondition
    notes: list[NonBlankStr] = Field(default_factory=list)


class OmopMappingProfile(ContractModel):
    profile_id: NonBlankStr
    version: NonBlankStr
    target_cdm: NonBlankStr
    supported_tables: list[OmopTargetTable] = Field(min_length=1)
    row_rules: list[OmopRowRule] = Field(default_factory=list)
    field_mappings: list[OmopFieldMapping] = Field(default_factory=list)
    review_policy: NonBlankStr
    standard_refs: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class OmopVocabularyCandidateRule(ContractModel):
    rule_id: NonBlankStr
    source_system: NonBlankStr
    source_resource_types: list[NonBlankStr] = Field(min_length=1)
    target_vocabulary_id: NonBlankStr
    target_table: OmopTargetTable
    source_path: NonBlankStr
    concept_id_required: bool = True
    requires_review: bool = True
    notes: list[NonBlankStr] = Field(default_factory=list)


class OmopKnownConceptCandidate(ContractModel):
    source_system: NonBlankStr
    source_code: NonBlankStr
    source_display: NonBlankStr | None = None
    target_vocabulary_id: NonBlankStr
    standard_concept_id: int | None = None
    standard_concept_name: NonBlankStr | None = None
    standard_concept_code: NonBlankStr | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_review: bool = True
    source_ref: NonBlankStr | None = None


class OmopVocabularyCandidateCatalog(ContractModel):
    catalog_id: NonBlankStr
    version: NonBlankStr
    rules: list[OmopVocabularyCandidateRule] = Field(default_factory=list)
    known_candidates: list[OmopKnownConceptCandidate] = Field(default_factory=list)
    standard_refs: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class OmopVocabularyCandidate(ContractModel):
    candidate_id: NonBlankStr = Field(default_factory=lambda: new_id("omopterm"))
    package_id: NonBlankStr
    resource_id: NonBlankStr
    resource_type: NonBlankStr
    source_system: NonBlankStr
    source_code: NonBlankStr
    source_display: NonBlankStr | None = None
    target_vocabulary_id: NonBlankStr
    target_table: OmopTargetTable
    standard_concept_id: int | None = None
    standard_concept_name: NonBlankStr | None = None
    standard_concept_code: NonBlankStr | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    requires_review: bool = True
    evidence_ref: NonBlankStr | None = None
    warnings: list[NonBlankStr] = Field(default_factory=list)


class OmopExportPreviewTable(ContractModel):
    table_name: OmopTargetTable
    row_count: int = Field(ge=0)
    mapped_field_count: int = Field(ge=0)
    required_unmapped_fields: list[NonBlankStr] = Field(default_factory=list)
    concept_candidate_count: int = Field(ge=0)
    standard_concept_count: int = Field(ge=0)
    concept_coverage_ratio: float = Field(ge=0.0, le=1.0)
    data_quality_warnings: list[NonBlankStr] = Field(default_factory=list)


class OmopExportPreview(ContractModel):
    preview_id: NonBlankStr = Field(default_factory=lambda: new_id("omopprev"))
    package_id: NonBlankStr
    workflow_id: NonBlankStr
    profile_id: NonBlankStr
    target_cdm: NonBlankStr
    table_previews: list[OmopExportPreviewTable] = Field(default_factory=list)
    total_rows: int = Field(ge=0)
    vocabulary_candidates: list[OmopVocabularyCandidate] = Field(default_factory=list)
    concept_candidate_count: int = Field(ge=0)
    standard_concept_count: int = Field(ge=0)
    concept_coverage_ratio: float = Field(ge=0.0, le=1.0)
    unmapped_fields: list[NonBlankStr] = Field(default_factory=list)
    data_quality_warnings: list[NonBlankStr] = Field(default_factory=list)
    review_required: bool = True
    notes: list[NonBlankStr] = Field(default_factory=list)


class DataQualityDashboardCompatibility(ContractModel):
    compatibility_id: NonBlankStr
    version: NonBlankStr
    target_tool: NonBlankStr
    compatible_outputs: list[NonBlankStr] = Field(default_factory=list)
    required_inputs: list[NonBlankStr] = Field(default_factory=list)
    supported_check_families: list[NonBlankStr] = Field(default_factory=list)
    unsupported_check_families: list[NonBlankStr] = Field(default_factory=list)
    future_integration_path: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)
    standard_refs: list[NonBlankStr] = Field(default_factory=list)


class CohortResearchWorkflowConcept(ContractModel):
    concept_id: NonBlankStr
    version: NonBlankStr
    intended_use: NonBlankStr
    prohibited_uses: list[NonBlankStr] = Field(default_factory=list)
    workflow_steps: list[NonBlankStr] = Field(default_factory=list)
    required_approvals: list[NonBlankStr] = Field(default_factory=list)
    output_artifacts: list[NonBlankStr] = Field(default_factory=list)
    separation_controls: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class ExternalSourceConnector(ContractModel):
    connector_id: NonBlankStr
    display_name: NonBlankStr
    source_type: ExternalSourceType
    source_url: NonBlankStr
    docs_url: NonBlankStr
    auth_requirement: ExternalAuthRequirement
    rate_limit_policy: NonBlankStr
    license_notes: NonBlankStr
    update_cadence: NonBlankStr
    data_classes: list[NonBlankStr] = Field(default_factory=list)
    allowed_use: list[NonBlankStr] = Field(default_factory=list)
    prohibited_use: list[NonBlankStr] = Field(default_factory=list)
    cache_policy_ref: NonBlankStr
    ingestion_approval_required: bool = True
    query_transparency_required: bool = True


class ExternalSourceConnectorRegistry(ContractModel):
    registry_id: NonBlankStr
    version: NonBlankStr
    connectors: list[ExternalSourceConnector] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class ExternalApiCachePolicy(ContractModel):
    policy_id: NonBlankStr
    version: NonBlankStr
    cache_key_fields: list[NonBlankStr] = Field(default_factory=list)
    required_metadata_fields: list[NonBlankStr] = Field(default_factory=list)
    default_ttl_seconds: int = Field(gt=0)
    stale_while_revalidate_seconds: int = Field(ge=0)
    invalidation_triggers: list[NonBlankStr] = Field(default_factory=list)
    privacy_controls: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class ExternalApiCacheEntryMetadata(ContractModel):
    cache_key: NonBlankStr
    source_id: NonBlankStr
    endpoint_url_hash: NonBlankStr
    query_hash: NonBlankStr
    source_release_version: NonBlankStr
    fetched_at: NonBlankStr
    expires_at: NonBlankStr
    invalidation_policy_id: NonBlankStr
    response_hash: NonBlankStr | None = None
    searchable_after_approval: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceIngestionApprovalPolicy(ContractModel):
    policy_id: NonBlankStr
    version: NonBlankStr
    candidate_states: list[SourceIngestionState] = Field(default_factory=list)
    searchable_states: list[SourceIngestionState] = Field(default_factory=list)
    approval_steps: list[NonBlankStr] = Field(default_factory=list)
    rejection_handling: list[NonBlankStr] = Field(default_factory=list)
    audit_requirements: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class SourceIngestionApprovalDecision(ContractModel):
    document_id: NonBlankStr
    connector_id: NonBlankStr
    state: SourceIngestionState
    searchable: bool
    required_actions: list[NonBlankStr] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class ExternalLinkLauncher(ContractModel):
    launcher_id: NonBlankStr
    display_name: NonBlankStr
    connector_id: NonBlankStr
    source_url: NonBlankStr
    url_template: NonBlankStr
    query_parameter: NonBlankStr
    supported_query_examples: list[NonBlankStr] = Field(default_factory=list)
    transparency_notes: list[NonBlankStr] = Field(default_factory=list)
    pii_phi_policy: NonBlankStr


class ExternalLinkLauncherCatalog(ContractModel):
    catalog_id: NonBlankStr
    version: NonBlankStr
    launchers: list[ExternalLinkLauncher] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class ExternalLinkLaunch(ContractModel):
    launcher_id: NonBlankStr
    query: NonBlankStr
    url: NonBlankStr
    external_network_call_performed: bool = False
    query_transparency: dict[str, Any] = Field(default_factory=dict)
    warnings: list[NonBlankStr] = Field(default_factory=list)


class EtlExportResourceManifestItem(ContractModel):
    resource_id: NonBlankStr
    resource_type: NonBlankStr
    resource_hash: NonBlankStr
    source_refs: list[NonBlankStr] = Field(default_factory=list)
    provenance_ref_count: int = Field(ge=0)
    review_required: bool = False
    warnings: list[NonBlankStr] = Field(default_factory=list)


class EtlExportPackage(ContractModel):
    export_id: NonBlankStr = Field(default_factory=lambda: new_id("etl"))
    manifest_version: NonBlankStr = "etl_export_package.v0"
    package_id: NonBlankStr
    workflow_id: NonBlankStr
    generated_at: NonBlankStr = Field(default_factory=lambda: utc_now().isoformat())
    clinical_package_hash: NonBlankStr
    omop_preview: OmopExportPreview
    resource_manifest: list[EtlExportResourceManifestItem] = Field(default_factory=list)
    provenance_record_count: int = Field(ge=0)
    audit_event_refs: list[NonBlankStr] = Field(default_factory=list)
    output_refs: list[NonBlankStr] = Field(default_factory=list)
    included_resources: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[NonBlankStr] = Field(default_factory=list)
    package: ClinicalPackage | None = None
