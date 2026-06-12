"""Deterministic conflict detection over Graph-NER retrieval handoffs."""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import (
    GraphConflictEvidenceRef,
    GraphConflictRecord,
    GraphConflictReport,
    GraphConflictSummary,
    RetrievalPackage,
    RetrievalQuery,
)
from ojtflow.core.time import utc_now


DEFAULT_GRAPH_CONFLICT_RULES = (
    Path(__file__).resolve().parents[3]
    / "knowledge"
    / "retrieval"
    / "graph_conflict_rules.json"
)
DEFAULT_CONCEPT_REGISTRY = (
    Path(__file__).resolve().parents[3]
    / "knowledge"
    / "terminologies"
    / "medical_concepts.json"
)
DEFAULT_UCUM_UNITS = (
    Path(__file__).resolve().parents[3]
    / "knowledge"
    / "terminologies"
    / "ucum_units.json"
)
GRAPH_CONFLICT_RULES_ENV_VAR = "OJT_GRAPH_CONFLICT_RULES_PATH"
CONCEPT_REGISTRY_ENV_VAR = "OJT_MEDICAL_CONCEPT_REGISTRY_PATH"
UCUM_UNITS_ENV_VAR = "OJT_UCUM_UNITS_PATH"


@dataclass(frozen=True)
class ContradictionRule:
    """One data-driven contradiction pattern rule."""

    rule_id: str
    label: str
    severity: str
    aspect_terms: tuple[str, ...]
    positive_patterns: tuple[str, ...]
    negative_patterns: tuple[str, ...]
    message_template: str
    suggested_action: str


@dataclass(frozen=True)
class GraphConflictPolicy:
    """Loaded policy for deterministic graph conflict detection."""

    version: str
    contradiction_rules: tuple[ContradictionRule, ...]
    deprecated_mapping: dict[str, Any]
    version_mismatch: dict[str, Any]
    unit_conflict: dict[str, Any]


class GraphConflictService:
    """Attach graph/evidence conflict reports to retrieval packages."""

    def __init__(self, policy: GraphConflictPolicy | None = None) -> None:
        self.policy = policy or active_graph_conflict_policy()

    def augment_package(
        self,
        package: RetrievalPackage,
        query: RetrievalQuery,
    ) -> RetrievalPackage:
        report = self.build_report(package, query)
        handoff_context = {
            **package.handoff_context,
            "graph_conflict_report": report.model_dump(mode="json"),
        }
        if not report.conflicts:
            return package.model_copy(update={"handoff_context": handoff_context})
        warning_codes = [f"graph_conflict:{item.kind}" for item in report.conflicts]
        trace = package.trace.model_copy(
            update={
                "warnings": _unique_strings([*package.trace.warnings, *warning_codes]),
                "safety_flags": _unique_strings(
                    [*package.trace.safety_flags, "graph_conflicts_detected"]
                ),
                "fusion_diagnostics": {
                    **package.trace.fusion_diagnostics,
                    "graph_conflict_report": report.summary.model_dump(mode="json"),
                },
            }
        )
        return package.model_copy(
            update={
                "handoff_context": handoff_context,
                "trace": trace,
            }
        )

    def build_report(
        self,
        package: RetrievalPackage,
        query: RetrievalQuery,
    ) -> GraphConflictReport:
        del query
        evidence = list(package.evidence)
        graph_context = _graph_context(package)
        graph_index = _graph_index(graph_context)
        records = _dedupe_conflicts(
            [
                *_contradictory_claim_conflicts(evidence, self.policy),
                *_deprecated_mapping_conflicts(evidence, graph_index, self.policy),
                *_version_mismatch_conflicts(evidence, self.policy),
                *_unit_conflicts(evidence, graph_index, self.policy),
            ]
        )
        return GraphConflictReport(
            policy_version=self.policy.version,
            generated_at=utc_now().isoformat(),
            summary=_summary(records),
            conflicts=records,
            warnings=_report_warnings(records),
        )


@lru_cache(maxsize=4)
def load_graph_conflict_policy(path_text: str) -> GraphConflictPolicy:
    """Load graph conflict rules from trusted JSON policy data."""

    path = Path(path_text)
    if not path.exists():
        return _fallback_policy()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return _fallback_policy()
    rules = raw.get("contradiction_rules")
    contradiction_rules = tuple(
        _contradiction_rule(item)
        for item in (rules if isinstance(rules, list) else [])
        if isinstance(item, dict)
    )
    return GraphConflictPolicy(
        version=str(raw.get("version") or "graph_conflict_rules.v1"),
        contradiction_rules=contradiction_rules,
        deprecated_mapping=_dict_value(raw.get("deprecated_mapping")),
        version_mismatch=_dict_value(raw.get("version_mismatch")),
        unit_conflict=_dict_value(raw.get("unit_conflict")),
    )


def active_graph_conflict_policy() -> GraphConflictPolicy:
    """Return the active graph conflict policy."""

    return load_graph_conflict_policy(
        os.environ.get(GRAPH_CONFLICT_RULES_ENV_VAR) or str(DEFAULT_GRAPH_CONFLICT_RULES)
    )


def _fallback_policy() -> GraphConflictPolicy:
    return GraphConflictPolicy(
        version="graph_conflict_rules.fallback",
        contradiction_rules=(
            ContradictionRule(
                rule_id="required_vs_not_required",
                label="Required versus not-required guidance",
                severity="warning",
                aspect_terms=("unit", "date", "patient_id", "code", "value"),
                positive_patterns=("required", "requires", "must include"),
                negative_patterns=("not required", "does not require", "optional"),
                message_template=(
                    "Retrieved evidence contains contradictory guidance about {aspect}."
                ),
                suggested_action=(
                    "Route this evidence set to human review before applying guidance."
                ),
            ),
        ),
        deprecated_mapping={
            "severity": "warning",
            "source_version_markers": ["deprecated", "retired", "inactive"],
            "lifecycle_states": ["deprecated", "blocked", "failed"],
            "reviewer_states": ["deprecated", "blocked", "failed", "needs_review"],
            "message_template": (
                "Terminology or standard mapping evidence comes from a deprecated "
                "or review-required source."
            ),
            "suggested_action": (
                "Verify the mapping against the current official release before use."
            ),
        },
        version_mismatch={
            "severity": "warning",
            "group_locator_keys": ["standard_system", "resource"],
            "ignore_versions": ["", "unknown", "n/a"],
            "message_template": (
                "Retrieved standard guidance for {group_key} spans multiple source "
                "versions: {versions}."
            ),
            "suggested_action": (
                "Prefer the configured current source version or split the answer "
                "by source version."
            ),
        },
        unit_conflict={
            "severity": "warning",
            "message_template": (
                "Retrieved evidence links {concept} to multiple unit candidates: {units}."
            ),
            "suggested_action": (
                "Normalize units with an approved UCUM conversion path before comparison."
            ),
        },
    )


def _contradiction_rule(raw: dict[str, Any]) -> ContradictionRule:
    return ContradictionRule(
        rule_id=str(raw.get("rule_id") or "contradiction_rule"),
        label=str(raw.get("label") or raw.get("rule_id") or "Contradiction rule"),
        severity=str(raw.get("severity") or "warning"),
        aspect_terms=_string_tuple(raw.get("aspect_terms")),
        positive_patterns=_string_tuple(raw.get("positive_patterns")),
        negative_patterns=_string_tuple(raw.get("negative_patterns")),
        message_template=str(
            raw.get("message_template")
            or "Retrieved evidence contains contradictory guidance about {aspect}."
        ),
        suggested_action=str(
            raw.get("suggested_action")
            or "Route this evidence set to human review before applying guidance."
        ),
    )


def _contradictory_claim_conflicts(
    evidence: list[Evidence],
    policy: GraphConflictPolicy,
) -> list[GraphConflictRecord]:
    records: list[GraphConflictRecord] = []
    for rule in policy.contradiction_rules:
        if not rule.aspect_terms or not rule.positive_patterns or not rule.negative_patterns:
            continue
        for aspect in rule.aspect_terms:
            positive = [
                item
                for item in evidence
                if _matches_claim_side(
                    item.claim,
                    aspect=aspect,
                    include=rule.positive_patterns,
                    exclude=rule.negative_patterns,
                )
            ]
            negative = [
                item
                for item in evidence
                if _matches_claim_side(
                    item.claim,
                    aspect=aspect,
                    include=rule.negative_patterns,
                    exclude=(),
                )
            ]
            if not positive or not negative:
                continue
            records.append(
                GraphConflictRecord(
                    conflict_id=_conflict_id(
                        "contradictory_source_claim",
                        rule.rule_id,
                        aspect,
                        _evidence_ids([*positive, *negative]),
                    ),
                    kind="contradictory_source_claim",
                    severity=rule.severity,
                    rule_id=rule.rule_id,
                    message=rule.message_template.format(aspect=aspect),
                    suggested_action=rule.suggested_action,
                    evidence_refs=_evidence_refs([*positive, *negative]),
                    metadata={
                        "aspect": aspect,
                        "positive_evidence_ids": _evidence_ids(positive),
                        "negative_evidence_ids": _evidence_ids(negative),
                    },
                )
            )
    return records


def _deprecated_mapping_conflicts(
    evidence: list[Evidence],
    graph_index: dict[str, Any],
    policy: GraphConflictPolicy,
) -> list[GraphConflictRecord]:
    settings = policy.deprecated_mapping
    markers = _lower_set(settings.get("source_version_markers"))
    lifecycle_states = _lower_set(settings.get("lifecycle_states"))
    reviewer_states = _lower_set(settings.get("reviewer_states"))
    records: list[GraphConflictRecord] = []
    for item in evidence:
        source_governance = _source_governance(item)
        lifecycle_state = str(source_governance.get("lifecycle_state") or "").lower()
        reviewer_state = str(source_governance.get("reviewer_state") or "").lower()
        source_version = str(item.source_version or "").lower()
        deprecated = (
            any(marker in source_version for marker in markers)
            or lifecycle_state in lifecycle_states
            or reviewer_state in reviewer_states
        )
        candidates = graph_index["candidates_by_evidence"].get(item.evidence_id, [])
        if not deprecated or not candidates:
            continue
        records.append(
            GraphConflictRecord(
                conflict_id=_conflict_id(
                    "deprecated_terminology_mapping",
                    item.evidence_id,
                    item.source_id,
                    item.source_version or "",
                ),
                kind="deprecated_terminology_mapping",
                severity=str(settings.get("severity") or "warning"),
                rule_id="deprecated_mapping_source_state",
                message=str(
                    settings.get("message_template")
                    or "Terminology mapping evidence comes from a deprecated source."
                ),
                suggested_action=str(
                    settings.get("suggested_action")
                    or "Verify the mapping against the current official release."
                ),
                evidence_refs=_evidence_refs([item]),
                node_refs=graph_index["nodes_by_evidence"].get(item.evidence_id, []),
                edge_refs=graph_index["edges_by_evidence"].get(item.evidence_id, []),
                normalized_code_candidates=candidates,
                metadata={
                    "source_version": item.source_version,
                    "lifecycle_state": lifecycle_state or None,
                    "reviewer_state": reviewer_state or None,
                },
            )
        )
    return records


def _version_mismatch_conflicts(
    evidence: list[Evidence],
    policy: GraphConflictPolicy,
) -> list[GraphConflictRecord]:
    settings = policy.version_mismatch
    group_keys = _string_tuple(settings.get("group_locator_keys")) or (
        "standard_system",
        "resource",
    )
    ignore_versions = _lower_set(settings.get("ignore_versions"))
    grouped: dict[str, list[Evidence]] = {}
    for item in evidence:
        version = str(item.source_version or "").strip()
        if version.lower() in ignore_versions:
            continue
        for locator_key in group_keys:
            value = item.locator.get(locator_key)
            if value:
                grouped.setdefault(f"{locator_key}:{value}", []).append(item)
        grouped.setdefault(f"source_id:{item.source_id}", []).append(item)
    records: list[GraphConflictRecord] = []
    for group_key, items in grouped.items():
        versions = sorted({str(item.source_version) for item in items if item.source_version})
        if len(versions) < 2:
            continue
        records.append(
            GraphConflictRecord(
                conflict_id=_conflict_id(
                    "version_mismatched_standard_guidance",
                    group_key,
                    versions,
                    _evidence_ids(items),
                ),
                kind="version_mismatched_standard_guidance",
                severity=str(settings.get("severity") or "warning"),
                rule_id="standard_version_mismatch",
                message=str(
                    settings.get("message_template")
                    or "Retrieved guidance spans multiple source versions."
                ).format(group_key=group_key, versions=", ".join(versions)),
                suggested_action=str(
                    settings.get("suggested_action")
                    or "Prefer the configured current source version."
                ),
                evidence_refs=_evidence_refs(items),
                metadata={
                    "group_key": group_key,
                    "versions": versions,
                },
            )
        )
    return records


def _unit_conflicts(
    evidence: list[Evidence],
    graph_index: dict[str, Any],
    policy: GraphConflictPolicy,
) -> list[GraphConflictRecord]:
    settings = policy.unit_conflict
    unit_aliases = _active_unit_aliases()
    concept_aliases = _active_concept_aliases()
    preferred_units_by_code = _active_preferred_units_by_code()
    concept_units: dict[str, dict[str, list[Evidence]]] = {}
    concept_labels: dict[str, str] = {}
    for item in evidence:
        units = _units_in_text(item.claim, unit_aliases)
        if not units:
            continue
        concepts = set(graph_index["concepts_by_evidence"].get(item.evidence_id, []))
        concepts.update(_concepts_in_text(item.claim, concept_aliases))
        for concept in concepts:
            concept_labels.setdefault(concept, concept)
            for unit in units:
                concept_units.setdefault(concept, {}).setdefault(unit, []).append(item)
    records: list[GraphConflictRecord] = []
    for concept, unit_map in concept_units.items():
        units = sorted(unit_map)
        if len(units) < 2:
            continue
        items = _unique_evidence([item for values in unit_map.values() for item in values])
        preferred_units = preferred_units_by_code.get(concept, [])
        records.append(
            GraphConflictRecord(
                conflict_id=_conflict_id(
                    "conflicting_units",
                    concept,
                    units,
                    _evidence_ids(items),
                ),
                kind="conflicting_units",
                severity=str(settings.get("severity") or "warning"),
                rule_id="multiple_unit_candidates_for_concept",
                message=str(
                    settings.get("message_template")
                    or "Retrieved evidence links {concept} to multiple unit candidates: {units}."
                ).format(concept=concept_labels[concept], units=", ".join(units)),
                suggested_action=str(
                    settings.get("suggested_action")
                    or "Normalize units before merging or comparing values."
                ),
                evidence_refs=_evidence_refs(items),
                node_refs=sorted(graph_index["nodes_by_concept"].get(concept, [])),
                normalized_code_candidates=[{"code": concept}],
                metadata={
                    "concept": concept,
                    "unit_codes": units,
                    "preferred_units": preferred_units,
                    "unexpected_units": sorted(set(units).difference(preferred_units)),
                },
            )
        )
    return records


def _graph_context(package: RetrievalPackage) -> dict[str, Any]:
    graph_context = package.handoff_context.get("graph_context")
    return graph_context if isinstance(graph_context, dict) else {}


def _graph_index(graph_context: dict[str, Any]) -> dict[str, Any]:
    nodes = {
        str(node.get("id")): node
        for node in graph_context.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }
    concepts_by_evidence: dict[str, list[str]] = {}
    candidates_by_evidence: dict[str, list[dict[str, Any]]] = {}
    nodes_by_evidence: dict[str, list[str]] = {}
    nodes_by_concept: dict[str, list[str]] = {}
    edges_by_evidence: dict[str, list[str]] = {}
    for edge in graph_context.get("edges", []):
        if not isinstance(edge, dict):
            continue
        evidence_id = _edge_evidence_id(edge)
        edge_ref = _edge_ref(edge)
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        target_node = nodes.get(target, {})
        source_node = nodes.get(source, {})
        candidate_codes = [
            *_normalized_candidates(target_node),
            *_normalized_candidates(source_node),
            *_normalized_candidates(edge.get("provenance")),
        ]
        concept_codes = [candidate["code"] for candidate in candidate_codes if candidate.get("code")]
        if not evidence_id:
            continue
        if edge_ref:
            edges_by_evidence.setdefault(evidence_id, []).append(edge_ref)
        for node_id in (source, target):
            if node_id and not node_id.startswith("evidence:"):
                nodes_by_evidence.setdefault(evidence_id, []).append(node_id)
        for code in concept_codes:
            concepts_by_evidence.setdefault(evidence_id, []).append(code)
            nodes_by_concept.setdefault(code, []).extend(
                node_id for node_id in (source, target) if node_id
            )
        if candidate_codes:
            candidates_by_evidence.setdefault(evidence_id, []).extend(candidate_codes)
    return {
        "nodes": nodes,
        "concepts_by_evidence": {
            key: sorted(set(value))
            for key, value in concepts_by_evidence.items()
        },
        "candidates_by_evidence": {
            key: _dedupe_candidates(value)
            for key, value in candidates_by_evidence.items()
        },
        "nodes_by_evidence": {
            key: sorted(set(value))
            for key, value in nodes_by_evidence.items()
        },
        "nodes_by_concept": {
            key: sorted(set(value))
            for key, value in nodes_by_concept.items()
        },
        "edges_by_evidence": {
            key: sorted(set(value))
            for key, value in edges_by_evidence.items()
        },
    }


def _edge_evidence_id(edge: dict[str, Any]) -> str | None:
    if edge.get("evidence_id"):
        return str(edge["evidence_id"])
    source = str(edge.get("source") or "")
    if source.startswith("evidence:"):
        return source.removeprefix("evidence:")
    provenance = edge.get("provenance")
    if isinstance(provenance, dict) and provenance.get("source_evidence_id"):
        return str(provenance["source_evidence_id"])
    return None


def _edge_ref(edge: dict[str, Any]) -> str:
    parts = [
        str(edge.get("source") or ""),
        str(edge.get("relation") or ""),
        str(edge.get("target") or ""),
        str(edge.get("evidence_id") or ""),
    ]
    return "|".join(parts)


def _normalized_candidates(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    candidates = value.get("normalized_code_candidates")
    if not isinstance(candidates, list):
        provenance = value.get("provenance")
        if isinstance(provenance, dict):
            candidates = provenance.get("normalized_code_candidates")
    if isinstance(candidates, list):
        return [
            dict(candidate)
            for candidate in candidates
            if isinstance(candidate, dict) and candidate.get("code")
        ]
    code = value.get("normalized_code")
    if not code and value.get("type") == "standard_code":
        code = value.get("label")
    if not code:
        return []
    candidate = {"code": str(code)}
    system = value.get("normalized_system") or value.get("standard_system")
    if system:
        candidate["system"] = str(system)
    display = value.get("normalized_display") or value.get("display_name")
    if display:
        candidate["display"] = str(display)
    return [candidate]


def _source_governance(evidence: Evidence) -> dict[str, Any]:
    value = evidence.locator.get("source_governance")
    return value if isinstance(value, dict) else {}


@lru_cache(maxsize=4)
def _load_concepts(path_text: str) -> tuple[dict[str, Any], ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    concepts = raw.get("concepts") if isinstance(raw, dict) else None
    if not isinstance(concepts, list):
        return ()
    return tuple(item for item in concepts if isinstance(item, dict))


def _concept_registry_path() -> str:
    return os.environ.get(CONCEPT_REGISTRY_ENV_VAR) or str(DEFAULT_CONCEPT_REGISTRY)


@lru_cache(maxsize=4)
def _load_ucum_units(path_text: str) -> tuple[dict[str, Any], ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    units = raw.get("units") if isinstance(raw, dict) else None
    if not isinstance(units, list):
        return ()
    return tuple(item for item in units if isinstance(item, dict))


def _ucum_units_path() -> str:
    return os.environ.get(UCUM_UNITS_ENV_VAR) or str(DEFAULT_UCUM_UNITS)


def _active_concept_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for concept in _load_concepts(_concept_registry_path()):
        system = str(concept.get("standard_system") or "").strip()
        code = str(concept.get("code") or "").strip()
        if not system or not code:
            continue
        normalized_code = f"{system}:{code}"
        for alias in concept.get("aliases") or []:
            if str(alias).strip():
                aliases[str(alias).strip().lower()] = normalized_code
    return aliases


def _active_preferred_units_by_code() -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for concept in _load_concepts(_concept_registry_path()):
        system = str(concept.get("standard_system") or "").strip()
        code = str(concept.get("code") or "").strip()
        metadata = concept.get("metadata") if isinstance(concept.get("metadata"), dict) else {}
        preferred_units = metadata.get("preferred_units") if isinstance(metadata, dict) else None
        if system and code and isinstance(preferred_units, list):
            values[f"{system}:{code}"] = [
                str(unit)
                for unit in preferred_units
                if str(unit).strip()
            ]
    return values


def _active_unit_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for unit in _load_ucum_units(_ucum_units_path()):
        code = str(unit.get("code") or "").strip()
        if not code:
            continue
        aliases[code.lower()] = code
        for alias in unit.get("aliases") or []:
            if str(alias).strip():
                aliases[str(alias).strip().lower()] = code
    return aliases


def _concepts_in_text(text: str, aliases: dict[str, str]) -> list[str]:
    return sorted(
        {
            code
            for alias, code in aliases.items()
            if _contains_term(text, alias)
        }
    )


def _units_in_text(text: str, aliases: dict[str, str]) -> list[str]:
    return sorted(
        {
            code
            for alias, code in aliases.items()
            if _contains_term(text, alias)
        }
    )


def _matches_claim_side(
    text: str,
    *,
    aspect: str,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
) -> bool:
    if not _contains_term(text, aspect):
        return False
    if exclude and any(_contains_term(text, pattern) for pattern in exclude):
        return False
    return any(_contains_term(text, pattern) for pattern in include)


def _contains_term(text: str, term: str) -> bool:
    value = term.strip().lower()
    if not value:
        return False
    normalized_text = text.lower().replace("_", " ")
    normalized_value = value.replace("_", " ")
    if re.search(r"\w", normalized_value):
        pattern = r"(?<![a-z0-9])" + re.escape(normalized_value) + r"(?![a-z0-9])"
        return re.search(pattern, normalized_text) is not None
    return normalized_value in normalized_text


def _summary(records: list[GraphConflictRecord]) -> GraphConflictSummary:
    severity_counts = Counter(record.severity for record in records)
    kind_counts = Counter(record.kind for record in records)
    return GraphConflictSummary(
        conflict_count=len(records),
        requires_review_count=sum(1 for record in records if record.requires_review),
        warning_count=severity_counts.get("warning", 0),
        destructive_count=severity_counts.get("destructive", 0),
        contradictory_claim_count=kind_counts.get("contradictory_source_claim", 0),
        deprecated_mapping_count=kind_counts.get("deprecated_terminology_mapping", 0),
        conflicting_unit_count=kind_counts.get("conflicting_units", 0),
        version_mismatch_count=kind_counts.get("version_mismatched_standard_guidance", 0),
    )


def _report_warnings(records: list[GraphConflictRecord]) -> list[str]:
    return [
        f"{record.kind}:{record.conflict_id}"
        for record in records
        if record.requires_review
    ][:20]


def _evidence_refs(items: list[Evidence]) -> list[GraphConflictEvidenceRef]:
    return [
        GraphConflictEvidenceRef(
            evidence_id=item.evidence_id,
            source_id=item.source_id,
            source_type=item.source_type,
            source_version=item.source_version,
            claim=item.claim,
            source_locator=dict(item.locator),
        )
        for item in _unique_evidence(items)
    ]


def _evidence_ids(items: list[Evidence]) -> list[str]:
    return [item.evidence_id for item in _unique_evidence(items)]


def _unique_evidence(items: list[Evidence]) -> list[Evidence]:
    seen: set[str] = set()
    result: list[Evidence] = []
    for item in items:
        if item.evidence_id in seen:
            continue
        result.append(item)
        seen.add(item.evidence_id)
    return result


def _dedupe_conflicts(records: list[GraphConflictRecord]) -> list[GraphConflictRecord]:
    deduped: dict[str, GraphConflictRecord] = {}
    for record in records:
        deduped.setdefault(record.conflict_id, record)
    return sorted(deduped.values(), key=lambda item: (item.kind, item.conflict_id))


def _dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        code = str(candidate.get("code") or "").strip()
        if code:
            deduped.setdefault(code, candidate)
    return list(deduped.values())


def _conflict_id(*parts: Any) -> str:
    encoded = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return "gconf_" + sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _dict_value(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _lower_set(value: Any) -> set[str]:
    return {item.lower() for item in _string_tuple(value)}


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result
