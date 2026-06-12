"""Retrieval source freshness/readiness reporting."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from ojtflow.core.contracts.retrieval import (
    CorpusIngestionItem,
    CorpusSourceAdapter,
    MedicalSourceQualityPolicyCatalog,
    MedicalSourceQualityScore,
    RetrievalFreshnessReport,
    RetrievalFreshnessSource,
    RetrievalSource,
    RetrievalSourceTrustPolicy,
)
from ojtflow.infrastructure.retrieval.catalogs import (
    load_corpus_adapter_catalog,
    load_medical_source_quality_policy_catalog,
    load_source_trust_policy_catalog,
)
from ojtflow.infrastructure.retrieval.corpus import build_corpus_ingestion_manifest
from ojtflow.infrastructure.retrieval.source_quality import score_medical_source_quality


def build_retrieval_freshness_report(
    knowledge_root: Path,
    *,
    indexed_sources: list[RetrievalSource],
    generated_at: datetime | None = None,
) -> RetrievalFreshnessReport:
    """Build a data-driven readiness report for governed retrieval sources."""

    generated_at_value = generated_at or datetime.now(UTC)
    adapter_catalog = load_corpus_adapter_catalog(knowledge_root)
    policy_catalog = load_source_trust_policy_catalog(knowledge_root)
    quality_policy = load_medical_source_quality_policy_catalog(knowledge_root)
    manifest = build_corpus_ingestion_manifest(
        (knowledge_root / "corpus",),
        knowledge_root=knowledge_root,
        generated_at=generated_at_value,
    )
    manifest_by_source = _manifest_items_by_source(manifest.items)
    indexed_by_source = {source.source_id: source for source in indexed_sources}
    policies = _policy_index(policy_catalog.policies)

    adapter_sources = {
        adapter.source_id: _source_status(
            adapter,
            indexed=indexed_by_source.get(adapter.source_id),
            manifest_items=manifest_by_source.get(adapter.source_id, []),
            policy=_policy_for_adapter(adapter, policies),
            quality_policy=quality_policy,
            generated_at=generated_at_value,
        )
        for adapter in adapter_catalog.adapters
    }
    for source in indexed_sources:
        if source.source_id in adapter_sources:
            continue
        adapter_sources[source.source_id] = _indexed_only_source_status(
            source,
            policy=policies.by_source_id.get(source.source_id),
            quality_policy=quality_policy,
        )

    sources = sorted(
        adapter_sources.values(),
        key=lambda item: (_status_sort_key(item.status), item.standard_system or "", item.source_id),
    )
    counts = Counter(source.status for source in sources)
    stale_count = sum(1 for source in sources if "stale_source" in source.issues)
    unindexed_count = sum(1 for source in sources if "not_indexed" in source.issues)
    missing_policy_count = sum(1 for source in sources if "missing_trust_policy" in source.issues)
    average_quality_score = _average_quality_score(sources)
    low_quality_count = sum(
        1
        for source in sources
        if source.quality is not None and source.quality.status in {"needs_review", "blocked"}
    )
    quality_review_count = sum(
        1
        for source in sources
        if source.quality is not None and source.quality.status != "ready"
    )
    score = _readiness_score(
        source_count=len(sources),
        blocked_count=counts["blocked"],
        needs_review_count=counts["needs_review"],
        watch_count=counts["watch"],
        stale_count=stale_count,
        unindexed_count=unindexed_count,
        missing_policy_count=missing_policy_count,
    )
    status = _report_status(
        blocked_count=counts["blocked"],
        needs_review_count=counts["needs_review"],
        watch_count=counts["watch"],
    )
    return RetrievalFreshnessReport(
        version="retrieval_freshness_report.v1",
        generated_at=_isoformat(generated_at_value),
        status=status,
        score=score,
        source_count=len(sources),
        ready_count=counts["ready"],
        watch_count=counts["watch"],
        needs_review_count=counts["needs_review"],
        blocked_count=counts["blocked"],
        stale_count=stale_count,
        unindexed_count=unindexed_count,
        missing_policy_count=missing_policy_count,
        average_quality_score=average_quality_score,
        low_quality_count=low_quality_count,
        quality_review_count=quality_review_count,
        adapter_catalog_version=adapter_catalog.version,
        manifest_version=manifest.version,
        policy_catalog_version=policy_catalog.version,
        quality_policy_version=quality_policy.version,
        sources=sources,
        warnings=_report_warnings(
            stale_count=stale_count,
            unindexed_count=unindexed_count,
            missing_policy_count=missing_policy_count,
            low_quality_count=low_quality_count,
        ),
    )


def _source_status(
    adapter: CorpusSourceAdapter,
    *,
    indexed: RetrievalSource | None,
    manifest_items: list[CorpusIngestionItem],
    policy: RetrievalSourceTrustPolicy | None,
    quality_policy: MedicalSourceQualityPolicyCatalog,
    generated_at: datetime,
) -> RetrievalFreshnessSource:
    issues: list[str] = []
    actions: list[str] = []
    indexed_chunk_count = indexed.chunk_count if indexed else 0
    if not adapter.enabled:
        issues.append("adapter_disabled")
        actions.append("Enable the source adapter before using it in retrieval.")
    if adapter.lifecycle_state in {"blocked", "failed"}:
        issues.append(f"lifecycle_{adapter.lifecycle_state}")
        actions.append("Keep the source out of retrieval until governance clears it.")
    elif adapter.lifecycle_state in {"candidate", "needs_review"}:
        issues.append(f"lifecycle_{adapter.lifecycle_state}")
        actions.append("Approve or reject the source lifecycle state before production use.")
    elif adapter.lifecycle_state == "deprecated":
        issues.append("lifecycle_deprecated")
        actions.append("Replace this source with a current release before relying on it.")
    if adapter.reviewer_state != "approved":
        issues.append(f"reviewer_state_{adapter.reviewer_state}")
        actions.append("Route the source through reviewer approval.")
    if policy is None:
        issues.append("missing_trust_policy")
        actions.append("Add a source trust policy with intended use and license boundaries.")
    if adapter.local_paths and indexed_chunk_count == 0:
        issues.append("not_indexed")
        actions.append("Run corpus reindex so approved local snapshots can be retrieved.")
    if not adapter.local_paths and adapter.access_mode != "local_curated_file":
        issues.append("external_snapshot_not_present")
        actions.append("Create a governed snapshot or use a transparent external search handoff.")

    last_observed = _last_observed_at(manifest_items)
    freshness_window = _freshness_window_days(adapter.refresh_cadence)
    age_days = _age_days(last_observed, generated_at)
    if (
        last_observed is not None
        and freshness_window is not None
        and age_days is not None
        and age_days > freshness_window
    ):
        issues.append("stale_source")
        actions.append("Refresh or re-ingest this source before using it as authoritative evidence.")

    status, severity = _status_for_issues(issues)
    quality = _source_quality_for_adapter(
        adapter,
        policy=policy,
        quality_policy=quality_policy,
        indexed_chunk_count=indexed_chunk_count,
        manifest_item_count=len(manifest_items),
        status=status,
        severity=severity,
        issues=issues,
    )
    return RetrievalFreshnessSource(
        source_id=adapter.source_id,
        title=adapter.title,
        source_type=adapter.source_type,
        authority=adapter.authority,
        standard_system=adapter.standard_system,
        clinical_domain=adapter.clinical_domain,
        release_version=adapter.release_version,
        refresh_cadence=adapter.refresh_cadence,
        lifecycle_state=adapter.lifecycle_state,
        reviewer_state=adapter.reviewer_state,
        indexed_chunk_count=indexed_chunk_count,
        manifest_item_count=len(manifest_items),
        last_observed_at=_isoformat(last_observed) if last_observed else None,
        age_days=age_days,
        freshness_window_days=freshness_window,
        status=status,
        severity=severity,
        issues=_dedupe(issues),
        recommended_actions=_dedupe(actions),
        source_urls=adapter.source_urls,
        quality=quality,
        metadata={
            "adapter_id": adapter.adapter_id,
            "access_mode": adapter.access_mode,
            "ingestion_mode": adapter.ingestion_mode,
            "chunk_profile": adapter.chunk_profile,
            "policy_source_id": policy.source_id if policy else None,
            "policy_evidence_tier": policy.evidence_tier if policy else None,
            "local_paths": list(adapter.local_paths),
        },
    )


def _indexed_only_source_status(
    source: RetrievalSource,
    *,
    policy: RetrievalSourceTrustPolicy | None,
    quality_policy: MedicalSourceQualityPolicyCatalog,
) -> RetrievalFreshnessSource:
    issues = ["missing_source_adapter"]
    actions = ["Register the indexed source in the governed corpus adapter catalog."]
    if policy is None:
        issues.append("missing_trust_policy")
        actions.append("Add a source trust policy with intended use and license boundaries.")
    status, severity = _status_for_issues(issues)
    quality = _source_quality_for_indexed_only(
        source,
        policy=policy,
        quality_policy=quality_policy,
        status=status,
        severity=severity,
        issues=issues,
    )
    return RetrievalFreshnessSource(
        source_id=source.source_id,
        title=source.title,
        source_type=source.source_type,
        authority=source.authority,
        standard_system=source.standard_system,
        clinical_domain=source.clinical_domain,
        release_version=source.source_version,
        refresh_cadence=policy.refresh_cadence if policy else None,
        lifecycle_state=source.lifecycle_state,
        reviewer_state=source.reviewer_state,
        indexed_chunk_count=source.chunk_count,
        manifest_item_count=0,
        status=status,
        severity=severity,
        issues=issues,
        recommended_actions=actions,
        source_urls=policy.source_urls if policy else {},
        quality=quality,
        metadata={
            "canonical_source_id": source.canonical_source_id,
            "chunk_profile": source.chunk_profile,
            "policy_source_id": policy.source_id if policy else None,
        },
    )


def _manifest_items_by_source(items: list[CorpusIngestionItem]) -> dict[str, list[CorpusIngestionItem]]:
    by_source: dict[str, list[CorpusIngestionItem]] = defaultdict(list)
    for item in items:
        by_source[item.source_id].append(item)
        canonical = item.metadata.get("canonical_source_id")
        if isinstance(canonical, str) and canonical:
            by_source[canonical].append(item)
    return dict(by_source)


class _PolicyIndex:
    def __init__(self, policies: list[RetrievalSourceTrustPolicy]) -> None:
        self.by_source_id = {policy.source_id: policy for policy in policies}
        self.by_standard: dict[str, list[RetrievalSourceTrustPolicy]] = defaultdict(list)
        self.by_standard_domain: dict[tuple[str, str], list[RetrievalSourceTrustPolicy]] = (
            defaultdict(list)
        )
        for policy in policies:
            standard = policy.standard_system.lower()
            domain = policy.domain.lower()
            self.by_standard[standard].append(policy)
            self.by_standard_domain[(standard, domain)].append(policy)


def _policy_index(policies: list[RetrievalSourceTrustPolicy]) -> _PolicyIndex:
    return _PolicyIndex(policies)


def _policy_for_adapter(
    adapter: CorpusSourceAdapter,
    policies: _PolicyIndex,
) -> RetrievalSourceTrustPolicy | None:
    metadata_policy = adapter.metadata.get("trust_policy_source_id")
    if isinstance(metadata_policy, str) and metadata_policy in policies.by_source_id:
        return policies.by_source_id[metadata_policy]
    if adapter.source_id in policies.by_source_id:
        return policies.by_source_id[adapter.source_id]
    candidates = policies.by_standard_domain.get(
        (adapter.standard_system.lower(), adapter.clinical_domain.lower()),
        [],
    )
    if candidates:
        return candidates[0]
    candidates = policies.by_standard.get(adapter.standard_system.lower(), [])
    return candidates[0] if len(candidates) == 1 else None


def _source_quality_for_adapter(
    adapter: CorpusSourceAdapter,
    *,
    policy: RetrievalSourceTrustPolicy | None,
    quality_policy: MedicalSourceQualityPolicyCatalog,
    indexed_chunk_count: int,
    manifest_item_count: int,
    status: str,
    severity: str,
    issues: list[str],
) -> MedicalSourceQualityScore:
    return score_medical_source_quality(
        quality_policy,
        dimensions={
            "source_id": adapter.source_id,
            "source_type": adapter.source_type.value,
            "authority": adapter.authority,
            "standard_system": adapter.standard_system,
            "clinical_domain": adapter.clinical_domain,
            "source_policy_presence": "present" if policy is not None else "missing",
            "adapter_presence": "present",
            "adapter_enabled": "true" if adapter.enabled else "false",
            "evidence_tier": policy.evidence_tier if policy is not None else "unknown",
            "lifecycle_state": adapter.lifecycle_state,
            "reviewer_state": adapter.reviewer_state,
            "freshness_status": status,
            "freshness_severity": severity,
            "issue": _dedupe(issues),
            "coverage_state": _coverage_state(
                indexed_chunk_count=indexed_chunk_count,
                manifest_item_count=manifest_item_count,
                local_path_count=len(adapter.local_paths),
                access_mode=adapter.access_mode,
            ),
            "indexed_chunk_count": indexed_chunk_count,
            "manifest_item_count": manifest_item_count,
            "license_constraint_keyword": _license_constraint_texts(adapter, policy=policy),
            "requires_reviewer_approval": (
                "true" if policy is not None and policy.requires_reviewer_approval else "false"
            ),
        },
    )


def _source_quality_for_indexed_only(
    source: RetrievalSource,
    *,
    policy: RetrievalSourceTrustPolicy | None,
    quality_policy: MedicalSourceQualityPolicyCatalog,
    status: str,
    severity: str,
    issues: list[str],
) -> MedicalSourceQualityScore:
    return score_medical_source_quality(
        quality_policy,
        dimensions={
            "source_id": source.source_id,
            "source_type": source.source_type.value,
            "authority": source.authority,
            "standard_system": source.standard_system,
            "clinical_domain": source.clinical_domain,
            "source_policy_presence": "present" if policy is not None else "missing",
            "adapter_presence": "missing",
            "adapter_enabled": "unknown",
            "evidence_tier": policy.evidence_tier if policy is not None else "unknown",
            "lifecycle_state": source.lifecycle_state or "unknown",
            "reviewer_state": source.reviewer_state or "unknown",
            "freshness_status": status,
            "freshness_severity": severity,
            "issue": _dedupe(issues),
            "coverage_state": "indexed_only",
            "indexed_chunk_count": source.chunk_count,
            "manifest_item_count": 0,
            "license_constraint_keyword": list(policy.license_constraints) if policy else [],
            "requires_reviewer_approval": (
                "true" if policy is not None and policy.requires_reviewer_approval else "false"
            ),
        },
    )


def _coverage_state(
    *,
    indexed_chunk_count: int,
    manifest_item_count: int,
    local_path_count: int,
    access_mode: str,
) -> str:
    if indexed_chunk_count > 0 and manifest_item_count > 0:
        return "indexed_manifested"
    if indexed_chunk_count > 0:
        return "indexed_only"
    if manifest_item_count > 0:
        return "manifest_only"
    if local_path_count == 0 and access_mode != "local_curated_file":
        return "external_without_snapshot"
    return "unindexed"


def _license_constraint_texts(
    adapter: CorpusSourceAdapter,
    *,
    policy: RetrievalSourceTrustPolicy | None,
) -> list[str]:
    values = list(adapter.license.constraints)
    if policy is not None:
        values.extend(policy.license_constraints)
        values.extend(policy.prohibited_use)
    return _dedupe(values)


def _last_observed_at(items: list[CorpusIngestionItem]) -> datetime | None:
    values = [_parse_iso(item.fetched_at) for item in items]
    values = [value for value in values if value is not None]
    return max(values) if values else None


def _parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _age_days(last_observed: datetime | None, generated_at: datetime) -> int | None:
    if last_observed is None:
        return None
    return max(0, (generated_at - last_observed).days)


def _freshness_window_days(refresh_cadence: str) -> int | None:
    cadence = refresh_cadence.lower()
    if "daily" in cadence:
        return 2
    if "weekly" in cadence:
        return 14
    if "monthly" in cadence:
        return 45
    if "quarterly" in cadence:
        return 120
    if "per_release" in cadence:
        return 120
    if "before_demo_freeze" in cadence:
        return 30
    return None


def _status_for_issues(issues: list[str]) -> tuple[str, str]:
    issue_set = set(issues)
    if issue_set & {"adapter_disabled", "lifecycle_blocked", "lifecycle_failed"}:
        return "blocked", "destructive"
    if issue_set & {"reviewer_state_blocked", "reviewer_state_failed"}:
        return "blocked", "destructive"
    if issue_set & {
        "lifecycle_candidate",
        "lifecycle_needs_review",
        "lifecycle_deprecated",
        "reviewer_state_candidate",
        "reviewer_state_needs_review",
        "reviewer_state_deprecated",
        "missing_trust_policy",
        "missing_source_adapter",
    }:
        return "needs_review", "warning"
    if issue_set & {"not_indexed", "external_snapshot_not_present", "stale_source"}:
        return "watch", "warning"
    return "ready", "info"


def _readiness_score(
    *,
    source_count: int,
    blocked_count: int,
    needs_review_count: int,
    watch_count: int,
    stale_count: int,
    unindexed_count: int,
    missing_policy_count: int,
) -> int:
    if source_count == 0:
        return 0
    penalty = (
        blocked_count * 25
        + needs_review_count * 12
        + watch_count * 6
        + stale_count * 5
        + unindexed_count * 4
        + missing_policy_count * 6
    )
    return max(0, min(100, 100 - penalty))


def _report_status(
    *,
    blocked_count: int,
    needs_review_count: int,
    watch_count: int,
) -> str:
    if blocked_count:
        return "blocked"
    if needs_review_count:
        return "needs_review"
    if watch_count:
        return "watch"
    return "ready"


def _report_warnings(
    *,
    stale_count: int,
    unindexed_count: int,
    missing_policy_count: int,
    low_quality_count: int,
) -> list[str]:
    warnings: list[str] = []
    if stale_count:
        warnings.append(f"{stale_count} source(s) are outside their freshness window.")
    if unindexed_count:
        warnings.append(f"{unindexed_count} source(s) are configured but not indexed.")
    if missing_policy_count:
        warnings.append(f"{missing_policy_count} source(s) lack an explicit trust policy.")
    if low_quality_count:
        warnings.append(f"{low_quality_count} source(s) have low medical source quality scores.")
    return warnings


def _average_quality_score(sources: list[RetrievalFreshnessSource]) -> int:
    scores = [source.quality.score for source in sources if source.quality is not None]
    if not scores:
        return 0
    return round(sum(scores) / len(scores))


def _status_sort_key(status: str) -> int:
    return {"blocked": 0, "needs_review": 1, "watch": 2, "ready": 3}.get(status, 4)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _isoformat(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
