"""Source-governance checks for selected retrieval evidence."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from ojtflow.core.contracts.enums import EvidenceSourceType
from ojtflow.core.contracts.retrieval import RetrievalHit
from ojtflow.infrastructure.retrieval.catalogs import (
    load_corpus_adapter_catalog,
    load_source_trust_policy_catalog,
)


DEFAULT_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[4] / "knowledge"
GOVERNED_SOURCE_TYPES = {
    EvidenceSourceType.HEALTHCARE_STANDARD.value,
    EvidenceSourceType.TERMINOLOGY_SYSTEM.value,
}


@dataclass(frozen=True)
class SourceGovernanceDecision:
    """Source-governance decision attached to selected retrieval evidence."""

    source_id: str
    status: str
    severity: str
    evidence_ids: tuple[str, ...]
    policy_source_id: str | None = None
    adapter_id: str | None = None
    authority: str | None = None
    evidence_tier: str | None = None
    requires_reviewer_approval: bool = False
    reviewer_state: str | None = None
    lifecycle_state: str | None = None
    refresh_cadence: str | None = None
    license_constraints: tuple[str, ...] = ()
    intended_use: tuple[str, ...] = ()
    prohibited_use: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()
    recommended_actions: tuple[str, ...] = ()

    def as_payload(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "severity": self.severity,
            "evidence_ids": list(self.evidence_ids),
            "policy_source_id": self.policy_source_id,
            "adapter_id": self.adapter_id,
            "authority": self.authority,
            "evidence_tier": self.evidence_tier,
            "requires_reviewer_approval": self.requires_reviewer_approval,
            "reviewer_state": self.reviewer_state,
            "lifecycle_state": self.lifecycle_state,
            "refresh_cadence": self.refresh_cadence,
            "license_constraints": list(self.license_constraints),
            "intended_use": list(self.intended_use),
            "prohibited_use": list(self.prohibited_use),
            "issues": list(self.issues),
            "recommended_actions": list(self.recommended_actions),
        }


@dataclass(frozen=True)
class SourceGovernanceIndex:
    """Loaded source governance catalogs keyed for package-time checks."""

    catalog_version: str
    adapter_catalog_version: str
    policies_by_source_id: dict[str, Any]
    policies_by_standard: dict[str, tuple[Any, ...]]
    policies_by_standard_domain: dict[tuple[str, str], tuple[Any, ...]]
    adapters_by_source_id: dict[str, Any]


def source_governance_decisions_from_hits(
    hits: list[RetrievalHit],
    *,
    knowledge_root: Path | str | None = None,
) -> dict[str, SourceGovernanceDecision]:
    """Evaluate selected evidence against source trust and adapter catalogs."""

    if not hits:
        return {}
    index = active_source_governance_index(knowledge_root=knowledge_root)
    hits_by_source: dict[str, list[RetrievalHit]] = {}
    for hit in hits:
        hits_by_source.setdefault(hit.evidence.source_id, []).append(hit)
    return {
        source_id: _source_governance_decision(source_hits, index=index)
        for source_id, source_hits in hits_by_source.items()
    }


def attach_source_governance(
    hits: list[RetrievalHit],
    decisions: dict[str, SourceGovernanceDecision],
) -> None:
    """Attach source-governance payloads to hit and evidence locators."""

    for hit in hits:
        decision = decisions.get(hit.evidence.source_id)
        if decision is None:
            continue
        payload = decision.as_payload()
        hit.source_locator = {
            **hit.source_locator,
            "source_governance": payload,
        }
        hit.evidence.locator = {
            **hit.evidence.locator,
            "source_governance": payload,
        }


def source_governance_summary(
    decisions: dict[str, SourceGovernanceDecision],
) -> dict[str, Any]:
    """Summarize source governance for assistant, UI, and audit handoff."""

    severity_counts = Counter(decision.severity for decision in decisions.values())
    status_counts = Counter(decision.status for decision in decisions.values())
    highest = _highest_source_governance_severity(decisions.values())
    return {
        "version": "source_governance_summary.v1",
        "status": _source_governance_package_status(decisions.values()),
        "source_count": len(decisions),
        "severity": highest,
        "severity_counts": dict(sorted(severity_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "review_required_count": sum(
            1 for decision in decisions.values() if decision.requires_reviewer_approval
        ),
        "missing_policy_count": sum(
            1
            for decision in decisions.values()
            if "missing_source_trust_policy" in decision.issues
        ),
        "decisions": [
            decision.as_payload()
            for decision in sorted(decisions.values(), key=lambda item: item.source_id)
        ],
    }


def source_governance_trace_warnings(
    decisions: dict[str, SourceGovernanceDecision],
) -> list[str]:
    """Return compact trace warnings for source-governance issues."""

    warnings: list[str] = []
    for decision in sorted(decisions.values(), key=lambda item: item.source_id):
        if decision.severity == "success":
            continue
        issue_text = ", ".join(decision.issues[:4]) if decision.issues else decision.status
        warnings.append(f"Source governance for {decision.source_id}: {issue_text}.")
    return warnings


def active_source_governance_index(
    *,
    knowledge_root: Path | str | None = None,
) -> SourceGovernanceIndex:
    """Load source governance catalogs from the configured knowledge root."""

    root = Path(knowledge_root) if knowledge_root is not None else DEFAULT_KNOWLEDGE_ROOT
    return _load_source_governance_index(str(root))


@lru_cache(maxsize=4)
def _load_source_governance_index(path_text: str) -> SourceGovernanceIndex:
    root = Path(path_text)
    policy_catalog = load_source_trust_policy_catalog(root)
    adapter_catalog = load_corpus_adapter_catalog(root)
    policies_by_source_id = {
        policy.source_id: policy
        for policy in policy_catalog.policies
    }
    policies_by_standard: dict[str, list[Any]] = {}
    policies_by_standard_domain: dict[tuple[str, str], list[Any]] = {}
    for policy in policy_catalog.policies:
        standard = policy.standard_system.strip().lower()
        domain = policy.domain.strip().lower()
        if standard:
            policies_by_standard.setdefault(standard, []).append(policy)
        if standard and domain:
            policies_by_standard_domain.setdefault((standard, domain), []).append(policy)
    return SourceGovernanceIndex(
        catalog_version=policy_catalog.version,
        adapter_catalog_version=adapter_catalog.version,
        policies_by_source_id=policies_by_source_id,
        policies_by_standard={
            key: tuple(value)
            for key, value in policies_by_standard.items()
        },
        policies_by_standard_domain={
            key: tuple(value)
            for key, value in policies_by_standard_domain.items()
        },
        adapters_by_source_id={
            adapter.source_id: adapter
            for adapter in adapter_catalog.adapters
        },
    )


def _source_governance_decision(
    hits: list[RetrievalHit],
    *,
    index: SourceGovernanceIndex,
) -> SourceGovernanceDecision:
    first = hits[0]
    adapter = _source_adapter_for_hit(first, index)
    policy = _source_policy_for_hit(first, index, adapter=adapter)
    issues: list[str] = []
    actions: list[str] = []
    lifecycle_state = _source_lifecycle_state(first, adapter=adapter)
    reviewer_state = _source_reviewer_state(first, adapter=adapter)

    if adapter is not None and not bool(adapter.enabled):
        issues.append("adapter_disabled")
        actions.append("Enable or replace the source adapter before relying on this evidence.")
    if lifecycle_state in {"blocked", "failed"}:
        issues.append(f"lifecycle_{lifecycle_state}")
        actions.append("Remove blocked or failed sources from retrieval until governance clears them.")
    elif lifecycle_state in {"candidate", "needs_review"}:
        issues.append(f"lifecycle_{lifecycle_state}")
        actions.append("Approve the source lifecycle state before production use.")
    elif lifecycle_state == "deprecated":
        issues.append("lifecycle_deprecated")
        actions.append("Refresh or replace deprecated source evidence.")
    if reviewer_state and reviewer_state != "approved":
        issues.append(f"reviewer_state_{reviewer_state}")
        actions.append("Route the source through reviewer approval.")
    if policy is None and _source_requires_trust_policy(first):
        issues.append("missing_source_trust_policy")
        actions.append("Add a source trust policy with authority, license, and intended-use boundaries.")
    if policy is not None and policy.requires_reviewer_approval:
        issues.append("review_required_by_source_policy")
        actions.append("Keep downstream use review-gated for this source.")

    severity = _source_governance_severity(issues)
    return SourceGovernanceDecision(
        source_id=first.evidence.source_id,
        status=_source_governance_status(severity, issues),
        severity=severity,
        evidence_ids=tuple(hit.evidence.evidence_id for hit in hits),
        policy_source_id=policy.source_id if policy else None,
        adapter_id=adapter.adapter_id if adapter else None,
        authority=policy.authority if policy else _source_metadata_text(first, "authority"),
        evidence_tier=policy.evidence_tier if policy else None,
        requires_reviewer_approval=bool(policy.requires_reviewer_approval) if policy else False,
        reviewer_state=reviewer_state,
        lifecycle_state=lifecycle_state,
        refresh_cadence=policy.refresh_cadence if policy else _source_metadata_text(first, "refresh_cadence"),
        license_constraints=tuple(policy.license_constraints) if policy else (),
        intended_use=tuple(policy.intended_use) if policy else (),
        prohibited_use=tuple(policy.prohibited_use) if policy else (),
        issues=tuple(_unique_strings(issues)),
        recommended_actions=tuple(_unique_strings(actions)),
    )


def _source_adapter_for_hit(
    hit: RetrievalHit,
    index: SourceGovernanceIndex,
) -> Any | None:
    for key in _source_governance_lookup_keys(hit):
        adapter = index.adapters_by_source_id.get(key)
        if adapter is not None:
            return adapter
    return None


def _source_policy_for_hit(
    hit: RetrievalHit,
    index: SourceGovernanceIndex,
    *,
    adapter: Any | None,
) -> Any | None:
    for key in _source_governance_lookup_keys(hit):
        policy = index.policies_by_source_id.get(key)
        if policy is not None:
            return policy
    if adapter is not None:
        trust_policy_source_id = _adapter_metadata_text(adapter, "trust_policy_source_id")
        if trust_policy_source_id:
            policy = index.policies_by_source_id.get(trust_policy_source_id)
            if policy is not None:
                return policy
        policy = index.policies_by_source_id.get(adapter.source_id)
        if policy is not None:
            return policy

    standard = _source_standard_system(hit).lower()
    domain = _source_clinical_domain(hit).lower()
    if standard and domain:
        candidates = index.policies_by_standard_domain.get((standard, domain), ())
        if candidates:
            return candidates[0]
    if standard:
        candidates = index.policies_by_standard.get(standard, ())
        if len(candidates) == 1:
            return candidates[0]
    return None


def _source_governance_lookup_keys(hit: RetrievalHit) -> list[str]:
    metadata = _hit_metadata(hit)
    keys = [
        hit.evidence.source_id,
        _metadata_text(metadata.get("canonical_source_id"), ""),
        _metadata_text(hit.source_locator.get("canonical_source_id"), ""),
        _metadata_text(hit.evidence.locator.get("canonical_source_id"), ""),
    ]
    return _unique_strings(keys)


def _source_requires_trust_policy(hit: RetrievalHit) -> bool:
    return hit.evidence.source_type.value in GOVERNED_SOURCE_TYPES


def _source_governance_severity(issues: list[str]) -> str:
    if any(issue in {"adapter_disabled", "lifecycle_blocked", "lifecycle_failed"} for issue in issues):
        return "destructive"
    if any(
        issue.startswith("lifecycle_")
        or issue.startswith("reviewer_state_")
        or issue == "missing_source_trust_policy"
        for issue in issues
    ):
        return "warning"
    if "review_required_by_source_policy" in issues:
        return "info"
    return "success"


def _source_governance_status(severity: str, issues: list[str]) -> str:
    if severity == "destructive":
        return "blocked"
    if "missing_source_trust_policy" in issues:
        return "unregistered"
    if severity in {"warning", "info"}:
        return "review_required"
    return "approved"


def _source_governance_package_status(
    decisions: Iterable[SourceGovernanceDecision],
) -> str:
    severity = _highest_source_governance_severity(decisions)
    if severity == "destructive":
        return "blocked"
    if severity == "warning":
        return "review_required"
    if severity == "info":
        return "review_recommended"
    return "approved"


def _highest_source_governance_severity(
    decisions: Iterable[SourceGovernanceDecision],
) -> str:
    severity_rank = {"success": 0, "info": 1, "warning": 2, "destructive": 3}
    highest = "success"
    for decision in decisions:
        if severity_rank.get(decision.severity, 0) > severity_rank[highest]:
            highest = decision.severity
    return highest


def _source_lifecycle_state(hit: RetrievalHit, *, adapter: Any | None) -> str | None:
    if adapter is not None:
        return str(adapter.lifecycle_state)
    return _source_metadata_text(hit, "lifecycle_state")


def _source_reviewer_state(hit: RetrievalHit, *, adapter: Any | None) -> str | None:
    if adapter is not None:
        return str(adapter.reviewer_state)
    return _source_metadata_text(hit, "reviewer_state")


def _source_standard_system(hit: RetrievalHit) -> str:
    return (
        _metadata_text(hit.evidence.locator.get("standard_system"), "")
        or _metadata_text(hit.source_locator.get("standard_system"), "")
        or _source_metadata_text(hit, "standard_system")
        or ""
    )


def _source_clinical_domain(hit: RetrievalHit) -> str:
    return (
        _metadata_text(hit.evidence.locator.get("clinical_domain"), "")
        or _metadata_text(hit.source_locator.get("clinical_domain"), "")
        or _source_metadata_text(hit, "clinical_domain")
        or ""
    )


def _source_metadata_text(hit: RetrievalHit, key: str) -> str | None:
    value = _metadata_text(_hit_metadata(hit).get(key), "")
    return value or None


def _adapter_metadata_text(adapter: Any, key: str) -> str | None:
    metadata = getattr(adapter, "metadata", {})
    if not isinstance(metadata, dict):
        return None
    value = _metadata_text(metadata.get(key), "")
    return value or None


def _hit_metadata(hit: RetrievalHit) -> dict[str, Any]:
    metadata = hit.evidence.locator.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _metadata_text(value: Any, fallback: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def _unique_strings(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
