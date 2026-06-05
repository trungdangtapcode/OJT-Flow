"""Policy-driven recommendations for retrieval judgment evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ojtflow.core.contracts.retrieval import RetrievalEvaluationRecommendation


@dataclass(frozen=True)
class RetrievalEvaluationPolicyRule:
    """One data-driven rule for turning evaluation metrics into tuning advice."""

    rule_id: str
    metric: str
    operator: str
    threshold: float
    severity: str
    message: str
    suggested_action: str
    min_judged_count: int = 0
    min_positive_count: int = 0
    include_unjudged_evidence_ids: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def recommendations_from_policy(
    *,
    rules: tuple[RetrievalEvaluationPolicyRule, ...],
    context: Mapping[str, Any],
    unjudged_evidence_ids: list[str],
) -> list[RetrievalEvaluationRecommendation]:
    """Evaluate policy rules against one ranked-result metric context."""

    recommendations: list[RetrievalEvaluationRecommendation] = []
    for rule in rules:
        if not _rule_matches(rule, context):
            continue
        evidence_ids = unjudged_evidence_ids if rule.include_unjudged_evidence_ids else []
        recommendations.append(
            RetrievalEvaluationRecommendation(
                rule_id=rule.rule_id,
                severity=rule.severity,
                metric=rule.metric,
                message=_format_policy_text(rule.message, context),
                suggested_action=_format_policy_text(rule.suggested_action, context),
                evidence_ids=evidence_ids,
                metadata={
                    **rule.metadata,
                    "operator": rule.operator,
                    "threshold": rule.threshold,
                    "actual": context.get(rule.metric),
                },
            )
        )
    return recommendations


def _rule_matches(
    rule: RetrievalEvaluationPolicyRule,
    context: Mapping[str, Any],
) -> bool:
    if int(context.get("judged_count", 0)) < rule.min_judged_count:
        return False
    if int(context.get("positive_count", 0)) < rule.min_positive_count:
        return False
    raw_value = context.get(rule.metric)
    if raw_value is None:
        return False
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return False
    return _compare(value, rule.operator, rule.threshold)


def _compare(value: float, operator: str, threshold: float) -> bool:
    if operator == "lt":
        return value < threshold
    if operator == "lte":
        return value <= threshold
    if operator == "gt":
        return value > threshold
    if operator == "gte":
        return value >= threshold
    if operator == "eq":
        return value == threshold
    return False


def _format_policy_text(template: str, context: Mapping[str, Any]) -> str:
    values = {
        key: _format_value(value)
        for key, value in context.items()
        if isinstance(key, str)
    }
    try:
        return template.format(**values)
    except (KeyError, ValueError):
        return template


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)
