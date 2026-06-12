"""Evidence-only retrieval answer synthesis and guardrails."""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import (
    RetrievalAnswer,
    RetrievalAnswerCitation,
    RetrievalAnswerClaim,
    RetrievalAnswerFreshnessWarning,
    RetrievalEvidenceSupportRow,
    RetrievalPackage,
    RetrievalQuery,
)


DEFAULT_ANSWER_POLICY = (
    Path(__file__).resolve().parents[3]
    / "knowledge"
    / "retrieval"
    / "answer_synthesis_policy.json"
)
ANSWER_POLICY_ENV_VAR = "OJT_RETRIEVAL_ANSWER_POLICY_PATH"


@dataclass(frozen=True)
class AnswerPolicy:
    """Data-driven policy for evidence-only answer synthesis."""

    version: str
    supported_statuses: tuple[str, ...]
    review_statuses: tuple[str, ...]
    stale_version_markers: tuple[str, ...]
    stale_lifecycle_states: tuple[str, ...]
    graph_guard_enabled: bool
    graph_guard_required_statuses: tuple[str, ...]
    graph_guard_clinical_assertion_terms: tuple[str, ...]
    graph_guard_warning_id: str
    refusal_messages: dict[str, str]


class RetrievalAnswerSynthesizer:
    """Attach a guarded, citation-backed answer to retrieval packages."""

    def __init__(self, policy: AnswerPolicy | None = None) -> None:
        self.policy = policy or active_answer_policy()

    def augment_package(
        self,
        package: RetrievalPackage,
        query: RetrievalQuery,
    ) -> RetrievalPackage:
        answer = build_retrieval_answer(package, query, policy=self.policy)
        handoff_context = {
            **package.handoff_context,
            "answer": answer.model_dump(mode="json"),
        }
        trace = package.trace
        if answer.status == "refused":
            trace = trace.model_copy(
                update={
                    "safety_flags": [
                        *trace.safety_flags,
                        "retrieval_answer_refused_unsupported",
                    ],
                    "warnings": [
                        *trace.warnings,
                        answer.refusal_reason or "retrieval_answer_refused",
                    ],
                }
            )
        elif answer.freshness_warnings:
            trace = trace.model_copy(
                update={
                    "warnings": [
                        *trace.warnings,
                        *[
                            warning.warning_id
                            for warning in answer.freshness_warnings
                        ],
                    ]
                }
            )
        return package.model_copy(
            update={
                "answer": answer,
                "handoff_context": handoff_context,
                "trace": trace,
            }
        )


def build_retrieval_answer(
    package: RetrievalPackage,
    query: RetrievalQuery,
    *,
    policy: AnswerPolicy | None = None,
) -> RetrievalAnswer:
    """Build an answer that cannot exceed cited retrieval support."""

    active_policy = policy or active_answer_policy()
    support_matrix = package.support_matrix
    rows = list(support_matrix.rows if support_matrix else [])
    evidence_by_id = {item.evidence_id: item for item in package.evidence}
    graph_context = _graph_context(package)
    graph_conflict_report = _graph_conflict_report(package)
    graph_conflict_summary = _graph_conflict_summary(graph_conflict_report)
    supported_rows = [
        row
        for row in rows
        if row.support_status in set(active_policy.supported_statuses)
    ]
    unsupported_rows = [
        row
        for row in rows
        if row.support_status not in set(active_policy.supported_statuses)
    ]
    citations = _citations_from_rows(supported_rows, evidence_by_id)
    claims = [
        _claim_from_row(
            row,
            citations=citations,
            graph_context=graph_context,
            policy=active_policy,
        )
        for row in supported_rows
    ]
    unsupported_claims = [
        _claim_from_row(
            row,
            citations=[],
            graph_context=graph_context,
            policy=active_policy,
        )
        for row in unsupported_rows
    ]
    freshness_warnings = _freshness_warnings(
        evidence_by_id=evidence_by_id,
        query=query,
        policy=active_policy,
    )
    gaps = _missing_evidence_gaps(
        rows=rows,
        supported_rows=supported_rows,
        unsupported_rows=unsupported_rows,
        package=package,
    )
    if graph_conflict_summary["requires_review_count"]:
        gaps = _unique([*gaps, *_graph_conflict_gaps(graph_conflict_report)])

    status = _answer_status(
        rows=rows,
        supported_rows=supported_rows,
        unsupported_rows=unsupported_rows,
        freshness_warnings=freshness_warnings,
    )
    graph_guard_summary = _claim_triple_guard_summary(claims, unsupported_claims)
    if graph_guard_summary["review_required_count"] and status == "supported":
        status = "review_required"
    if graph_conflict_summary["requires_review_count"] and status == "supported":
        status = "review_required"
    if graph_guard_summary["review_required_count"]:
        gaps = _unique(
            [
                *gaps,
                (
                    "Graph claim guard flagged "
                    f"{graph_guard_summary['review_required_count']} clinical "
                    "claim(s) without graph triple support."
                ),
            ]
        )
    refusal_reason = _refusal_reason(status, active_policy, rows=rows, gaps=gaps)
    confidence = _answer_confidence(
        supported_rows=supported_rows,
        unsupported_rows=unsupported_rows,
        freshness_warnings=freshness_warnings,
        graph_guard_review_count=int(graph_guard_summary["review_required_count"]),
        graph_conflict_review_count=int(graph_conflict_summary["requires_review_count"]),
    )
    return RetrievalAnswer(
        status=status,
        answer_text=_answer_text(
            status=status,
            query=query,
            claims=claims,
            citations=citations,
            gaps=gaps,
            refusal_reason=refusal_reason,
        ),
        refusal_reason=refusal_reason,
        requires_human_review=(
            status != "supported"
            or bool(freshness_warnings)
            or bool(graph_guard_summary["review_required_count"])
            or bool(graph_conflict_summary["requires_review_count"])
            or any(row.support_status in active_policy.review_statuses for row in rows)
        ),
        confidence=confidence,
        claims=claims,
        citations=citations,
        unsupported_claims=unsupported_claims,
        missing_evidence_gaps=gaps,
        freshness_warnings=freshness_warnings,
        graph_path_summary=_graph_path_summary(graph_context, claims),
        metadata={
            "policy_version": active_policy.version,
            "support_row_count": len(rows),
            "supported_row_count": len(supported_rows),
            "unsupported_row_count": len(unsupported_rows),
            "claim_triple_guard": graph_guard_summary,
            "graph_conflict_summary": graph_conflict_summary,
            "query": query.query,
        },
    )


@lru_cache(maxsize=4)
def load_answer_policy(path_text: str) -> AnswerPolicy:
    """Load the retrieval answer policy from trusted JSON data."""

    path = Path(path_text)
    if not path.exists():
        return _fallback_policy()
    raw = json.loads(path.read_text(encoding="utf-8"))
    synthesis = raw.get("synthesis") if isinstance(raw, dict) else {}
    freshness = raw.get("freshness") if isinstance(raw, dict) else {}
    claim_guard = raw.get("claim_triple_guard") if isinstance(raw, dict) else {}
    claim_guard = claim_guard if isinstance(claim_guard, dict) else {}
    return AnswerPolicy(
        version=str(raw.get("version") or "retrieval_answer_synthesis_policy.v1"),
        supported_statuses=_string_tuple(
            synthesis.get("supported_statuses"),
            default=("strong", "partial"),
        ),
        review_statuses=_string_tuple(
            synthesis.get("review_statuses"),
            default=("partial", "weak", "unsupported"),
        ),
        stale_version_markers=_string_tuple(
            freshness.get("stale_version_markers"),
            default=("deprecated", "stale", "old", "outdated"),
        ),
        stale_lifecycle_states=_string_tuple(
            freshness.get("stale_lifecycle_states"),
            default=("deprecated", "blocked", "failed", "needs_review"),
        ),
        graph_guard_enabled=_bool_value(claim_guard.get("enabled"), default=True),
        graph_guard_required_statuses=_string_tuple(
            claim_guard.get("required_for_support_statuses"),
            default=("strong",),
        ),
        graph_guard_clinical_assertion_terms=_string_tuple(
            claim_guard.get("clinical_assertion_terms"),
            default=(
                "patient",
                "diagnosis",
                "medication",
                "lab",
                "observation",
                "unit",
                "loinc",
                "rxnorm",
                "fhir",
            ),
        ),
        graph_guard_warning_id=str(
            claim_guard.get("warning_id") or "claim_without_graph_triple_support"
        ),
        refusal_messages={
            str(key): str(value)
            for key, value in dict(raw.get("refusal_messages") or {}).items()
            if str(key).strip() and str(value).strip()
        },
    )


def active_answer_policy() -> AnswerPolicy:
    """Return the configured answer policy with environment override support."""

    return load_answer_policy(
        os.environ.get(ANSWER_POLICY_ENV_VAR) or str(DEFAULT_ANSWER_POLICY)
    )


def _fallback_policy() -> AnswerPolicy:
    return AnswerPolicy(
        version="retrieval_answer_synthesis_policy.fallback",
        supported_statuses=("strong", "partial"),
        review_statuses=("partial", "weak", "unsupported"),
        stale_version_markers=("deprecated", "stale", "old", "outdated"),
        stale_lifecycle_states=("deprecated", "blocked", "failed", "needs_review"),
        graph_guard_enabled=True,
        graph_guard_required_statuses=("strong",),
        graph_guard_clinical_assertion_terms=(
            "patient",
            "diagnosis",
            "medication",
            "lab",
            "observation",
            "unit",
            "loinc",
            "rxnorm",
            "fhir",
        ),
        graph_guard_warning_id="claim_without_graph_triple_support",
        refusal_messages={},
    )


def _citations_from_rows(
    rows: list[RetrievalEvidenceSupportRow],
    evidence_by_id: dict[str, Evidence],
) -> list[RetrievalAnswerCitation]:
    by_evidence_id: dict[str, RetrievalAnswerCitation] = {}
    for row in rows:
        evidence = evidence_by_id.get(row.evidence_id)
        if evidence is None:
            continue
        existing = by_evidence_id.get(row.evidence_id)
        claim_ids = (
            [*existing.supported_claim_ids, row.claim_id]
            if existing is not None
            else [row.claim_id]
        )
        by_evidence_id[row.evidence_id] = RetrievalAnswerCitation(
            citation_id=(
                existing.citation_id
                if existing is not None
                else f"cite:{len(by_evidence_id) + 1}"
            ),
            evidence_id=evidence.evidence_id,
            source_id=evidence.source_id,
            source_type=evidence.source_type,
            source_version=_optional_str(evidence.source_version),
            source_locator={**evidence.locator, **row.source_locator},
            supported_claim_ids=_unique(claim_ids),
        )
    return list(by_evidence_id.values())


def _claim_from_row(
    row: RetrievalEvidenceSupportRow,
    *,
    citations: list[RetrievalAnswerCitation],
    graph_context: dict[str, Any],
    policy: AnswerPolicy,
) -> RetrievalAnswerClaim:
    citation_ids = [
        citation.citation_id
        for citation in citations
        if citation.evidence_id == row.evidence_id
    ]
    graph_path_refs = _graph_refs_for_evidence(graph_context, row.evidence_id)
    graph_guard = _claim_graph_guard(
        row,
        graph_path_refs=graph_path_refs,
        policy=policy,
    )
    warnings = list(row.warnings)
    if graph_guard["status"] == "review_required":
        warnings.append(policy.graph_guard_warning_id)
    return RetrievalAnswerClaim(
        claim_id=row.claim_id,
        text=row.claim,
        support_status=row.support_status,
        evidence_ids=[row.evidence_id],
        citation_ids=citation_ids,
        graph_path_refs=graph_path_refs,
        graph_guard=graph_guard,
        warnings=_unique(warnings),
    )


def _freshness_warnings(
    *,
    evidence_by_id: dict[str, Evidence],
    query: RetrievalQuery,
    policy: AnswerPolicy,
) -> list[RetrievalAnswerFreshnessWarning]:
    warnings: list[RetrievalAnswerFreshnessWarning] = []
    requested_version = _optional_str(query.filters.get("source_version"))
    for evidence in evidence_by_id.values():
        source_version = evidence.source_version or ""
        source_version_lower = source_version.casefold()
        stale_marker = next(
            (
                marker
                for marker in policy.stale_version_markers
                if marker.casefold() in source_version_lower
            ),
            None,
        )
        if stale_marker:
            warnings.append(
                RetrievalAnswerFreshnessWarning(
                    warning_id=f"source_version_{stale_marker}",
                    severity="warning",
                    evidence_id=evidence.evidence_id,
                    source_id=evidence.source_id,
                    source_version=_optional_str(evidence.source_version),
                    message=(
                        f"Evidence source {evidence.source_id} has version marker "
                        f"{stale_marker!r}."
                    ),
                    suggested_action=(
                        "Refresh the source inventory or select a newer approved "
                        "source before relying on this answer."
                    ),
                    metadata={"marker": stale_marker},
                )
            )
        lifecycle_state = _locator_state(evidence.locator)
        if lifecycle_state and lifecycle_state in set(policy.stale_lifecycle_states):
            warnings.append(
                RetrievalAnswerFreshnessWarning(
                    warning_id=f"source_lifecycle_{lifecycle_state}",
                    severity=(
                        "error" if lifecycle_state in {"blocked", "failed"} else "warning"
                    ),
                    evidence_id=evidence.evidence_id,
                    source_id=evidence.source_id,
                    source_version=_optional_str(evidence.source_version),
                    message=(
                        f"Evidence source {evidence.source_id} has lifecycle state "
                        f"{lifecycle_state}."
                    ),
                    suggested_action=(
                        "Use an approved, current source or send the source for "
                        "data-steward review."
                    ),
                    metadata={"lifecycle_state": lifecycle_state},
                )
            )
        if (
            requested_version
            and evidence.source_version
            and evidence.source_version != requested_version
        ):
            warnings.append(
                RetrievalAnswerFreshnessWarning(
                    warning_id="source_version_mismatch",
                    severity="warning",
                    evidence_id=evidence.evidence_id,
                    source_id=evidence.source_id,
                    source_version=_optional_str(evidence.source_version),
                    message=(
                        f"Evidence source {evidence.source_id} returned version "
                        f"{evidence.source_version}, not requested version {requested_version}."
                    ),
                    suggested_action=(
                        "Review the source version filter and re-run retrieval against the required release."
                    ),
                    metadata={"requested_source_version": requested_version},
                )
            )
        if evidence.trust_level != TrustLevel.APPROVED:
            warnings.append(
                RetrievalAnswerFreshnessWarning(
                    warning_id="source_not_approved",
                    severity="warning",
                    evidence_id=evidence.evidence_id,
                    source_id=evidence.source_id,
                    source_version=_optional_str(evidence.source_version),
                    message=f"Evidence source {evidence.source_id} is not approved.",
                    suggested_action=(
                        "Use approved evidence or keep the answer gated for human review."
                    ),
                    metadata={"trust_level": str(evidence.trust_level)},
                )
            )
    return _dedupe_warnings(warnings)


def _missing_evidence_gaps(
    *,
    rows: list[RetrievalEvidenceSupportRow],
    supported_rows: list[RetrievalEvidenceSupportRow],
    unsupported_rows: list[RetrievalEvidenceSupportRow],
    package: RetrievalPackage,
) -> list[str]:
    gaps: list[str] = []
    if not rows:
        gaps.append("No ranked evidence rows were available for answer synthesis.")
    if rows and not supported_rows:
        gaps.append("No claim reached strong or partial evidence support.")
    if unsupported_rows:
        gaps.append(
            f"{len(unsupported_rows)} evidence row(s) had weak or unsupported support."
        )
    if package.evidence_buckets:
        missing_required = [
            bucket.label
            for bucket in package.evidence_buckets
            if bucket.required and bucket.hit_count <= 0
        ]
        for label in missing_required:
            gaps.append(f"Required evidence bucket is missing: {label}.")
    if package.trace.warnings:
        gaps.append("Retrieval trace contains warnings that require operator review.")
    return _unique(gaps)


def _answer_status(
    *,
    rows: list[RetrievalEvidenceSupportRow],
    supported_rows: list[RetrievalEvidenceSupportRow],
    unsupported_rows: list[RetrievalEvidenceSupportRow],
    freshness_warnings: list[RetrievalAnswerFreshnessWarning],
) -> str:
    if not rows or not supported_rows:
        return "refused"
    if any(warning.severity == "error" for warning in freshness_warnings):
        return "review_required"
    if unsupported_rows or freshness_warnings:
        return "partial"
    if all(row.support_status == "strong" for row in supported_rows):
        return "supported"
    return "partial"


def _refusal_reason(
    status: str,
    policy: AnswerPolicy,
    *,
    rows: list[RetrievalEvidenceSupportRow],
    gaps: list[str],
) -> str | None:
    if status != "refused":
        return None
    if not rows:
        return policy.refusal_messages.get(
            "no_evidence",
            "No retrieved evidence was available to support an answer.",
        )
    return policy.refusal_messages.get(
        "unsupported",
        gaps[0] if gaps else "Retrieved evidence did not support an answer.",
    )


def _answer_confidence(
    *,
    supported_rows: list[RetrievalEvidenceSupportRow],
    unsupported_rows: list[RetrievalEvidenceSupportRow],
    freshness_warnings: list[RetrievalAnswerFreshnessWarning],
    graph_guard_review_count: int = 0,
    graph_conflict_review_count: int = 0,
) -> float:
    if not supported_rows:
        return 0.0
    base = sum(_row_confidence(row) for row in supported_rows) / len(supported_rows)
    penalty = (
        0.08 * len(unsupported_rows)
        + 0.05 * len(freshness_warnings)
        + 0.06 * graph_guard_review_count
        + 0.07 * graph_conflict_review_count
    )
    return round(max(0.0, min(1.0, base - penalty)), 3)


def _row_confidence(row: RetrievalEvidenceSupportRow) -> float:
    if row.confidence is not None:
        return max(0.0, min(1.0, row.confidence))
    if row.support_status == "strong":
        return 0.86
    if row.support_status == "partial":
        return 0.68
    return 0.32


def _answer_text(
    *,
    status: str,
    query: RetrievalQuery,
    claims: list[RetrievalAnswerClaim],
    citations: list[RetrievalAnswerCitation],
    gaps: list[str],
    refusal_reason: str | None,
) -> str:
    if status == "refused":
        return (
            "I cannot answer this from the retrieved evidence. "
            f"{refusal_reason or 'The evidence support was insufficient.'}"
        )
    claim_text = "; ".join(claim.text for claim in claims[:3])
    citation_refs = ", ".join(citation.evidence_id for citation in citations[:5])
    prefix = (
        "The retrieved evidence supports the following operational finding"
        if len(claims) == 1
        else "The retrieved evidence supports the following operational findings"
    )
    answer = f"{prefix}: {claim_text}. Citations: {citation_refs}."
    if status != "supported" and gaps:
        answer = f"{answer} Review required: {gaps[0]}"
    if query.workflow_id:
        answer = f"{answer} Workflow: {query.workflow_id}."
    return answer


def _graph_context(package: RetrievalPackage) -> dict[str, Any]:
    value = package.handoff_context.get("graph_context")
    return value if isinstance(value, dict) else {}


def _graph_conflict_report(package: RetrievalPackage) -> dict[str, Any]:
    value = package.handoff_context.get("graph_conflict_report")
    return value if isinstance(value, dict) else {}


def _graph_conflict_summary(report: dict[str, Any]) -> dict[str, int]:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return {
            "conflict_count": 0,
            "requires_review_count": 0,
        }
    return {
        "conflict_count": _int_value(summary.get("conflict_count")),
        "requires_review_count": _int_value(summary.get("requires_review_count")),
        "warning_count": _int_value(summary.get("warning_count")),
        "destructive_count": _int_value(summary.get("destructive_count")),
    }


def _graph_conflict_gaps(report: dict[str, Any]) -> list[str]:
    conflicts = report.get("conflicts")
    if not isinstance(conflicts, list):
        return []
    gaps: list[str] = []
    for conflict in conflicts[:3]:
        if not isinstance(conflict, dict):
            continue
        message = _optional_str(conflict.get("message"))
        if message:
            gaps.append(f"Graph conflict requires review: {message}")
    if len(conflicts) > 3:
        gaps.append(f"{len(conflicts) - 3} additional graph conflict(s) require review.")
    return gaps


def _graph_refs_for_evidence(graph_context: dict[str, Any], evidence_id: str) -> list[str]:
    refs: list[str] = []
    for edge in graph_context.get("edges") or []:
        if isinstance(edge, dict) and edge.get("evidence_id") == evidence_id:
            refs.append(
                f"{edge.get('source')}:{edge.get('relation')}:{edge.get('target')}"
            )
    for triple in graph_context.get("triples") or []:
        if isinstance(triple, dict) and triple.get("evidence_id") == evidence_id:
            refs.append(
                f"{triple.get('subject')} / {triple.get('predicate')} / {triple.get('object')}"
            )
    return _unique(ref for ref in refs if ref and "None" not in ref)[:8]


def _claim_graph_guard(
    row: RetrievalEvidenceSupportRow,
    *,
    graph_path_refs: list[str],
    policy: AnswerPolicy,
) -> dict[str, Any]:
    requires_graph = (
        policy.graph_guard_enabled
        and row.support_status in set(policy.graph_guard_required_statuses)
        and _looks_like_clinical_assertion(
            row.claim,
            policy.graph_guard_clinical_assertion_terms,
        )
    )
    status = "not_required"
    if requires_graph and graph_path_refs:
        status = "supported"
    elif requires_graph:
        status = "review_required"
    return {
        "contract": "claim_triple_guard.v0",
        "enabled": policy.graph_guard_enabled,
        "status": status,
        "requires_graph_support": requires_graph,
        "graph_path_ref_count": len(graph_path_refs),
        "warning_id": policy.graph_guard_warning_id if status == "review_required" else None,
        "required_for_support_statuses": list(policy.graph_guard_required_statuses),
    }


def _claim_triple_guard_summary(
    claims: list[RetrievalAnswerClaim],
    unsupported_claims: list[RetrievalAnswerClaim],
) -> dict[str, Any]:
    all_claims = [*claims, *unsupported_claims]
    status_counts = Counter(
        str(claim.graph_guard.get("status") or "unknown")
        for claim in all_claims
    )
    return {
        "contract": "claim_triple_guard_summary.v0",
        "claim_count": len(all_claims),
        "supported_count": status_counts.get("supported", 0),
        "review_required_count": status_counts.get("review_required", 0),
        "not_required_count": status_counts.get("not_required", 0),
        "unknown_count": status_counts.get("unknown", 0),
    }


def _looks_like_clinical_assertion(
    text: str,
    clinical_terms: tuple[str, ...],
) -> bool:
    normalized = text.casefold()
    return any(term.casefold() in normalized for term in clinical_terms)


def _graph_path_summary(
    graph_context: dict[str, Any],
    claims: list[RetrievalAnswerClaim],
) -> dict[str, Any]:
    summary = graph_context.get("summary") if isinstance(graph_context, dict) else None
    graph_ref_count = sum(len(claim.graph_path_refs) for claim in claims)
    return {
        "graph_contract": graph_context.get("graph_contract"),
        "node_count": (
            int(summary.get("node_count", 0)) if isinstance(summary, dict) else 0
        ),
        "edge_count": (
            int(summary.get("edge_count", 0)) if isinstance(summary, dict) else 0
        ),
        "triple_count": (
            int(summary.get("triple_count", 0)) if isinstance(summary, dict) else 0
        ),
        "claim_graph_ref_count": graph_ref_count,
        "graph_supported": graph_ref_count > 0,
    }


def _locator_state(locator: dict[str, Any]) -> str | None:
    for key in ("lifecycle_state", "reviewer_state", "source_lifecycle_state"):
        value = _optional_str(locator.get(key))
        if value:
            return value.casefold()
    metadata = locator.get("metadata")
    if isinstance(metadata, dict):
        return _locator_state(metadata)
    return None


def _optional_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _int_value(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def _string_tuple(value: Any, *, default: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, list):
        return default
    values = tuple(str(item).strip() for item in value if str(item).strip())
    return values or default


def _bool_value(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _unique(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _dedupe_warnings(
    warnings: list[RetrievalAnswerFreshnessWarning],
) -> list[RetrievalAnswerFreshnessWarning]:
    seen: set[tuple[str, str | None, str | None]] = set()
    deduped: list[RetrievalAnswerFreshnessWarning] = []
    for warning in warnings:
        key = (warning.warning_id, warning.evidence_id, warning.source_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(warning)
    return deduped
