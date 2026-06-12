"""Data-driven medical source quality scoring."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ojtflow.core.contracts.retrieval import (
    MedicalSourceQualityPolicyCatalog,
    MedicalSourceQualityScore,
    MedicalSourceQualitySignal,
    RetrievalFreshnessStatus,
)


def score_medical_source_quality(
    policy: MedicalSourceQualityPolicyCatalog,
    *,
    dimensions: Mapping[str, Any],
) -> MedicalSourceQualityScore:
    """Apply the configured source-quality policy to normalized source facts."""

    signals: list[MedicalSourceQualitySignal] = []
    for rule in policy.rules:
        matched_value = _matched_rule_value(rule.dimension, rule.match_values, dimensions)
        if matched_value is None:
            continue
        signals.append(
            MedicalSourceQualitySignal(
                rule_id=rule.rule_id,
                dimension=rule.dimension,
                matched_value=matched_value,
                score_delta=rule.score_delta,
                severity=rule.severity,
                message=rule.message,
                suggested_action=rule.suggested_action,
                metadata=rule.metadata,
            )
        )

    raw_score = policy.base_score + sum(signal.score_delta for signal in signals)
    score = max(0, min(100, raw_score))
    negative_delta = abs(sum(signal.score_delta for signal in signals if signal.score_delta < 0))
    positive_delta = sum(signal.score_delta for signal in signals if signal.score_delta > 0)
    severity = _highest_severity(signal.severity for signal in signals)
    return MedicalSourceQualityScore(
        policy_version=policy.version,
        score=score,
        status=_status_for_score(score, severity=severity, policy=policy),
        severity=severity,
        base_score=policy.base_score,
        positive_delta=positive_delta,
        negative_delta=negative_delta,
        top_action=_top_action(signals),
        signals=signals,
        dimensions=_serializable_dimensions(dimensions),
    )


def _matched_rule_value(
    dimension: str,
    match_values: list[str],
    dimensions: Mapping[str, Any],
) -> str | None:
    actual_values = _dimension_values(dimensions.get(dimension))
    if not actual_values:
        return None
    if not match_values:
        return actual_values[0]
    normalized_matches = [value.strip().lower() for value in match_values if value.strip()]
    if dimension == "license_constraint_keyword":
        for actual in actual_values:
            actual_lower = actual.lower()
            for expected in normalized_matches:
                if expected and expected in actual_lower:
                    return expected
        return None
    actual_lookup = {value.lower(): value for value in actual_values}
    for expected in normalized_matches:
        if expected in actual_lookup:
            return actual_lookup[expected]
    return None


def _dimension_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, bool):
        return ["true" if value else "false"]
    if isinstance(value, int | float):
        return [str(value)]
    if isinstance(value, Mapping):
        return [
            f"{key}:{nested}"
            for key, nested in value.items()
            if str(key).strip() and str(nested).strip()
        ]
    if isinstance(value, Iterable):
        result: list[str] = []
        for item in value:
            result.extend(_dimension_values(item))
        return result
    text = str(value).strip()
    return [text] if text else []


def _highest_severity(severities: Iterable[str]) -> str:
    order = {
        "success": 0,
        "info": 1,
        "warning": 2,
        "error": 3,
        "destructive": 4,
    }
    highest = "info"
    highest_rank = order[highest]
    for severity in severities:
        rank = order.get(severity, 1)
        if rank > highest_rank:
            highest = severity
            highest_rank = rank
    return highest


def _status_for_score(
    score: int,
    *,
    severity: str,
    policy: MedicalSourceQualityPolicyCatalog,
) -> RetrievalFreshnessStatus:
    if severity in {"destructive", "error"}:
        return "blocked"
    thresholds = policy.status_thresholds
    if score >= thresholds.ready_min:
        return "ready"
    if score >= thresholds.watch_min:
        return "watch"
    if score >= thresholds.needs_review_min:
        return "needs_review"
    return "blocked"


def _top_action(signals: list[MedicalSourceQualitySignal]) -> str:
    risky_signals = [signal for signal in signals if signal.score_delta < 0]
    if not risky_signals:
        return "Keep source quality metadata current during ingestion and reindexing."
    severity_rank = {
        "success": 0,
        "info": 1,
        "warning": 2,
        "error": 3,
        "destructive": 4,
    }
    selected = max(
        risky_signals,
        key=lambda signal: (
            severity_rank.get(signal.severity, 1),
            abs(signal.score_delta),
            signal.rule_id,
        ),
    )
    return selected.suggested_action


def _serializable_dimensions(dimensions: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: _serializable_value(value)
        for key, value in sorted(dimensions.items())
    }


def _serializable_value(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _serializable_value(nested)
            for key, nested in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, Iterable):
        return [_serializable_value(item) for item in value]
    return str(value)
