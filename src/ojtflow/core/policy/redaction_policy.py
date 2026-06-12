"""Versioned PHI redaction policy."""

from __future__ import annotations

from ojtflow.core.contracts.phi import PhiFinding, PhiRiskLevel
from ojtflow.core.contracts.redaction import (
    RedactionActionType,
    RedactionPolicy,
    RedactionPolicyRule,
)


DEFAULT_PHI_REDACTION_POLICY = RedactionPolicy(
    policy_id="phi_redaction_policy_v0",
    version="2026-06-11",
    default_action="mask",
    token_namespace="ojtflow_local_placeholder_v0",
    external_provider_block_actions=["review_gated_reveal"],
    rules=[
        RedactionPolicyRule(
            rule_id="direct_identifier_mask",
            categories=["direct_identifier"],
            action="mask",
            replacement_template="[REDACTED:{kind}]",
            review_required=False,
            reveal_requires_review=True,
            reason="Direct identifiers are masked by default before export or provider use.",
        ),
        RedactionPolicyRule(
            rule_id="contact_mask",
            categories=["contact"],
            action="mask",
            replacement_template="[REDACTED:{kind}]",
            review_required=False,
            reveal_requires_review=True,
            reason="Contact identifiers are masked by default before export or provider use.",
        ),
        RedactionPolicyRule(
            rule_id="clinical_context_review_gate",
            categories=["clinical_context", "demographic", "free_text_sensitive"],
            action="review_gated_reveal",
            replacement_template="[REVIEW_REQUIRED:{kind}]",
            review_required=True,
            reveal_requires_review=True,
            reason="Clinical and demographic context may be meaningful; reveal requires review.",
        ),
    ],
)


def default_redaction_policy() -> RedactionPolicy:
    """Return the active built-in redaction policy."""

    return DEFAULT_PHI_REDACTION_POLICY


def redaction_rule_for_finding(
    finding: PhiFinding,
    *,
    policy: RedactionPolicy | None = None,
    action_override: RedactionActionType | None = None,
) -> RedactionPolicyRule:
    """Resolve the redaction rule for a PHI finding."""

    active_policy = policy or default_redaction_policy()
    if action_override:
        return RedactionPolicyRule(
            rule_id=f"override_{action_override}",
            action=action_override,
            kinds=[finding.kind],
            categories=[finding.category],
            risk_levels=[],
            replacement_template=_default_template(action_override),
            review_required=action_override == "review_gated_reveal",
            reveal_requires_review=action_override == "review_gated_reveal",
            reason=f"Caller requested redaction action '{action_override}'.",
        )

    for rule in active_policy.rules:
        if rule.kinds and finding.kind in rule.kinds:
            return rule
        if rule.categories and finding.category in rule.categories:
            return rule
        if rule.risk_levels and _risk_level_matches(finding, rule.risk_levels):
            return rule

    return RedactionPolicyRule(
        rule_id="default_redaction_action",
        action=active_policy.default_action,
        kinds=[finding.kind],
        categories=[finding.category],
        replacement_template=_default_template(active_policy.default_action),
        review_required=False,
        reveal_requires_review=False,
        reason="No specific redaction rule matched; applied the default policy action.",
    )


def _risk_level_matches(finding: PhiFinding, risk_levels: list[PhiRiskLevel]) -> bool:
    if finding.category == "direct_identifier":
        return "high" in risk_levels
    if finding.category in {"contact", "clinical_context", "demographic"}:
        return "medium" in risk_levels
    return "low" in risk_levels


def _default_template(action: RedactionActionType) -> str:
    if action == "review_gated_reveal":
        return "[REVIEW_REQUIRED:{kind}]"
    if action == "tokenize_placeholder":
        return "[TOKEN:{kind}:{token}]"
    if action == "suppress":
        return ""
    return "[REDACTED:{kind}]"
