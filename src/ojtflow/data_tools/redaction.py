"""Deterministic sensitive text redaction preview."""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterable

from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.contracts.redaction import RedactionMatch, RedactionPreview
from ojtflow.core.policy.risk_rules import looks_sensitive_field


SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)"
)


def build_redaction_preview(
    text: str,
    *,
    data_format: DataFormat | None = None,
) -> RedactionPreview:
    """Return redacted text and match metadata without mutating source content."""

    matches: list[RedactionMatch] = []
    redacted_text = _redact_sensitive_csv_fields(
        text,
        matches=matches,
        enabled=data_format in {DataFormat.CSV, None},
    )
    redacted_text = _redact_regex_matches(
        redacted_text,
        matches=matches,
        rules=(
            ("ssn", SSN_PATTERN, "[REDACTED:SSN]", "SSN-like value detected."),
            ("email", EMAIL_PATTERN, "[REDACTED:EMAIL]", "Email address detected."),
            ("phone", PHONE_PATTERN, "[REDACTED:PHONE]", "Phone-like value detected."),
        ),
    )
    warnings = []
    if matches:
        warnings.append(
            "Potential sensitive text was found. Review redacted preview before "
            "sending content to external LLM or OCR providers."
        )
    return RedactionPreview(
        original_length=len(text),
        redacted_text=redacted_text,
        matches=matches,
        external_provider_block_recommended=bool(matches),
        warnings=warnings,
    )


def _redact_sensitive_csv_fields(
    text: str,
    *,
    matches: list[RedactionMatch],
    enabled: bool,
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
        if header and looks_sensitive_field(header)
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
            kind = _field_redaction_kind(header)
            replacement = f"[REDACTED:{kind.upper()}]"
            matches.append(
                RedactionMatch(
                    kind=kind,
                    value_preview=_preview(value),
                    replacement=replacement,
                    confidence=0.86,
                    reason=f"Column '{header}' is sensitive by field-name policy.",
                    location=SourceLocation(
                        row=row_index,
                        column=header,
                        field=header,
                    ),
                )
            )
            redacted_row[column_index] = replacement
        writer.writerow(redacted_row)
    return output.getvalue().rstrip("\n")


def _redact_regex_matches(
    text: str,
    *,
    matches: list[RedactionMatch],
    rules: Iterable[tuple[str, re.Pattern[str], str, str]],
) -> str:
    redacted = text
    for kind, pattern, replacement, reason in rules:
        pieces: list[str] = []
        cursor = 0
        found = False
        for match in pattern.finditer(redacted):
            found = True
            value = match.group(0)
            pieces.append(redacted[cursor:match.start()])
            pieces.append(replacement)
            matches.append(
                RedactionMatch(
                    kind=kind,
                    value_preview=_preview(value),
                    replacement=replacement,
                    confidence=0.9,
                    reason=reason,
                    start=match.start(),
                    end=match.end(),
                )
            )
            cursor = match.end()
        if found:
            pieces.append(redacted[cursor:])
            redacted = "".join(pieces)
    return redacted


def _field_redaction_kind(field_name: str):
    normalized = field_name.lower().replace("-", "_").replace(" ", "_")
    if "ssn" in normalized:
        return "ssn"
    if "patient" in normalized:
        return "patient_identifier"
    if "email" in normalized:
        return "email"
    if "phone" in normalized:
        return "phone"
    return "sensitive_field"


def _preview(value: str) -> str:
    value = str(value)
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}...{value[-2:]}"
