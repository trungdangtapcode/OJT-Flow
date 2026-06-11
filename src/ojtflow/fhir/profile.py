"""Lightweight FHIR-like resource profiling.

This is not a full HL7 FHIR validator. It detects FHIR-like shape, profiles
resource types, and emits handoff context for later Graph-NER/RAG integration.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.errors import ToolExecutionError
from ojtflow.medical.contracts import (
    FhirResourceProfileCatalog,
    FhirResourceProfileSpec,
    FhirProfile,
)


DEFAULT_FHIR_PROFILE_REGISTRY_PATH = (
    Path(__file__).resolve().parents[3] / "knowledge" / "fhir" / "resource_profiles.json"
)


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
    catalog = load_fhir_resource_profile_catalog()
    profile_issues = _validate_minimal_resource_shapes(resources, catalog)
    issues.extend(issue["message"] for issue in profile_issues)
    profiled_resource_types = sorted(
        resource_type
        for resource_type in resource_counts
        if _profile_for_resource(catalog, resource_type) is not None
    )
    search_parameters = {
        resource_type: [
            parameter.model_dump(mode="json")
            for parameter in profile.search_parameters
        ]
        for resource_type in profiled_resource_types
        if (profile := _profile_for_resource(catalog, resource_type)) is not None
    }
    profile_evidence = [
        {
            "resource_type": profile.resource_type,
            "profile_id": profile.profile_id,
            "source_url": profile.source_url,
            "clinical_domain": profile.clinical_domain,
            "governance_notes": list(profile.governance_notes),
        }
        for resource_type in profiled_resource_types
        if (profile := _profile_for_resource(catalog, resource_type)) is not None
    ]

    evidence = [
        Evidence(
            source_type=EvidenceSourceType.SCHEMA,
            source_id=f"fhir_like:{resource_type}",
            source_version=catalog.version,
            claim=_profile_claim(catalog, resource_type),
            confidence=0.85,
            trust_level=TrustLevel.INTERNAL,
            locator={
                "profile_registry_version": catalog.version,
                "fhir_release": catalog.fhir_release,
                "profile": _profile_locator(catalog, resource_type),
            },
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
            "rag_query_terms": _rag_query_terms(resource_counts, search_parameters),
            "profile_registry_version": catalog.version,
            "fhir_release": catalog.fhir_release,
            "profiled_resource_types": profiled_resource_types,
            "search_parameters_by_resource": search_parameters,
            "profile_sources": {
                item["resource_type"]: item["source_url"] for item in profile_evidence
            },
        },
        profile_registry_version=catalog.version,
        profiled_resource_types=profiled_resource_types,
        profile_issues=profile_issues,
        search_parameters=search_parameters,
        profile_evidence=profile_evidence,
    )
    return {"profile": profile, "evidence": evidence}


def load_fhir_resource_profile_catalog(
    path: Path | None = None,
) -> FhirResourceProfileCatalog:
    """Load lightweight FHIR-like resource profile registry from trusted data."""

    registry_path = path or _registry_path_from_env()
    return _load_fhir_resource_profile_catalog(str(registry_path))


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


@lru_cache(maxsize=8)
def _load_fhir_resource_profile_catalog(path: str) -> FhirResourceProfileCatalog:
    registry_path = Path(path)
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    catalog = FhirResourceProfileCatalog.model_validate(raw)
    _ensure_unique_profiles(catalog, registry_path)
    return catalog


def _registry_path_from_env() -> Path:
    configured = os.getenv("OJT_FHIR_RESOURCE_PROFILES_PATH")
    return Path(configured) if configured else DEFAULT_FHIR_PROFILE_REGISTRY_PATH


def _ensure_unique_profiles(catalog: FhirResourceProfileCatalog, path: Path) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for profile in catalog.profiles:
        if profile.resource_type in seen:
            duplicates.add(profile.resource_type)
        seen.add(profile.resource_type)
    if duplicates:
        raise ValueError(
            f"Invalid FHIR profile registry at {path}: duplicate resource_type "
            f"{', '.join(sorted(duplicates))}"
        )


def _validate_minimal_resource_shapes(
    resources: list[dict[str, Any]],
    catalog: FhirResourceProfileCatalog,
) -> list[dict[str, Any]]:
    """Validate lightweight FHIR-like shape from the data-driven registry."""

    issues: list[dict[str, Any]] = []
    for index, resource in enumerate(resources):
        resource_type = resource.get("resourceType")
        prefix = f"{resource_type or 'Resource'}[{index}]"
        profile = _profile_for_resource(catalog, str(resource_type or ""))
        if profile is None:
            issues.append(
                _profile_issue(
                    resource_type=str(resource_type or "Resource"),
                    index=index,
                    path=f"{prefix}.resourceType",
                    message=f"{prefix} has no OJTFlow FHIR-like profile registry entry",
                    profile_id=None,
                )
            )
            continue
        for field in profile.required_fields:
            if not _has_field(resource, field):
                issues.append(
                    _profile_issue(
                        resource_type=profile.resource_type,
                        index=index,
                        path=f"{prefix}.{field}",
                        message=f"{prefix} is missing '{field}'",
                        profile_id=profile.profile_id,
                    )
                )
        for group in profile.required_any:
            if not _has_any(resource, tuple(group.fields)):
                issues.append(
                    _profile_issue(
                        resource_type=profile.resource_type,
                        index=index,
                        path=f"{prefix}.{group.group_id}",
                        message=f"{prefix} {group.message}",
                        profile_id=profile.profile_id,
                        metadata={"fields": list(group.fields)},
                    )
                )
    return issues


def _has_any(resource: dict[str, Any], field_names: tuple[str, ...]) -> bool:
    return any(_has_field(resource, field) for field in field_names)


def _has_field(resource: dict[str, Any], field_name: str) -> bool:
    value = resource.get(field_name)
    return value not in (None, "", [])


def _profile_for_resource(
    catalog: FhirResourceProfileCatalog,
    resource_type: str,
) -> FhirResourceProfileSpec | None:
    for profile in catalog.profiles:
        if profile.resource_type == resource_type:
            return profile
    return None


def _profile_issue(
    *,
    resource_type: str,
    index: int,
    path: str,
    message: str,
    profile_id: str | None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "resource_type": resource_type,
        "index": index,
        "path": path,
        "severity": "warning",
        "profile_id": profile_id,
        "message": message,
        "metadata": metadata or {},
    }


def _profile_claim(catalog: FhirResourceProfileCatalog, resource_type: str) -> str:
    profile = _profile_for_resource(catalog, resource_type)
    if profile is None:
        return f"Detected FHIR-like resource type '{resource_type}' without local profile registry entry"
    return (
        f"Detected FHIR-like resource type '{resource_type}' using profile "
        f"{profile.profile_id}"
    )


def _profile_locator(catalog: FhirResourceProfileCatalog, resource_type: str) -> dict[str, Any]:
    profile = _profile_for_resource(catalog, resource_type)
    if profile is None:
        return {}
    return {
        "profile_id": profile.profile_id,
        "source_url": profile.source_url,
        "search_parameters": [
            parameter.model_dump(mode="json") for parameter in profile.search_parameters
        ],
    }


def _rag_query_terms(
    resource_counts: Counter[str],
    search_parameters: dict[str, list[dict[str, Any]]],
) -> list[str]:
    terms = set(resource_counts)
    for resource_type, parameters in search_parameters.items():
        for parameter in parameters:
            name = parameter.get("name")
            if isinstance(name, str) and name:
                terms.add(f"{resource_type}.{name}")
    return sorted(terms)
