"""Lightweight FHIR-like resource profiling.

This is not a full HL7 FHIR validator. It detects FHIR-like shape, profiles
resource types, and emits handoff context for later Graph-NER/RAG integration.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.errors import ToolExecutionError
from ojtflow.medical.contracts import FhirProfile


def profile_fhir_like(text: str) -> dict[str, Any]:
    """Profile FHIR-like JSON resource or Bundle text."""

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ToolExecutionError(f"Invalid FHIR-like JSON: {exc.msg}") from exc

    issues: list[str] = []
    resources = _extract_resources(payload, issues)
    resource_counts = Counter(
        resource.get("resourceType", "Unknown")
        for resource in resources
        if isinstance(resource, dict)
    )
    root_resource_type = payload.get("resourceType") if isinstance(payload, dict) else None
    is_fhir_like = bool(root_resource_type or resource_counts)

    if not is_fhir_like:
        issues.append("Missing root resourceType or Bundle.entry resources")
    if root_resource_type == "Bundle" and "entry" not in payload:
        issues.append("Bundle is missing entry array")
    _validate_minimal_resource_shapes(resources, issues)

    evidence = [
        Evidence(
            source_type=EvidenceSourceType.SCHEMA,
            source_id=f"fhir_like:{resource_type}",
            source_version="fhir_like_profile.v0",
            claim=f"Detected FHIR-like resource type '{resource_type}'",
            confidence=0.85,
            trust_level=TrustLevel.INTERNAL,
        )
        for resource_type in sorted(resource_counts)
    ]
    profile = FhirProfile(
        is_fhir_like=is_fhir_like,
        resource_type=root_resource_type,
        resource_counts=dict(resource_counts),
        issues=issues,
        evidence_ids=[item.evidence_id for item in evidence],
        handoff_context={
            "resource_types": sorted(resource_counts),
            "graphner_ready": is_fhir_like,
            "rag_query_terms": sorted(resource_counts),
        },
    )
    return {"profile": profile, "evidence": evidence}


def _extract_resources(payload: Any, issues: list[str]) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        issues.append("FHIR-like input must be a JSON object")
        return []

    resource_type = payload.get("resourceType")
    if resource_type == "Bundle":
        entries = payload.get("entry")
        if not isinstance(entries, list):
            issues.append("Bundle.entry must be an array")
            return []
        resources: list[dict[str, Any]] = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                issues.append(f"Bundle.entry[{index}] must be an object")
                continue
            resource = entry.get("resource")
            if not isinstance(resource, dict):
                issues.append(f"Bundle.entry[{index}].resource is missing or not an object")
                continue
            if not resource.get("resourceType"):
                issues.append(f"Bundle.entry[{index}].resource is missing resourceType")
            resources.append(resource)
        return resources

    return [payload] if resource_type else []


def _validate_minimal_resource_shapes(
    resources: list[dict[str, Any]],
    issues: list[str],
) -> None:
    """Validate lightweight FHIR-like shape for known healthcare demo resources."""

    for index, resource in enumerate(resources):
        resource_type = resource.get("resourceType")
        prefix = f"{resource_type or 'Resource'}[{index}]"
        if resource_type == "Observation":
            for field in ("status", "code"):
                if field not in resource:
                    issues.append(f"{prefix} is missing '{field}'")
            if "subject" not in resource:
                issues.append(f"{prefix} is missing 'subject'")
            if not _has_any(resource, ("effectiveDateTime", "effectivePeriod", "issued")):
                issues.append(
                    f"{prefix} is missing effective time ('effectiveDateTime', 'effectivePeriod', or 'issued')"
                )
            if not _has_any(
                resource,
                (
                    "valueQuantity",
                    "valueCodeableConcept",
                    "valueString",
                    "valueBoolean",
                    "valueInteger",
                    "valueRange",
                    "component",
                ),
            ):
                issues.append(f"{prefix} is missing observation value or component")
        elif resource_type == "Patient" and not _has_any(resource, ("id", "identifier")):
            issues.append(f"{prefix} is missing 'id' or 'identifier'")


def _has_any(resource: dict[str, Any], field_names: tuple[str, ...]) -> bool:
    return any(field in resource and resource[field] not in (None, "", []) for field in field_names)
