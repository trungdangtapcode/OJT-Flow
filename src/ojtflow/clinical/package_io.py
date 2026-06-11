"""Canonical export and reload validation for ClinicalPackage v0."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from ojtflow.core.contracts.clinical import (
    ClinicalPackage,
    ClinicalPackageExport,
    ClinicalPackageImportIssue,
    ClinicalPackageImportValidation,
    ClinicalProvenanceRecord,
    ClinicalResourceRecord,
)
from ojtflow.core.contracts.enums import Severity
from ojtflow.core.errors import ToolExecutionError
from ojtflow.core.time import utc_now
from ojtflow.data_tools.hashing import sha256_text


EXPORT_SCHEMA_VERSION = "clinical_package_export.v0"
FHIR_LIKE_BOUNDARY_WARNING = (
    "FHIR-like Bundle export has not been validated by a full HL7 FHIR validator."
)
OJT_FLOW_FHIR_LIKE_SYSTEM = "urn:ojtflow:fhir-like"


def export_clinical_package(
    package: ClinicalPackage,
    *,
    require_approval: bool = True,
    metadata: dict[str, Any] | None = None,
) -> ClinicalPackageExport:
    """Build a canonical export envelope for a governed clinical package."""

    approved, approval_warnings = clinical_package_export_approval(package)
    if require_approval and not approved:
        raise ToolExecutionError(
            "Clinical package is not approved for export.",
            workflow_id=package.workflow_id,
            details={
                "package_id": package.package_id,
                "review_status": _review_status(package),
                "warnings": approval_warnings,
            },
        )

    fhir_like_bundle = build_fhir_like_bundle(package)
    package_hash = hash_json(package)
    bundle_hash = hash_json(fhir_like_bundle)
    warnings = _unique_non_empty(
        [
            *approval_warnings,
            *package.warnings,
            FHIR_LIKE_BOUNDARY_WARNING,
        ]
    )
    export_metadata = {
        "boundary": "fhir_like_not_full_hl7_validation",
        "package_type": package.package_type,
        "source": "ojtflow_workflow_state",
    }
    export_metadata.update(metadata or {})

    return ClinicalPackageExport(
        schema_version=EXPORT_SCHEMA_VERSION,
        workflow_id=package.workflow_id,
        package_id=package.package_id,
        package_schema_version=package.schema_version,
        package_hash=package_hash,
        fhir_like_bundle_hash=bundle_hash,
        approved_for_export=approved,
        review_status=_review_status(package),
        resource_count=len(package.clinical_bundle.resources),
        evidence_count=len(package.evidence),
        provenance_count=len(package.provenance),
        operation_outcome_issue_count=len(package.operation_outcome.issue),
        warnings=warnings,
        metadata=export_metadata,
        clinical_package=package,
        fhir_like_bundle=fhir_like_bundle,
    )


def validate_clinical_package_export(
    payload: dict[str, Any] | str,
    *,
    require_hash_match: bool = True,
) -> ClinicalPackageImportValidation:
    """Validate and rehydrate an OJTFlow clinical package export."""

    issues: list[ClinicalPackageImportIssue] = []
    warnings: list[str] = []
    parsed = _parse_payload(payload, issues)
    if parsed is None:
        return _validation_result(issues=issues, warnings=warnings)

    package_payload, expected_package_hash, bundle_payload, expected_bundle_hash = (
        _extract_package_payload(parsed, issues)
    )
    if package_payload is None:
        return _validation_result(
            issues=issues,
            warnings=warnings,
            expected_package_hash=expected_package_hash,
            expected_fhir_like_bundle_hash=expected_bundle_hash,
            fhir_like_bundle=bundle_payload,
        )

    package = _load_package(package_payload, issues)
    if package is None:
        return _validation_result(
            issues=issues,
            warnings=warnings,
            expected_package_hash=expected_package_hash,
            expected_fhir_like_bundle_hash=expected_bundle_hash,
            fhir_like_bundle=bundle_payload,
        )

    package_hash = hash_json(package)
    if require_hash_match and expected_package_hash and package_hash != expected_package_hash:
        issues.append(
            ClinicalPackageImportIssue(
                severity=Severity.ERROR,
                code="package_hash_mismatch",
                message="Clinical package hash does not match the export manifest.",
                path="package_hash",
            )
        )

    if bundle_payload is None:
        bundle_payload = build_fhir_like_bundle(package)
        warnings.append("No FHIR-like Bundle was supplied; rebuilt it from the clinical package.")
    bundle_hash = hash_json(bundle_payload)
    if require_hash_match and expected_bundle_hash and bundle_hash != expected_bundle_hash:
        issues.append(
            ClinicalPackageImportIssue(
                severity=Severity.ERROR,
                code="bundle_hash_mismatch",
                message="FHIR-like Bundle hash does not match the export manifest.",
                path="fhir_like_bundle_hash",
            )
        )
    _validate_bundle_shape(bundle_payload, package, issues, warnings)
    if not package.provenance:
        warnings.append("Clinical package has no provenance records.")
    if not package.evidence:
        warnings.append("Clinical package has no evidence records.")

    return _validation_result(
        issues=issues,
        warnings=warnings,
        package=package,
        package_hash=package_hash,
        expected_package_hash=expected_package_hash,
        fhir_like_bundle_hash=bundle_hash,
        expected_fhir_like_bundle_hash=expected_bundle_hash,
        fhir_like_bundle=bundle_payload,
    )


def build_fhir_like_bundle(package: ClinicalPackage) -> dict[str, Any]:
    """Project a ClinicalPackage into a FHIR-like Bundle dictionary."""

    bundle_id = f"{package.package_id}-bundle"
    entries: list[dict[str, Any]] = []
    for record in package.clinical_bundle.resources:
        entries.append(_resource_entry(package, record))
    if package.operation_outcome.issue:
        entries.append(
            {
                "fullUrl": f"urn:ojtflow:{package.workflow_id}:operation-outcome",
                "resource": {
                    **package.operation_outcome.model_dump(mode="json"),
                    "id": f"{package.package_id}-operation-outcome",
                },
            }
        )
    for provenance in package.provenance:
        entries.append(_provenance_entry(package, provenance, bundle_id))

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": package.clinical_bundle.type,
        "meta": {
            "lastUpdated": package.updated_at,
            "tag": [
                {
                    "system": OJT_FLOW_FHIR_LIKE_SYSTEM,
                    "code": package.schema_version,
                    "display": "OJTFlow ClinicalPackage v0",
                },
                {
                    "system": OJT_FLOW_FHIR_LIKE_SYSTEM,
                    "code": "fhir_like_not_validated",
                    "display": "FHIR-like package without full HL7 validation",
                },
            ],
        },
        "entry": entries,
    }


def clinical_package_export_approval(package: ClinicalPackage) -> tuple[bool, list[str]]:
    """Return whether a clinical package is eligible for outbound export."""

    warnings: list[str] = []
    review_status = _review_status(package)
    if review_status in {"approved", "approved_with_edits"}:
        return True, warnings
    if review_status:
        warnings.append(f"clinical package review status is {review_status}")
        return False, warnings
    if any(record.review_required for record in package.clinical_bundle.resources):
        warnings.append("clinical package has resources that still require review")
        return False, warnings
    warnings.append(
        "clinical package has no explicit review record; export allowed because no resource is review-gated"
    )
    return True, warnings


def canonical_json(value: Any) -> str:
    """Serialize a model or JSON-like value into stable canonical JSON."""

    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def hash_json(value: Any) -> str:
    """Return the SHA-256 hex digest of canonical JSON."""

    return sha256_text(canonical_json(value))


def _parse_payload(
    payload: dict[str, Any] | str,
    issues: list[ClinicalPackageImportIssue],
) -> dict[str, Any] | None:
    if isinstance(payload, str):
        try:
            loaded = json.loads(payload)
        except json.JSONDecodeError as exc:
            issues.append(
                ClinicalPackageImportIssue(
                    severity=Severity.ERROR,
                    code="invalid_json",
                    message=f"Clinical package export is not valid JSON: {exc.msg}",
                    path=None,
                )
            )
            return None
    else:
        loaded = payload
    if not isinstance(loaded, dict):
        issues.append(
            ClinicalPackageImportIssue(
                severity=Severity.ERROR,
                code="invalid_export_payload",
                message="Clinical package export payload must be a JSON object.",
                path=None,
            )
        )
        return None
    return loaded


def _extract_package_payload(
    payload: dict[str, Any],
    issues: list[ClinicalPackageImportIssue],
) -> tuple[dict[str, Any] | None, str | None, dict[str, Any] | None, str | None]:
    expected_package_hash = _optional_text(payload.get("package_hash"))
    expected_bundle_hash = _optional_text(payload.get("fhir_like_bundle_hash"))
    bundle_payload = payload.get("fhir_like_bundle")
    if bundle_payload is not None and not isinstance(bundle_payload, dict):
        issues.append(
            ClinicalPackageImportIssue(
                severity=Severity.ERROR,
                code="invalid_bundle",
                message="fhir_like_bundle must be a JSON object when supplied.",
                path="fhir_like_bundle",
            )
        )
        bundle_payload = None

    package_payload = payload.get("clinical_package")
    if package_payload is None and payload.get("package_type") == "ojtflow_clinical_package":
        package_payload = payload
    if package_payload is None:
        issues.append(
            ClinicalPackageImportIssue(
                severity=Severity.ERROR,
                code="missing_clinical_package",
                message="Export payload must contain clinical_package.",
                path="clinical_package",
            )
        )
        return None, expected_package_hash, bundle_payload, expected_bundle_hash
    if not isinstance(package_payload, dict):
        issues.append(
            ClinicalPackageImportIssue(
                severity=Severity.ERROR,
                code="invalid_clinical_package",
                message="clinical_package must be a JSON object.",
                path="clinical_package",
            )
        )
        return None, expected_package_hash, bundle_payload, expected_bundle_hash
    return package_payload, expected_package_hash, bundle_payload, expected_bundle_hash


def _load_package(
    package_payload: dict[str, Any],
    issues: list[ClinicalPackageImportIssue],
) -> ClinicalPackage | None:
    try:
        return ClinicalPackage.model_validate(package_payload)
    except ValidationError as exc:
        for error in exc.errors():
            issues.append(
                ClinicalPackageImportIssue(
                    severity=Severity.ERROR,
                    code="schema_validation_error",
                    message=str(error.get("msg") or "Clinical package schema validation failed."),
                    path=_format_path(error.get("loc")),
                )
            )
        return None


def _validate_bundle_shape(
    bundle: dict[str, Any],
    package: ClinicalPackage,
    issues: list[ClinicalPackageImportIssue],
    warnings: list[str],
) -> None:
    if bundle.get("resourceType") != "Bundle":
        issues.append(
            ClinicalPackageImportIssue(
                severity=Severity.ERROR,
                code="invalid_bundle_resource_type",
                message="FHIR-like export must have resourceType=Bundle.",
                path="fhir_like_bundle.resourceType",
            )
        )
    entries = bundle.get("entry")
    if not isinstance(entries, list):
        issues.append(
            ClinicalPackageImportIssue(
                severity=Severity.ERROR,
                code="invalid_bundle_entries",
                message="FHIR-like Bundle entry must be a list.",
                path="fhir_like_bundle.entry",
            )
        )
        return
    exported_keys: set[tuple[str, str]] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            issues.append(
                ClinicalPackageImportIssue(
                    severity=Severity.ERROR,
                    code="invalid_bundle_entry",
                    message="FHIR-like Bundle entry must be a JSON object.",
                    path=f"fhir_like_bundle.entry[{index}]",
                )
            )
            continue
        resource = entry.get("resource")
        if not isinstance(resource, dict):
            issues.append(
                ClinicalPackageImportIssue(
                    severity=Severity.ERROR,
                    code="missing_bundle_resource",
                    message="FHIR-like Bundle entry is missing a resource object.",
                    path=f"fhir_like_bundle.entry[{index}].resource",
                )
            )
            continue
        resource_type = _optional_text(resource.get("resourceType"))
        resource_id = _optional_text(resource.get("id"))
        if not resource_type:
            issues.append(
                ClinicalPackageImportIssue(
                    severity=Severity.ERROR,
                    code="missing_resource_type",
                    message="FHIR-like Bundle resource is missing resourceType.",
                    path=f"fhir_like_bundle.entry[{index}].resource.resourceType",
                )
            )
        if resource_type and resource_id:
            exported_keys.add((resource_type, resource_id))

    missing = [
        f"{record.resource_type}/{record.resource_id}"
        for record in package.clinical_bundle.resources
        if (record.resource_type, record.resource_id) not in exported_keys
    ]
    if missing:
        issues.append(
            ClinicalPackageImportIssue(
                severity=Severity.ERROR,
                code="bundle_missing_package_resources",
                message="FHIR-like Bundle is missing clinical package resources.",
                path="fhir_like_bundle.entry",
            )
        )
    provenance_count = sum(
        1
        for entry in entries
        if isinstance(entry, dict)
        and isinstance(entry.get("resource"), dict)
        and entry["resource"].get("resourceType") == "Provenance"
    )
    if package.provenance and provenance_count < len(package.provenance):
        warnings.append("FHIR-like Bundle has fewer Provenance resources than the clinical package.")


def _resource_entry(package: ClinicalPackage, record: ClinicalResourceRecord) -> dict[str, Any]:
    resource = dict(record.resource)
    resource.setdefault("id", record.resource_id)
    return {
        "fullUrl": f"urn:ojtflow:{package.workflow_id}:{record.resource_type}:{record.resource_id}",
        "resource": resource,
    }


def _provenance_entry(
    package: ClinicalPackage,
    provenance: ClinicalProvenanceRecord,
    bundle_id: str,
) -> dict[str, Any]:
    target_refs = provenance.target_refs or [f"Bundle/{bundle_id}"]
    resource = {
        "resourceType": "Provenance",
        "id": provenance.provenance_id,
        "recorded": provenance.occurred_at or utc_now().isoformat(),
        "activity": {"text": provenance.activity},
        "target": [{"reference": _normal_resource_ref(ref)} for ref in target_refs],
        "agent": [
            {
                "who": {"display": provenance.agent},
                "type": {"text": provenance.agent},
            }
        ],
        "entity": [
            {"role": "source", "what": {"reference": _normal_resource_ref(ref)}}
            for ref in provenance.source_refs
        ],
        "reason": [{"text": provenance.summary}],
        "extension": [
            {
                "url": f"{OJT_FLOW_FHIR_LIKE_SYSTEM}/evidence-ids",
                "valueString": ",".join(provenance.evidence_ids),
            },
            {
                "url": f"{OJT_FLOW_FHIR_LIKE_SYSTEM}/issue-ids",
                "valueString": ",".join(provenance.issue_ids),
            },
        ],
    }
    if provenance.metadata:
        resource["meta"] = {"source": f"urn:ojtflow:{package.workflow_id}:provenance"}
        resource["containedMetadata"] = provenance.metadata
    return {
        "fullUrl": f"urn:ojtflow:{package.workflow_id}:Provenance:{provenance.provenance_id}",
        "resource": resource,
    }


def _normal_resource_ref(ref: str) -> str:
    if "://" in ref or ref.startswith("urn:") or "/" in ref:
        return ref
    return f"urn:ojtflow:{ref}"


def _validation_result(
    *,
    issues: list[ClinicalPackageImportIssue],
    warnings: list[str],
    package: ClinicalPackage | None = None,
    package_hash: str | None = None,
    expected_package_hash: str | None = None,
    fhir_like_bundle_hash: str | None = None,
    expected_fhir_like_bundle_hash: str | None = None,
    fhir_like_bundle: dict[str, Any] | None = None,
) -> ClinicalPackageImportValidation:
    error_count = sum(1 for issue in issues if issue.severity == Severity.ERROR)
    return ClinicalPackageImportValidation(
        valid=error_count == 0,
        package_hash=package_hash,
        expected_package_hash=expected_package_hash,
        fhir_like_bundle_hash=fhir_like_bundle_hash,
        expected_fhir_like_bundle_hash=expected_fhir_like_bundle_hash,
        workflow_id=package.workflow_id if package else None,
        package_id=package.package_id if package else None,
        resource_count=len(package.clinical_bundle.resources) if package else 0,
        evidence_count=len(package.evidence) if package else 0,
        provenance_count=len(package.provenance) if package else 0,
        operation_outcome_issue_count=len(package.operation_outcome.issue) if package else 0,
        issues=issues,
        warnings=_unique_non_empty(warnings),
        clinical_package=package,
        fhir_like_bundle=fhir_like_bundle,
    )


def _review_status(package: ClinicalPackage) -> str | None:
    review = package.review or {}
    value = review.get("status") if isinstance(review, dict) else None
    return str(value).strip() if value else None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _format_path(location: Any) -> str | None:
    if not location:
        return None
    if isinstance(location, str):
        return location
    if isinstance(location, (tuple, list)):
        return ".".join(str(part) for part in location)
    return str(location)


def _unique_non_empty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            unique.append(text)
            seen.add(text)
    return unique
