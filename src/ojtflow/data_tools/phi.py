"""Rule-based PHI and sensitive-data classification."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qsl, urlparse

from ojtflow.core.contracts.data import ParsedData
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.contracts.phi import (
    PhiCategory,
    PhiClassification,
    PhiClassificationPolicy,
    PhiFinding,
    PhiPatternRule,
    PhiTargetType,
)
from ojtflow.core.policy.phi_policy import (
    default_phi_policy,
    match_phi_field_rule,
    normalize_policy_text,
)


ALWAYS_SENSITIVE_URL_KEYS = {
    "access_token",
    "auth",
    "bearer",
    "beneficiary",
    "birth_date",
    "code_verifier",
    "date_of_birth",
    "dob",
    "email",
    "id_token",
    "medical_record",
    "member_id",
    "mrn",
    "patient_id",
    "person_id",
    "phone",
    "secret",
    "session",
    "ssn",
    "subject_id",
    "token",
}

CONTEXT_SENSITIVE_URL_KEYS = {
    "account",
    "first_name",
    "full_name",
    "last_name",
    "member",
    "name",
    "patient",
    "person",
    "subject",
}

SENSITIVE_URL_ROUTE_KEYS = {
    "account",
    "member",
    "patient",
    "person",
    "subject",
}


def classify_parsed_data(
    parsed: ParsedData,
    *,
    policy: PhiClassificationPolicy | None = None,
) -> PhiClassification:
    """Classify PHI signals in parsed data records or document text."""

    if parsed.records:
        return classify_records(
            parsed.records,
            source_ref=parsed.source_ref,
            target_type="row",
            policy=policy,
        )
    text = _text_from_content(parsed.content)
    return classify_text(
        text,
        source_ref=parsed.source_ref,
        target_type="document",
        data_format=parsed.format,
        policy=policy,
    )


def classify_records(
    records: list[dict[str, Any]],
    *,
    source_ref: str | None = None,
    target_type: PhiTargetType = "row",
    policy: PhiClassificationPolicy | None = None,
) -> PhiClassification:
    """Classify PHI signals in structured records."""

    active_policy = policy or default_phi_policy()
    findings: list[PhiFinding] = []
    for row_index, record in enumerate(records, start=1):
        source_row = int(record.get("_source_row", row_index))
        for field, value in record.items():
            if field == "_source_row":
                continue
            field_rule = match_phi_field_rule(field, policy=active_policy)
            if field_rule:
                findings.append(
                    PhiFinding(
                        target_type="field",
                        category=field_rule.category,
                        kind=field_rule.kind,
                        field=field,
                        value_preview=_preview(value),
                        confidence=field_rule.confidence,
                        reason=field_rule.reason,
                        source_ref=source_ref,
                        location=SourceLocation(
                            row=source_row,
                            column=field,
                            field=field,
                            source_ref=source_ref,
                        ),
                    )
                )
            findings.extend(
                _regex_findings(
                    str(value),
                    target_type=target_type,
                    source_ref=source_ref,
                    field=field,
                    location=SourceLocation(
                        row=source_row,
                        column=field,
                        field=field,
                        source_ref=source_ref,
                    ),
                    policy=active_policy,
                )
            )
    return _classification(
        target_type=target_type,
        source_ref=source_ref,
        findings=findings,
        policy=active_policy,
    )


def classify_text(
    text: str,
    *,
    source_ref: str | None = None,
    target_type: PhiTargetType = "document",
    data_format: DataFormat | None = None,
    policy: PhiClassificationPolicy | None = None,
) -> PhiClassification:
    """Classify PHI signals in text, including CSV-like text when available."""

    active_policy = policy or default_phi_policy()
    findings: list[PhiFinding] = []
    if data_format in {DataFormat.CSV, None} and "," in text and "\n" in text:
        findings.extend(
            _csv_field_findings(
                text,
                source_ref=source_ref,
                policy=active_policy,
            )
        )
    findings.extend(
        _regex_findings(
            text,
            target_type=target_type,
            source_ref=source_ref,
            field=None,
            location=None,
            policy=active_policy,
        )
    )
    return _classification(
        target_type=target_type,
        source_ref=source_ref,
        findings=findings,
        policy=active_policy,
    )


def _csv_field_findings(
    text: str,
    *,
    source_ref: str | None,
    policy: PhiClassificationPolicy,
) -> list[PhiFinding]:
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return []
    if len(rows) < 2 or not rows[0]:
        return []
    headers = [header.strip() for header in rows[0]]
    findings: list[PhiFinding] = []
    for column_index, header in enumerate(headers):
        if not header:
            continue
        field_rule = match_phi_field_rule(header, policy=policy)
        if not field_rule:
            continue
        for row_index, row in enumerate(rows[1:], start=2):
            value = row[column_index] if column_index < len(row) else ""
            if value in ("", None):
                continue
            findings.append(
                PhiFinding(
                    target_type="field",
                    category=field_rule.category,
                    kind=field_rule.kind,
                    field=header,
                    value_preview=_preview(value),
                    confidence=field_rule.confidence,
                    reason=field_rule.reason,
                    source_ref=source_ref,
                    location=SourceLocation(
                        row=row_index,
                        column=header,
                        field=header,
                        source_ref=source_ref,
                    ),
                )
            )
    return findings


def _regex_findings(
    text: str,
    *,
    target_type: PhiTargetType,
    source_ref: str | None,
    field: str | None,
    location: SourceLocation | None,
    policy: PhiClassificationPolicy,
) -> list[PhiFinding]:
    findings: list[PhiFinding] = []
    for rule, pattern in _regex_rules(policy):
        for match in pattern.finditer(text):
            if rule.kind == "url" and not _url_contains_sensitive_identifier(match.group(0)):
                continue
            findings.append(
                PhiFinding(
                    target_type=target_type,
                    category=rule.category,
                    kind=rule.kind,
                    field=field,
                    value_preview=_preview(match.group(0)),
                    confidence=rule.confidence,
                    reason=rule.reason,
                    source_ref=source_ref,
                    location=location,
                )
            )
    return findings


def _url_contains_sensitive_identifier(value: str) -> bool:
    cleaned = value.strip(" \t\r\n\"'<>[]{}()")
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    path_tokens = [
        token
        for token in _normalize(parsed.path).replace(".", "_").split("/")
        for token in token.split("_")
        if token
    ]
    if _path_contains_sensitive_identifier(path_tokens):
        return True
    for key, item in parse_qsl(parsed.query, keep_blank_values=True):
        normalized_key = _normalize(key)
        normalized_value = str(item).strip()
        if _is_always_sensitive_url_key(normalized_key):
            return True
        if _is_context_sensitive_url_key(normalized_key) and _looks_like_person_name(
            normalized_value
        ):
            return True
        if normalized_key in {"code", "url", "format", "_format"}:
            continue
        if normalized_key and normalized_value and _looks_like_secret(normalized_value):
            return True
    return False


def _path_contains_sensitive_identifier(path_tokens: list[str]) -> bool:
    if not set(path_tokens) & SENSITIVE_URL_ROUTE_KEYS:
        return False
    return any(_looks_like_url_identifier(token) for token in path_tokens)


def _is_always_sensitive_url_key(normalized_key: str) -> bool:
    if normalized_key in ALWAYS_SENSITIVE_URL_KEYS:
        return True
    key_tokens = {
        token
        for token in normalized_key.replace(".", "_").replace("/", "_").split("_")
        if token
    }
    return bool(key_tokens & ALWAYS_SENSITIVE_URL_KEYS)


def _is_context_sensitive_url_key(normalized_key: str) -> bool:
    if normalized_key in CONTEXT_SENSITIVE_URL_KEYS:
        return True
    key_tokens = {
        token
        for token in normalized_key.replace(".", "_").replace("/", "_").split("_")
        if token
    }
    return bool(key_tokens & CONTEXT_SENSITIVE_URL_KEYS)


def _looks_like_secret(value: str) -> bool:
    compact = value.replace("-", "").replace("_", "")
    return len(compact) >= 24 and compact.isalnum()


def _looks_like_url_identifier(value: str) -> bool:
    compact = value.replace("-", "").replace("_", "")
    return (
        len(compact) >= 6
        and any(char.isdigit() for char in compact)
        and compact.isalnum()
    )


def _looks_like_person_name(value: str) -> bool:
    normalized = " ".join(_normalize(value).replace("-", " ").replace("_", " ").split())
    if not normalized:
        return False
    parts = normalized.split()
    if len(parts) < 2:
        return False
    return all(part.isalpha() and len(part) >= 2 for part in parts[:4])


def _classification(
    *,
    target_type: PhiTargetType,
    source_ref: str | None,
    findings: list[PhiFinding],
    policy: PhiClassificationPolicy,
) -> PhiClassification:
    categories = _unique([finding.category for finding in findings])
    risk_level = _risk_level(findings, policy)
    return PhiClassification(
        target_type=target_type,
        source_ref=source_ref,
        risk_level=risk_level,
        finding_count=len(findings),
        categories=categories,
        findings=findings,
        requires_review=risk_level in set(policy.review_risk_levels),
        external_provider_block_recommended=(
            risk_level in set(policy.external_provider_block_risk_levels)
        ),
    )


def _regex_rules(
    policy: PhiClassificationPolicy,
) -> Iterable[tuple[PhiPatternRule, Any]]:
    import re

    for rule in policy.pattern_rules:
        yield rule, re.compile(rule.pattern, re.IGNORECASE)


def _risk_level(
    findings: list[PhiFinding],
    policy: PhiClassificationPolicy,
) -> str:
    if not findings:
        return "none"
    high_risk_categories = set(policy.high_risk_categories)
    medium_risk_categories = set(policy.medium_risk_categories)
    if any(finding.category in high_risk_categories for finding in findings):
        return "high"
    if any(finding.category in medium_risk_categories for finding in findings):
        return "medium"
    return "low"


def _text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        raw = content.get("raw")
        if isinstance(raw, str):
            return raw
    return str(content or "")


def _normalize(value: str) -> str:
    return normalize_policy_text(value)


def _preview(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    if len(text) <= 4:
        return "*" * len(text)
    return f"{text[:2]}...{text[-2:]}"


def _unique(values: list[PhiCategory]) -> list[PhiCategory]:
    seen: set[PhiCategory] = set()
    result: list[PhiCategory] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
