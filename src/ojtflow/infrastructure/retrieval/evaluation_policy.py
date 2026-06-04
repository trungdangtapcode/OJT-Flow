"""Load retrieval evaluation policy rules from trusted knowledge data."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ojtflow.application.retrieval_evaluation_policy import RetrievalEvaluationPolicyRule

DEFAULT_EVALUATION_POLICY_PATH = Path("retrieval/evaluation_policy.json")
SUPPORTED_OPERATORS = {"lt", "lte", "gt", "gte", "eq"}


def load_retrieval_evaluation_policy(
    knowledge_root: Path,
) -> tuple[RetrievalEvaluationPolicyRule, ...]:
    """Load operator-facing retrieval tuning policy from the knowledge registry."""

    override = os.environ.get("OJT_RETRIEVAL_EVALUATION_POLICY_PATH")
    path = Path(override) if override else knowledge_root / DEFAULT_EVALUATION_POLICY_PATH
    return _load_retrieval_evaluation_policy(path)


def _load_retrieval_evaluation_policy(path: Path) -> tuple[RetrievalEvaluationPolicyRule, ...]:
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"Invalid retrieval evaluation policy at {path}: expected rules list")
    rules = tuple(_policy_rule(record, path=path) for record in records)
    _ensure_unique_rule_ids(rules, path=path)
    return rules


def _policy_rule(record: Any, *, path: Path) -> RetrievalEvaluationPolicyRule:
    if not isinstance(record, dict):
        raise ValueError(f"Invalid retrieval evaluation policy at {path}: rule must be an object")
    required = (
        "rule_id",
        "metric",
        "operator",
        "threshold",
        "severity",
        "message",
        "suggested_action",
    )
    missing = [field for field in required if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Invalid retrieval evaluation policy at {path}: missing {missing_text}")
    operator = _required_text(record["operator"], field="operator", path=path)
    if operator not in SUPPORTED_OPERATORS:
        raise ValueError(
            f"Invalid retrieval evaluation policy at {path}: unsupported operator {operator}"
        )
    return RetrievalEvaluationPolicyRule(
        rule_id=_required_text(record["rule_id"], field="rule_id", path=path),
        metric=_required_text(record["metric"], field="metric", path=path),
        operator=operator,
        threshold=_number(record["threshold"], field="threshold", path=path),
        severity=_required_text(record["severity"], field="severity", path=path),
        message=_required_text(record["message"], field="message", path=path),
        suggested_action=_required_text(
            record["suggested_action"],
            field="suggested_action",
            path=path,
        ),
        min_judged_count=_optional_int(
            record.get("min_judged_count"),
            field="min_judged_count",
            path=path,
        ),
        min_positive_count=_optional_int(
            record.get("min_positive_count"),
            field="min_positive_count",
            path=path,
        ),
        include_unjudged_evidence_ids=_optional_bool(
            record.get("include_unjudged_evidence_ids"),
            field="include_unjudged_evidence_ids",
            path=path,
        ),
        metadata=record["metadata"] if isinstance(record.get("metadata"), dict) else {},
    )


def _number(value: Any, *, field: str, path: Path) -> float:
    if isinstance(value, bool):
        raise ValueError(
            f"Invalid retrieval evaluation policy at {path}: {field} must be a number"
        )
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid retrieval evaluation policy at {path}: {field} must be a number"
        ) from exc


def _optional_int(value: Any, *, field: str, path: Path) -> int:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"Invalid retrieval evaluation policy at {path}: {field} must be a non-negative integer"
        )
    return value


def _optional_bool(value: Any, *, field: str, path: Path) -> bool:
    if value is None:
        return False
    if not isinstance(value, bool):
        raise ValueError(
            f"Invalid retrieval evaluation policy at {path}: {field} must be a boolean"
        )
    return value


def _required_text(value: Any, *, field: str, path: Path) -> str:
    text = " ".join(str(value).split())
    if not text:
        raise ValueError(f"Invalid retrieval evaluation policy at {path}: {field} cannot be blank")
    return text


def _ensure_unique_rule_ids(
    rules: tuple[RetrievalEvaluationPolicyRule, ...],
    *,
    path: Path,
) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for rule in rules:
        if rule.rule_id in seen:
            duplicates.add(rule.rule_id)
        seen.add(rule.rule_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Invalid retrieval evaluation policy at {path}: duplicate rule_id {duplicate_text}"
        )
