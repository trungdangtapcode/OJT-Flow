"""OMOP analytics and external-source governance helpers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypeVar
from urllib.parse import quote_plus

from ojtflow.core.contracts.analytics import (
    CohortResearchWorkflowConcept,
    DataQualityDashboardCompatibility,
    EtlExportPackage,
    EtlExportResourceManifestItem,
    ExternalApiCacheEntryMetadata,
    ExternalApiCachePolicy,
    ExternalLinkLaunch,
    ExternalLinkLauncherCatalog,
    ExternalSourceConnectorRegistry,
    OmopExportPreview,
    OmopExportPreviewTable,
    OmopKnownConceptCandidate,
    OmopMappingProfile,
    OmopTargetTable,
    OmopVocabularyCandidate,
    OmopVocabularyCandidateCatalog,
    SourceIngestionApprovalDecision,
    SourceIngestionApprovalPolicy,
)
from ojtflow.core.contracts.clinical import ClinicalPackage, ClinicalResourceRecord
from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.errors import ToolExecutionError
from ojtflow.data_tools.hashing import sha256_text


ANALYTICS_DIR = Path("analytics")
SOURCE_CATALOG_DIR = Path("source_catalog")
OMOP_MAPPING_PROFILE_PATH = ANALYTICS_DIR / "omop_mapping_profile.json"
OMOP_VOCABULARY_CANDIDATES_PATH = ANALYTICS_DIR / "omop_vocabulary_candidates.json"
DQD_COMPATIBILITY_PATH = ANALYTICS_DIR / "data_quality_dashboard_compatibility.json"
COHORT_RESEARCH_WORKFLOW_PATH = ANALYTICS_DIR / "cohort_research_workflow.json"
EXTERNAL_CONNECTOR_REGISTRY_PATH = SOURCE_CATALOG_DIR / "external_connector_registry.json"
EXTERNAL_API_CACHE_POLICY_PATH = SOURCE_CATALOG_DIR / "external_api_cache_policy.json"
SOURCE_INGESTION_APPROVAL_POLICY_PATH = (
    SOURCE_CATALOG_DIR / "source_ingestion_approval_policy.json"
)
EXTERNAL_LINK_LAUNCHERS_PATH = SOURCE_CATALOG_DIR / "external_link_launchers.json"

ModelT = TypeVar("ModelT", bound=ContractModel)


def load_omop_mapping_profile(knowledge_root: Path) -> OmopMappingProfile:
    profile = _load_contract(knowledge_root / OMOP_MAPPING_PROFILE_PATH, OmopMappingProfile)
    missing_tables = set(profile.supported_tables) - {
        rule.target_table for rule in profile.row_rules
    }
    if missing_tables:
        raise ValueError(
            "OMOP mapping profile has supported tables without row rules: "
            + ", ".join(sorted(missing_tables))
        )
    return profile


def load_omop_vocabulary_candidate_catalog(
    knowledge_root: Path,
) -> OmopVocabularyCandidateCatalog:
    catalog = _load_contract(
        knowledge_root / OMOP_VOCABULARY_CANDIDATES_PATH,
        OmopVocabularyCandidateCatalog,
    )
    _ensure_unique(
        [rule.rule_id for rule in catalog.rules],
        label="OMOP vocabulary candidate rule",
        path=knowledge_root / OMOP_VOCABULARY_CANDIDATES_PATH,
    )
    return catalog


def load_dqd_compatibility(knowledge_root: Path) -> DataQualityDashboardCompatibility:
    return _load_contract(
        knowledge_root / DQD_COMPATIBILITY_PATH,
        DataQualityDashboardCompatibility,
    )


def load_cohort_research_workflow(
    knowledge_root: Path,
) -> CohortResearchWorkflowConcept:
    return _load_contract(
        knowledge_root / COHORT_RESEARCH_WORKFLOW_PATH,
        CohortResearchWorkflowConcept,
    )


def load_external_source_connectors(
    knowledge_root: Path,
) -> ExternalSourceConnectorRegistry:
    registry = _load_contract(
        knowledge_root / EXTERNAL_CONNECTOR_REGISTRY_PATH,
        ExternalSourceConnectorRegistry,
    )
    _ensure_unique(
        [connector.connector_id for connector in registry.connectors],
        label="external connector",
        path=knowledge_root / EXTERNAL_CONNECTOR_REGISTRY_PATH,
    )
    return registry


def load_external_api_cache_policy(knowledge_root: Path) -> ExternalApiCachePolicy:
    return _load_contract(
        knowledge_root / EXTERNAL_API_CACHE_POLICY_PATH,
        ExternalApiCachePolicy,
    )


def load_source_ingestion_approval_policy(
    knowledge_root: Path,
) -> SourceIngestionApprovalPolicy:
    return _load_contract(
        knowledge_root / SOURCE_INGESTION_APPROVAL_POLICY_PATH,
        SourceIngestionApprovalPolicy,
    )


def load_external_link_launchers(knowledge_root: Path) -> ExternalLinkLauncherCatalog:
    catalog = _load_contract(
        knowledge_root / EXTERNAL_LINK_LAUNCHERS_PATH,
        ExternalLinkLauncherCatalog,
    )
    _ensure_unique(
        [launcher.launcher_id for launcher in catalog.launchers],
        label="external link launcher",
        path=knowledge_root / EXTERNAL_LINK_LAUNCHERS_PATH,
    )
    return catalog


def build_omop_export_preview(
    package: ClinicalPackage,
    *,
    profile: OmopMappingProfile,
    vocabulary_catalog: OmopVocabularyCandidateCatalog,
) -> OmopExportPreview:
    assignments = _resource_assignments(package, profile)
    candidates = build_omop_vocabulary_candidates(
        package,
        vocabulary_catalog=vocabulary_catalog,
    )
    candidate_lookup = _candidate_lookup_by_resource_table(candidates)
    table_previews: list[OmopExportPreviewTable] = []
    all_unmapped: list[str] = []
    all_warnings: list[str] = []

    for table in profile.supported_tables:
        records = assignments.get(table, [])
        table_candidates = [
            candidate
            for candidate in candidates
            if candidate.target_table == table
        ]
        mapped_count = 0
        unmapped: set[str] = set()
        warnings: list[str] = []

        for record in records:
            mappings = [
                mapping
                for mapping in profile.field_mappings
                if mapping.target_table == table
                and mapping.source_resource_type == record.resource_type
            ]
            for mapping in mappings:
                if mapping.target_field.endswith("_concept_id"):
                    has_standard_concept = any(
                        candidate.standard_concept_id is not None
                        for candidate in candidate_lookup.get(
                            (record.resource_id, table),
                            [],
                        )
                    )
                    if has_standard_concept:
                        mapped_count += 1
                    elif mapping.required:
                        unmapped.add(mapping.target_field)
                    continue
                if _path_has_value(record, mapping.source_path):
                    mapped_count += 1
                elif mapping.required:
                    unmapped.add(mapping.target_field)

            if record.review_required:
                warnings.append(f"{record.resource_id} requires review before OMOP export")
            warnings.extend(record.warnings)

        concept_count = len(table_candidates)
        standard_concept_count = sum(
            1 for candidate in table_candidates if candidate.standard_concept_id is not None
        )
        concept_coverage = _ratio(standard_concept_count, concept_count)
        if records and concept_count == 0 and table in {
            "measurement",
            "observation",
            "condition_occurrence",
            "drug_exposure",
        }:
            warnings.append(f"{table} has rows without vocabulary candidates")
        if unmapped:
            warnings.append(
                f"{table} has required unmapped fields: {', '.join(sorted(unmapped))}"
            )
        table_previews.append(
            OmopExportPreviewTable(
                table_name=table,
                row_count=len(records),
                mapped_field_count=mapped_count,
                required_unmapped_fields=sorted(unmapped),
                concept_candidate_count=concept_count,
                standard_concept_count=standard_concept_count,
                concept_coverage_ratio=concept_coverage,
                data_quality_warnings=_dedupe(warnings),
            )
        )
        all_unmapped.extend(f"{table}.{field}" for field in sorted(unmapped))
        all_warnings.extend(warnings)

    total_rows = sum(table.row_count for table in table_previews)
    concept_count = len(candidates)
    standard_concept_count = sum(
        1 for candidate in candidates if candidate.standard_concept_id is not None
    )
    base_warnings = [
        *profile.warnings,
        "OMOP preview is not a production ETL load.",
        "Run reviewed vocabulary resolution and OHDSI DQD before analytics use.",
    ]
    return OmopExportPreview(
        package_id=package.package_id,
        workflow_id=package.workflow_id,
        profile_id=profile.profile_id,
        target_cdm=profile.target_cdm,
        table_previews=table_previews,
        total_rows=total_rows,
        vocabulary_candidates=candidates,
        concept_candidate_count=concept_count,
        standard_concept_count=standard_concept_count,
        concept_coverage_ratio=_ratio(standard_concept_count, concept_count),
        unmapped_fields=_dedupe(all_unmapped),
        data_quality_warnings=_dedupe([*base_warnings, *all_warnings]),
        review_required=(
            bool(all_unmapped)
            or any(candidate.requires_review for candidate in candidates)
            or any(record.review_required for record in package.clinical_bundle.resources)
        ),
        notes=[
            profile.review_policy,
            "ClinicalPackage provenance is preserved for downstream ETL teams.",
        ],
    )


def build_omop_vocabulary_candidates(
    package: ClinicalPackage,
    *,
    vocabulary_catalog: OmopVocabularyCandidateCatalog,
) -> list[OmopVocabularyCandidate]:
    candidates: list[OmopVocabularyCandidate] = []
    for record in package.clinical_bundle.resources:
        for rule in vocabulary_catalog.rules:
            if record.resource_type not in rule.source_resource_types:
                continue
            values = _path_values(record, rule.source_path)
            for value in values:
                candidates.extend(
                    _candidate_from_rule_value(
                        package=package,
                        record=record,
                        value=value,
                        rule_system=rule.source_system,
                        target_vocabulary_id=rule.target_vocabulary_id,
                        target_table=rule.target_table,
                        known_candidates=vocabulary_catalog.known_candidates,
                        requires_review=rule.requires_review,
                    )
                )

    for terminology_candidate in package.terminology_candidates:
        source_system = _standard_system_to_uri(terminology_candidate.standard_system)
        known = _find_known_candidate(
            vocabulary_catalog.known_candidates,
            source_system=source_system,
            source_code=terminology_candidate.code,
        )
        matched_record = _record_for_terminology_candidate(
            package.clinical_bundle.resources,
            terminology_candidate.source_value,
            terminology_candidate.location.row if terminology_candidate.location else None,
        )
        candidates.append(
            _omop_candidate(
                package=package,
                record=matched_record,
                source_system=source_system,
                source_code=terminology_candidate.code,
                source_display=terminology_candidate.display,
                target_vocabulary_id=terminology_candidate.standard_system,
                target_table="measurement",
                known=known,
                confidence=min(terminology_candidate.confidence, 0.85),
                requires_review=True,
                evidence_ref=terminology_candidate.source_uri,
                warnings=[
                    "Terminology candidate requires review before OMOP concept assignment."
                ],
            )
        )

    for unit_validation in package.unit_validations:
        if not unit_validation.normalized_unit:
            continue
        matched_record = _record_for_source_row(
            package.clinical_bundle.resources,
            unit_validation.location.row if unit_validation.location else None,
        )
        known = _find_known_candidate(
            vocabulary_catalog.known_candidates,
            source_system="http://unitsofmeasure.org",
            source_code=unit_validation.normalized_unit,
        )
        candidates.append(
            _omop_candidate(
                package=package,
                record=matched_record,
                source_system="http://unitsofmeasure.org",
                source_code=unit_validation.normalized_unit,
                source_display=unit_validation.normalized_unit,
                target_vocabulary_id="UCUM",
                target_table="measurement",
                known=known,
                confidence=min(unit_validation.confidence, 0.75),
                requires_review=unit_validation.requires_review or known is None,
                evidence_ref=None,
                warnings=["Unit concept candidate requires release-specific review."],
            )
        )

    return _dedupe_candidates(candidates)


def build_external_api_cache_metadata(
    *,
    policy: ExternalApiCachePolicy,
    connector_id: str,
    endpoint_url: str,
    query: str,
    source_release_version: str,
    response_text: str | None = None,
    fetched_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ExternalApiCacheEntryMetadata:
    fetched_dt = _parse_datetime(fetched_at) if fetched_at else datetime.now(timezone.utc)
    expires_dt = fetched_dt + timedelta(seconds=policy.default_ttl_seconds)
    normalized_query = _normalize_query(query)
    cache_fingerprint = json.dumps(
        {
            "connector_id": connector_id,
            "endpoint_url_hash": sha256_text(endpoint_url),
            "query_hash": sha256_text(normalized_query),
            "source_release_version": source_release_version,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return ExternalApiCacheEntryMetadata(
        cache_key=f"extcache_{sha256_text(cache_fingerprint)[:24]}",
        source_id=connector_id,
        endpoint_url_hash=sha256_text(endpoint_url),
        query_hash=sha256_text(normalized_query),
        source_release_version=source_release_version,
        fetched_at=fetched_dt.isoformat(),
        expires_at=expires_dt.isoformat(),
        invalidation_policy_id=policy.policy_id,
        response_hash=sha256_text(response_text) if response_text is not None else None,
        searchable_after_approval=False,
        metadata={
            "cache_key_fields": list(policy.cache_key_fields),
            "required_metadata_fields": list(policy.required_metadata_fields),
            "raw_query_not_returned": True,
            **(metadata or {}),
        },
    )


def evaluate_source_ingestion_candidate(
    *,
    policy: SourceIngestionApprovalPolicy,
    connector_ids: set[str],
    connector_id: str,
    document_id: str,
    source_url: str,
    source_release_version: str,
    license_accepted: bool,
    reviewer_approved: bool,
    contains_phi: bool = False,
) -> SourceIngestionApprovalDecision:
    required_actions: list[str] = []
    warnings: list[str] = []
    if connector_id not in connector_ids:
        required_actions.append("register_connector")
        warnings.append("Connector is not registered.")
    if not source_url.strip():
        required_actions.append("provide_source_url")
    if not source_release_version.strip():
        required_actions.append("provide_source_release_version")
    if not license_accepted:
        required_actions.append("accept_source_license")
    if contains_phi:
        required_actions.append("remove_or_approve_phi")
        warnings.append("Candidate source or query contains PHI/sensitive context.")
    if not reviewer_approved:
        required_actions.append("data_steward_approval")

    state: str = "candidate"
    if "register_connector" in required_actions or "remove_or_approve_phi" in required_actions:
        state = "blocked"
    elif not required_actions:
        state = "approved_searchable"
    searchable = state in set(policy.searchable_states)
    return SourceIngestionApprovalDecision(
        document_id=document_id,
        connector_id=connector_id,
        state=state,  # type: ignore[arg-type]
        searchable=searchable,
        required_actions=_dedupe(required_actions),
        warnings=_dedupe([*warnings, *policy.warnings]),
    )


def launch_external_link(
    *,
    catalog: ExternalLinkLauncherCatalog,
    launcher_id: str,
    query: str,
) -> ExternalLinkLaunch:
    launcher = next(
        (item for item in catalog.launchers if item.launcher_id == launcher_id),
        None,
    )
    if launcher is None:
        raise ToolExecutionError(
            "External link launcher was not found.",
            details={"launcher_id": launcher_id},
        )
    cleaned_query = " ".join(query.strip().split())
    encoded_query = quote_plus(cleaned_query)
    return ExternalLinkLaunch(
        launcher_id=launcher.launcher_id,
        query=cleaned_query,
        url=launcher.url_template.format(query=encoded_query),
        external_network_call_performed=False,
        query_transparency={
            "connector_id": launcher.connector_id,
            "source_url": launcher.source_url,
            "query_parameter": launcher.query_parameter,
            "encoded_query": encoded_query,
            "url_template": launcher.url_template,
            "backend_fetch": False,
        },
        warnings=[
            launcher.pii_phi_policy,
            "This launcher creates a transparent external URL and does not ingest content.",
            *catalog.warnings,
        ],
    )


def build_etl_export_package(
    package: ClinicalPackage,
    *,
    preview: OmopExportPreview,
    include_resources: bool = True,
) -> EtlExportPackage:
    package_json = json.dumps(package.model_dump(mode="json"), sort_keys=True)
    resource_manifest = [
        EtlExportResourceManifestItem(
            resource_id=record.resource_id,
            resource_type=record.resource_type,
            resource_hash=sha256_text(
                json.dumps(record.resource, sort_keys=True, separators=(",", ":"))
            ),
            source_refs=_source_refs(record),
            provenance_ref_count=len(record.field_provenance),
            review_required=record.review_required,
            warnings=list(record.warnings),
        )
        for record in package.clinical_bundle.resources
    ]
    warnings = [
        "ETL export manifest preserves provenance for downstream analytics teams.",
        "Manifest is not a production OMOP database load.",
        *preview.data_quality_warnings,
    ]
    if preview.review_required:
        warnings.append("OMOP preview still requires review before downstream ETL.")
    return EtlExportPackage(
        package_id=package.package_id,
        workflow_id=package.workflow_id,
        clinical_package_hash=sha256_text(package_json),
        omop_preview=preview,
        resource_manifest=resource_manifest,
        provenance_record_count=len(package.provenance),
        audit_event_refs=list(package.audit_event_refs),
        output_refs=list(package.output_refs),
        included_resources=(
            [record.resource for record in package.clinical_bundle.resources]
            if include_resources
            else []
        ),
        warnings=_dedupe(warnings),
        package=package if include_resources else None,
    )


def _load_contract(path: Path, model: type[ModelT]) -> ModelT:
    if not path.exists():
        raise FileNotFoundError(f"Missing analytics/source catalog: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return model.model_validate(raw)


def _ensure_unique(values: list[str], *, label: str, path: Path) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"Duplicate {label} IDs in {path}: {', '.join(duplicates)}")


def _resource_assignments(
    package: ClinicalPackage,
    profile: OmopMappingProfile,
) -> dict[OmopTargetTable, list[ClinicalResourceRecord]]:
    assignments: dict[OmopTargetTable, list[ClinicalResourceRecord]] = {
        table: [] for table in profile.supported_tables
    }
    for record in package.clinical_bundle.resources:
        for rule in profile.row_rules:
            if record.resource_type not in rule.source_resource_types:
                continue
            if _row_rule_matches(record, rule.condition):
                assignments.setdefault(rule.target_table, []).append(record)
    return assignments


def _row_rule_matches(record: ClinicalResourceRecord, condition: str) -> bool:
    if condition == "resource_type_match":
        return True
    if condition == "has_numeric_value_quantity":
        value = _path_value(record, "resource.valueQuantity.value")
        return _is_number(value)
    if condition == "observation_without_numeric_value_quantity":
        return record.resource_type == "Observation" and not _is_number(
            _path_value(record, "resource.valueQuantity.value")
        )
    if condition == "has_document_content":
        return bool(_path_value(record, "resource.content.0.attachment.url")) or bool(
            _path_value(record, "resource.presentedForm.0.url")
        )
    return False


def _candidate_from_rule_value(
    *,
    package: ClinicalPackage,
    record: ClinicalResourceRecord,
    value: Any,
    rule_system: str,
    target_vocabulary_id: str,
    target_table: OmopTargetTable,
    known_candidates: list[OmopKnownConceptCandidate],
    requires_review: bool,
) -> list[OmopVocabularyCandidate]:
    items: list[tuple[str, str | None, str]] = []
    if isinstance(value, dict):
        system = str(value.get("system") or "").strip()
        code = str(value.get("code") or "").strip()
        display = str(value.get("display") or "").strip() or None
        if system == rule_system and code:
            items.append((code, display, system))
    elif isinstance(value, str) and value.strip():
        items.append((value.strip(), value.strip(), rule_system))
    candidates: list[OmopVocabularyCandidate] = []
    for code, display, system in items:
        known = _find_known_candidate(
            known_candidates,
            source_system=system,
            source_code=code,
        )
        candidates.append(
            _omop_candidate(
                package=package,
                record=record,
                source_system=system,
                source_code=code,
                source_display=display,
                target_vocabulary_id=target_vocabulary_id,
                target_table=target_table,
                known=known,
                confidence=known.confidence if known else 0.45,
                requires_review=requires_review or known is None,
                evidence_ref=known.source_ref if known else None,
                warnings=(
                    []
                    if known and known.standard_concept_id is not None
                    else ["OMOP standard concept ID is unresolved for this candidate."]
                ),
            )
        )
    return candidates


def _omop_candidate(
    *,
    package: ClinicalPackage,
    record: ClinicalResourceRecord | None,
    source_system: str,
    source_code: str,
    source_display: str | None,
    target_vocabulary_id: str,
    target_table: OmopTargetTable,
    known: OmopKnownConceptCandidate | None,
    confidence: float,
    requires_review: bool,
    evidence_ref: str | None,
    warnings: list[str],
) -> OmopVocabularyCandidate:
    return OmopVocabularyCandidate(
        package_id=package.package_id,
        resource_id=record.resource_id if record else package.package_id,
        resource_type=record.resource_type if record else "ClinicalPackage",
        source_system=source_system,
        source_code=source_code,
        source_display=source_display or (known.source_display if known else None),
        target_vocabulary_id=target_vocabulary_id,
        target_table=target_table,
        standard_concept_id=known.standard_concept_id if known else None,
        standard_concept_name=known.standard_concept_name if known else None,
        standard_concept_code=known.standard_concept_code if known else None,
        confidence=confidence,
        requires_review=requires_review or (known.requires_review if known else True),
        evidence_ref=evidence_ref,
        warnings=warnings,
    )


def _find_known_candidate(
    known_candidates: list[OmopKnownConceptCandidate],
    *,
    source_system: str,
    source_code: str,
) -> OmopKnownConceptCandidate | None:
    for candidate in known_candidates:
        if (
            candidate.source_system == source_system
            and candidate.source_code.lower() == source_code.lower()
        ):
            return candidate
    return None


def _candidate_lookup_by_resource_table(
    candidates: list[OmopVocabularyCandidate],
) -> dict[tuple[str, OmopTargetTable], list[OmopVocabularyCandidate]]:
    lookup: dict[tuple[str, OmopTargetTable], list[OmopVocabularyCandidate]] = {}
    for candidate in candidates:
        lookup.setdefault((candidate.resource_id, candidate.target_table), []).append(candidate)
    return lookup


def _dedupe_candidates(
    candidates: list[OmopVocabularyCandidate],
) -> list[OmopVocabularyCandidate]:
    seen: set[tuple[str, str, str, str]] = set()
    unique: list[OmopVocabularyCandidate] = []
    for candidate in candidates:
        key = (
            candidate.resource_id,
            candidate.source_system,
            candidate.source_code.lower(),
            candidate.target_vocabulary_id,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _record_for_terminology_candidate(
    records: list[ClinicalResourceRecord],
    source_value: str,
    source_row: int | None,
) -> ClinicalResourceRecord | None:
    if source_row is not None:
        by_row = _record_for_source_row(records, source_row)
        if by_row:
            return by_row
    normalized_source = source_value.strip().lower()
    return next(
        (
            record
            for record in records
            if str(_path_value(record, "resource.code.text") or "").strip().lower()
            == normalized_source
        ),
        records[0] if records else None,
    )


def _record_for_source_row(
    records: list[ClinicalResourceRecord],
    source_row: int | None,
) -> ClinicalResourceRecord | None:
    if source_row is None:
        return records[0] if records else None
    return next(
        (record for record in records if record.source_row == source_row),
        records[0] if records else None,
    )


def _standard_system_to_uri(value: str) -> str:
    normalized = value.strip().upper()
    if normalized == "LOINC":
        return "http://loinc.org"
    if normalized == "UCUM":
        return "http://unitsofmeasure.org"
    if normalized == "RXNORM":
        return "http://www.nlm.nih.gov/research/umls/rxnorm"
    if normalized == "SNOMED":
        return "http://snomed.info/sct"
    return value


def _path_has_value(record: ClinicalResourceRecord, path: str) -> bool:
    values = _path_values(record, path)
    return any(value not in (None, "", [], {}) for value in values)


def _path_values(record: ClinicalResourceRecord, path: str) -> list[Any]:
    value = _path_value(record, path)
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _path_value(record: ClinicalResourceRecord, path: str) -> Any:
    root: Any = record
    for part in path.split("."):
        if isinstance(root, ClinicalResourceRecord):
            root = getattr(root, part, None)
        elif isinstance(root, dict):
            root = root.get(part)
        elif isinstance(root, list):
            try:
                root = root[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
        if root is None:
            return None
    return root


def _source_refs(record: ClinicalResourceRecord) -> list[str]:
    refs: list[str] = []
    for provenance in record.field_provenance:
        if provenance.location and provenance.location.source_ref:
            refs.append(provenance.location.source_ref)
    return _dedupe(refs)


def _is_number(value: Any) -> bool:
    if isinstance(value, bool) or value in (None, ""):
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        clean = str(value).strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        unique.append(clean)
    return unique


def _normalize_query(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _parse_datetime(value: str) -> datetime:
    clean = value.strip()
    if clean.endswith("Z"):
        clean = f"{clean[:-1]}+00:00"
    parsed = datetime.fromisoformat(clean)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
