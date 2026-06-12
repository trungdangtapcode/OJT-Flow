"""Citation locator normalization for retrieval evidence."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from string import Formatter
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType
from ojtflow.core.contracts.retrieval import (
    CitationLocatorRule,
    CitationLocatorRuleCatalog,
    NormalizedCitationLocator,
)


DEFAULT_CITATION_LOCATOR_RULES_PATH = (
    Path(__file__).resolve().parents[4] / "knowledge" / "retrieval" / "citation_locator_rules.json"
)
RESOURCE_TYPE_PATTERN = re.compile(
    r"\b(Patient|Observation|Condition|AllergyIntolerance|DiagnosticReport|DocumentReference)\b",
    re.IGNORECASE,
)
NCT_PATTERN = re.compile(r"\bNCT\d{8}\b", re.IGNORECASE)
PMID_PATTERN = re.compile(r"\bPMID[:\s]*(\d{4,12})\b", re.IGNORECASE)
RXCUI_PATTERN = re.compile(r"\bRXCUI[:\s]*(\d{2,12})\b", re.IGNORECASE)


def normalize_citation_locator(
    *,
    source_id: str,
    source_type: EvidenceSourceType,
    source_version: str | None,
    title: str,
    locator: dict[str, Any],
) -> NormalizedCitationLocator | None:
    """Normalize a raw source locator into a portable citation locator."""

    context = _locator_context(
        source_id=source_id,
        source_type=source_type,
        source_version=source_version,
        title=title,
        locator=locator,
    )
    for rule in active_citation_locator_rules().rules:
        if not _rule_matches(rule, context=context, locator=locator):
            continue
        if not _has_required_context(rule.required_context_keys, context):
            continue
        display = _render_template(rule.display_template, context) or rule.label
        canonical_url = (
            _render_template(rule.canonical_url_template, context)
            if rule.canonical_url_template
            else None
        )
        identifier = _first_context_value(rule.identifier_keys, context)
        page = _positive_int(context.get("page"))
        raw_keys = sorted(str(key) for key in locator if str(key).strip())
        return NormalizedCitationLocator(
            rule_id=rule.rule_id,
            locator_kind=rule.locator_kind,
            label=rule.label,
            display=display,
            source_id=source_id,
            source_type=source_type,
            source_version=source_version,
            standard_system=_optional_text(context.get("standard_system")),
            canonical_url=canonical_url,
            identifier=identifier,
            path=_optional_text(context.get("path")),
            page=page,
            section=_optional_text(context.get("section_heading") or context.get("section")),
            raw_locator_keys=raw_keys,
            warnings=list(rule.warnings),
            metadata={
                **rule.metadata,
                "matched_rule_priority": rule.priority,
            },
        )
    return None


def active_citation_locator_rules() -> CitationLocatorRuleCatalog:
    """Load active citation locator rules from trusted data."""

    path = os.environ.get("OJT_CITATION_LOCATOR_RULES_PATH")
    return _load_citation_locator_rules(path or str(DEFAULT_CITATION_LOCATOR_RULES_PATH))


@lru_cache(maxsize=4)
def _load_citation_locator_rules(path_text: str) -> CitationLocatorRuleCatalog:
    path = Path(path_text)
    if not path.exists():
        return CitationLocatorRuleCatalog(version="citation_locator_rules.empty", rules=[])
    raw = json.loads(path.read_text(encoding="utf-8"))
    catalog = CitationLocatorRuleCatalog.model_validate(raw)
    rule_ids = [rule.rule_id for rule in catalog.rules]
    duplicates = sorted({rule_id for rule_id in rule_ids if rule_ids.count(rule_id) > 1})
    if duplicates:
        duplicate_text = ", ".join(duplicates)
        raise ValueError(
            f"Invalid citation locator rules at {path}: duplicate rule_id {duplicate_text}"
        )
    return CitationLocatorRuleCatalog(
        version=catalog.version,
        rules=sorted(catalog.rules, key=lambda rule: (rule.priority, rule.rule_id)),
    )


def _locator_context(
    *,
    source_id: str,
    source_type: EvidenceSourceType,
    source_version: str | None,
    title: str,
    locator: dict[str, Any],
) -> dict[str, Any]:
    context = {
        key: value
        for key, value in locator.items()
        if isinstance(key, str)
    }
    context.update(
        {
            "source_id": source_id,
            "source_type": source_type.value,
            "source_version": source_version,
            "title": title,
            "standard_system": context.get("standard_system"),
        }
    )
    standard = _optional_text(context.get("standard")) or ""
    if not _optional_text(context.get("standard_system")):
        inferred_standard_system = _infer_standard_system(
            source_id=source_id,
            standard=standard,
            title=title,
        )
        if inferred_standard_system:
            context["standard_system"] = inferred_standard_system
    combined_text = " ".join(
        _optional_text(value) or ""
        for value in (
            title,
            standard,
            source_id,
            context.get("resource_type"),
            context.get("standard_system"),
        )
    )
    resource_type = _optional_text(context.get("resource_type")) or _extract_regex(
        RESOURCE_TYPE_PATTERN,
        combined_text,
    )
    if resource_type:
        context["resource_type"] = _canonical_resource_type(resource_type)
        context["resource_type_slug"] = _slug(context["resource_type"])
    pmid = _optional_text(context.get("pmid")) or _extract_regex(PMID_PATTERN, combined_text)
    if pmid:
        context["pmid"] = pmid
    nct_id = _optional_text(context.get("nct_id")) or _extract_regex(NCT_PATTERN, combined_text)
    if nct_id:
        context["nct_id"] = nct_id.upper()
    rxcui = _optional_text(context.get("rxcui")) or _extract_regex(RXCUI_PATTERN, combined_text)
    if rxcui:
        context["rxcui"] = rxcui
    if not _optional_text(context.get("unit_code")) and context.get("standard_system") == "UCUM":
        context["unit_code"] = _optional_text(context.get("standard")) or "UCUM"
    if not _optional_text(context.get("openfda_endpoint")) and context.get("standard_system") == "openFDA":
        context["openfda_endpoint"] = "drug"
    if not _optional_text(context.get("path")) and _optional_text(context.get("source_ref")):
        context["path"] = context["source_ref"]
    return context


def _infer_standard_system(
    *,
    source_id: str,
    standard: str,
    title: str,
) -> str | None:
    combined = f"{source_id} {standard} {title}".lower()
    if "fhir" in combined:
        return "FHIR"
    if "pubmed" in combined or "mesh" in combined:
        return "MeSH"
    if "clinicaltrials" in combined:
        return "ClinicalTrials.gov"
    if "openfda" in combined:
        return "openFDA"
    if "ucum" in combined:
        return "UCUM"
    if "rxnorm" in combined or "rxnav" in combined:
        return "RxNorm"
    return None


def _rule_matches(
    rule: CitationLocatorRule,
    *,
    context: dict[str, Any],
    locator: dict[str, Any],
) -> bool:
    match = rule.match
    source_id = str(context.get("source_id") or "")
    standard_system = str(context.get("standard_system") or "")
    source_type = str(context.get("source_type") or "")
    if match.source_ids and source_id not in set(match.source_ids):
        return False
    if match.source_id_prefixes and not any(
        source_id.startswith(prefix)
        for prefix in match.source_id_prefixes
    ):
        return False
    if match.source_types and source_type not in set(match.source_types):
        return False
    if match.standard_systems and standard_system not in set(match.standard_systems):
        return False
    locator_keys = {str(key) for key in locator}
    if match.locator_all_keys and not set(match.locator_all_keys).issubset(locator_keys):
        return False
    if match.locator_any_keys and not locator_keys.intersection(match.locator_any_keys):
        return False
    return any(
        (
            match.source_ids,
            match.source_id_prefixes,
            match.source_types,
            match.standard_systems,
            match.locator_any_keys,
            match.locator_all_keys,
        )
    )


def _has_required_context(keys: list[str], context: dict[str, Any]) -> bool:
    return all(_optional_text(context.get(key)) for key in keys)


def _render_template(template: str | None, context: dict[str, Any]) -> str | None:
    if template is None:
        return None
    fields = [field_name for _, field_name, _, _ in Formatter().parse(template) if field_name]
    if any(not _optional_text(context.get(field)) for field in fields):
        return None
    return template.format(**{field: context.get(field) for field in fields})


def _first_context_value(keys: list[str], context: dict[str, Any]) -> str | None:
    for key in keys:
        value = _optional_text(context.get(key))
        if value:
            return value
    return None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def _positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 1 else None


def _extract_regex(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    if match.groups():
        return match.group(1)
    return match.group(0)


def _canonical_resource_type(value: str) -> str:
    normalized = "".join(part for part in re.split(r"[^A-Za-z]", value) if part)
    known = {
        "patient": "Patient",
        "observation": "Observation",
        "condition": "Condition",
        "allergyintolerance": "AllergyIntolerance",
        "diagnosticreport": "DiagnosticReport",
        "documentreference": "DocumentReference",
    }
    return known.get(normalized.lower(), value)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
