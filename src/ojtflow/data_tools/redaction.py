"""Rule-based sensitive text redaction preview."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from typing import Any

from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.contracts.phi import (
    PhiClassificationPolicy,
    PhiFinding,
    PhiPatternRule,
)
from ojtflow.core.contracts.redaction import (
    RedactionActionType,
    RedactionMatch,
    RedactionMatchStatus,
    RedactionPolicy,
    RedactionPolicyRule,
    RedactionPreview,
)
from ojtflow.core.policy.phi_policy import default_phi_policy, match_phi_field_rule
from ojtflow.core.policy.redaction_policy import (
    default_redaction_policy,
    redaction_rule_for_finding,
)
from ojtflow.data_tools.phi import classify_text


def build_redaction_preview(
    text: str,
    *,
    data_format: DataFormat | None = None,
    action_override: RedactionActionType | None = None,
    reveal_approved: bool = False,
    redaction_policy: RedactionPolicy | None = None,
    phi_policy: PhiClassificationPolicy | None = None,
) -> RedactionPreview:
    """Return redacted text and match metadata without mutating source content."""

    active_phi_policy = phi_policy or default_phi_policy()
    active_redaction_policy = redaction_policy or default_redaction_policy()
    phi_classification = classify_text(
        text,
        data_format=data_format,
        target_type="document",
        policy=active_phi_policy,
    )
    matches: list[RedactionMatch] = []
    redacted_text = _redact_sensitive_csv_fields(
        text,
        matches=matches,
        enabled=data_format in {DataFormat.CSV, None},
        phi_policy=active_phi_policy,
        redaction_policy=active_redaction_policy,
        action_override=action_override,
        reveal_approved=reveal_approved,
    )
    redacted_text = _redact_regex_matches(
        redacted_text,
        matches=matches,
        rules=active_phi_policy.pattern_rules,
        redaction_policy=active_redaction_policy,
        action_override=action_override,
        reveal_approved=reveal_approved,
    )
    warnings: list[str] = []
    if matches:
        warnings.append(
            "Potential sensitive text was found. Review redacted preview before "
            "sending content to external LLM or OCR providers."
        )
    if any(match.status == "requires_review" for match in matches):
        warnings.append("Some PHI can only be revealed after human review.")
    return RedactionPreview(
        policy_id=active_redaction_policy.policy_id,
        policy_version=active_redaction_policy.version,
        original_length=len(text),
        redacted_text=redacted_text,
        matches=matches,
        phi_classification=phi_classification,
        action_summary=_action_summary(matches),
        requires_review=any(match.status == "requires_review" for match in matches),
        reveal_required=any(match.reveal_requires_review for match in matches)
        and not reveal_approved,
        reveal_approved=reveal_approved,
        external_provider_block_recommended=(
            bool(matches)
            or phi_classification.external_provider_block_recommended
            or any(
                match.action in active_redaction_policy.external_provider_block_actions
                for match in matches
            )
        ),
        warnings=warnings,
    )


def _redact_sensitive_csv_fields(
    text: str,
    *,
    matches: list[RedactionMatch],
    enabled: bool,
    phi_policy: PhiClassificationPolicy,
    redaction_policy: RedactionPolicy,
    action_override: RedactionActionType | None,
    reveal_approved: bool,
) -> str:
    if not enabled or "," not in text or "\n" not in text:
        return text
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return text
    if len(rows) < 2 or not rows[0]:
        return text

    headers = [header.strip() for header in rows[0]]
    sensitive_columns = [
        index
        for index, header in enumerate(headers)
        if header and match_phi_field_rule(header, policy=phi_policy)
    ]
    if not sensitive_columns:
        return text

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(rows[0])
    for row_index, row in enumerate(rows[1:], start=2):
        redacted_row = list(row)
        for column_index in sensitive_columns:
            if column_index >= len(redacted_row):
                continue
            value = redacted_row[column_index]
            if value in (None, ""):
                continue
            header = headers[column_index]
            field_rule = match_phi_field_rule(header, policy=phi_policy)
            if not field_rule:
                continue
            location = SourceLocation(row=row_index, column=header, field=header)
            finding = PhiFinding(
                target_type="field",
                category=field_rule.category,
                kind=field_rule.kind,
                confidence=field_rule.confidence,
                reason=field_rule.reason,
                field=header,
                value_preview=_preview(value),
                location=location,
            )
            match = _redaction_match(
                finding=finding,
                value=value,
                rule=redaction_rule_for_finding(
                    finding,
                    policy=redaction_policy,
                    action_override=action_override,
                ),
                policy=redaction_policy,
                reveal_approved=reveal_approved,
                location=location,
            )
            matches.append(match)
            redacted_row[column_index] = match.replacement
        writer.writerow(redacted_row)
    return output.getvalue().rstrip("\n")


def _redact_regex_matches(
    text: str,
    *,
    matches: list[RedactionMatch],
    rules: list[PhiPatternRule],
    redaction_policy: RedactionPolicy,
    action_override: RedactionActionType | None,
    reveal_approved: bool,
) -> str:
    redacted = text
    for pattern_rule in rules:
        pattern = re.compile(pattern_rule.pattern, re.IGNORECASE)
        pieces: list[str] = []
        cursor = 0
        found = False
        for match in pattern.finditer(redacted):
            found = True
            value = match.group(0)
            finding = PhiFinding(
                target_type="document",
                category=pattern_rule.category,
                kind=pattern_rule.kind,
                confidence=pattern_rule.confidence,
                reason=pattern_rule.reason,
                value_preview=_preview(value),
            )
            redaction_match = _redaction_match(
                finding=finding,
                value=value,
                rule=redaction_rule_for_finding(
                    finding,
                    policy=redaction_policy,
                    action_override=action_override,
                ),
                policy=redaction_policy,
                reveal_approved=reveal_approved,
                start=match.start(),
                end=match.end(),
            )
            pieces.append(redacted[cursor:match.start()])
            pieces.append(redaction_match.replacement)
            matches.append(redaction_match)
            cursor = match.end()
        if found:
            pieces.append(redacted[cursor:])
            redacted = "".join(pieces)
    return redacted


def _redaction_match(
    *,
    finding: PhiFinding,
    value: Any,
    rule: RedactionPolicyRule,
    policy: RedactionPolicy,
    reveal_approved: bool,
    start: int | None = None,
    end: int | None = None,
    location: SourceLocation | None = None,
) -> RedactionMatch:
    replacement, status, token = _replacement(
        value=value,
        kind=finding.kind,
        rule=rule,
        policy=policy,
        reveal_approved=reveal_approved,
    )
    return RedactionMatch(
        kind=finding.kind,
        value_preview=_preview(value),
        replacement=replacement,
        action=rule.action,
        status=status,
        rule_id=rule.rule_id,
        token=token,
        confidence=finding.confidence,
        reason=f"{finding.reason} {rule.reason}",
        start=start,
        end=end,
        location=location,
        reveal_requires_review=rule.reveal_requires_review,
    )


def _replacement(
    *,
    value: Any,
    kind: str,
    rule: RedactionPolicyRule,
    policy: RedactionPolicy,
    reveal_approved: bool,
) -> tuple[str, RedactionMatchStatus, str | None]:
    normalized_kind = kind.upper()
    if rule.action == "suppress":
        return "", "applied", None
    if rule.action == "tokenize_placeholder":
        token = _token_placeholder(policy.token_namespace, kind, value)
        return _format_replacement(rule, kind=normalized_kind, token=token), "applied", token
    if rule.action == "review_gated_reveal":
        if reveal_approved:
            return str(value), "revealed", None
        return _format_replacement(rule, kind=normalized_kind, token=None), "requires_review", None
    return _format_replacement(rule, kind=normalized_kind, token=None), "applied", None


def _format_replacement(
    rule: RedactionPolicyRule,
    *,
    kind: str,
    token: str | None,
) -> str:
    template = rule.replacement_template
    if template is None:
        if rule.action == "tokenize_placeholder":
            template = "[TOKEN:{kind}:{token}]"
        elif rule.action == "review_gated_reveal":
            template = "[REVIEW_REQUIRED:{kind}]"
        elif rule.action == "suppress":
            template = ""
        else:
            template = "[REDACTED:{kind}]"
    return template.format(kind=kind, token=token or "")


def _token_placeholder(namespace: str, kind: str, value: Any) -> str:
    digest = hashlib.sha256(f"{namespace}:{kind}:{value}".encode("utf-8")).hexdigest()
    return digest[:12]


def _action_summary(matches: list[RedactionMatch]) -> dict[RedactionActionType, int]:
    summary: dict[RedactionActionType, int] = {}
    for match in matches:
        summary[match.action] = summary.get(match.action, 0) + 1
    return summary


def _preview(value: str) -> str:
    value = str(value)
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}...{value[-2:]}"
