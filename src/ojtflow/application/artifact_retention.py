"""Artifact retention policy resolution."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.artifacts import (
    ArtifactRetentionPolicy,
    ArtifactRetentionRule,
    ArtifactSource,
)
from ojtflow.core.time import utc_now
from ojtflow.data_tools.extract import source_format_for_filename


POTENTIAL_PHI_FORMATS = {"pdf", "docx", "xlsx", "xls", "image", "csv", "json", "yaml"}


def resolve_artifact_retention_policy(
    *,
    product_mode: str,
    owner_user_id: str,
    source: str,
    mime_type: str,
    filename: str,
    rules: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
) -> ArtifactRetentionPolicy:
    """Resolve a retention policy for one uploaded artifact."""

    sensitivity_class = _sensitivity_class(
        filename=filename,
        mime_type=mime_type,
        source=source,
    )
    typed_rules = [_rule_from_mapping(rule) for rule in rules]
    for rule in typed_rules:
        if _rule_matches(
            rule,
            product_mode=product_mode,
            owner_user_id=owner_user_id,
            source=source,
            sensitivity_class=sensitivity_class,
        ):
            return ArtifactRetentionPolicy(
                policy_id=rule.rule_id,
                sensitivity_class=sensitivity_class,
                action=rule.action,
                retain_until=_retain_until(rule.retain_days),
                reason=rule.reason or "Configured artifact retention rule.",
                mode=product_mode,
                source=_artifact_source(source),
                tenant_id=owner_user_id,
            )

    retain_days = 7 if product_mode in {"local_dev", "demo"} else 30
    action = "review" if sensitivity_class != "low" else "retain"
    return ArtifactRetentionPolicy(
        policy_id=f"default_{product_mode}_artifact_retention_v0",
        sensitivity_class=sensitivity_class,
        action=action,
        retain_until=_retain_until(retain_days),
        reason=(
            "Default upload retention policy; override with "
            "OJT_ARTIFACT_RETENTION_RULES for tenant/source/sensitivity-specific rules."
        ),
        mode=product_mode,
        source=_artifact_source(source),
        tenant_id=owner_user_id,
    )


def _rule_from_mapping(value: dict[str, Any]) -> ArtifactRetentionRule:
    return ArtifactRetentionRule.model_validate(value)


def _rule_matches(
    rule: ArtifactRetentionRule,
    *,
    product_mode: str,
    owner_user_id: str,
    source: str,
    sensitivity_class: str,
) -> bool:
    if rule.mode and rule.mode != product_mode:
        return False
    if rule.tenant_id and rule.tenant_id != owner_user_id:
        return False
    if rule.source and rule.source != source:
        return False
    if rule.sensitivity_class and rule.sensitivity_class != sensitivity_class:
        return False
    return True


def _sensitivity_class(*, filename: str, mime_type: str, source: str) -> str:
    try:
        source_format = source_format_for_filename(filename)
    except Exception:
        source_format = Path(filename).suffix.lower().lstrip(".")
    normalized_mime = mime_type.lower()
    if source == "clipboard":
        return "potential_phi"
    if source_format in POTENTIAL_PHI_FORMATS:
        return "potential_phi"
    if normalized_mime.startswith(("image/", "application/pdf")):
        return "potential_phi"
    return "low"


def _retain_until(days: int | None) -> str | None:
    if days is None:
        return None
    return (utc_now() + timedelta(days=days)).isoformat()


def _artifact_source(source: str) -> ArtifactSource:
    if source in {"upload", "clipboard", "assistant_attachment", "api"}:
        return source
    return "upload"
