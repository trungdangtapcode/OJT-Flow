"""No-raw-PHI logging guard and scanner."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.logging import LogPhiFinding, LogPhiScanResult
from ojtflow.data_tools.redaction import build_redaction_preview


RAW_PHI_LOG_PLACEHOLDER = "[RAW_PHI_BLOCKED]"
REDACTED_VALUE_PREFIXES = (
    "[REDACTED:",
    "[TOKEN:",
    "[REVIEW_REQUIRED:",
    RAW_PHI_LOG_PLACEHOLDER,
)
SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?P<key>patient_id|patient|mrn|ssn|email|phone|diagnosis|dob)"
    r"\s*[:=]\s*(?P<quote>['\"]?)(?P<value>[^,'\"\s}\]]+)(?P=quote)",
    re.IGNORECASE,
)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)"
)

_LOG_RECORD_RESERVED = frozenset(logging.makeLogRecord({}).__dict__)


class NoRawPhiFilter(logging.Filter):
    """Sanitize log records before handlers format them."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)
        record.msg = sanitize_log_text(message)
        record.args = ()
        for key, value in list(record.__dict__.items()):
            if key in _LOG_RECORD_RESERVED or key.startswith("_"):
                continue
            record.__dict__[key] = sanitize_log_value(value)
        record.raw_phi_guard = True
        return True


def install_no_raw_phi_filter(logger: logging.Logger | None = None) -> None:
    """Install the no-raw-PHI filter on a logger and its current handlers."""

    target = logger or logging.getLogger()
    _add_filter_once(target)
    for handler in target.handlers:
        _add_filter_once(handler)


def sanitize_log_value(value: Any) -> Any:
    """Return a log-safe copy of a value."""

    if isinstance(value, str):
        return sanitize_log_text(value)
    if isinstance(value, dict):
        return {key: sanitize_log_value(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return tuple(sanitize_log_value(child) for child in value)
    if isinstance(value, list):
        return [sanitize_log_value(child) for child in value]
    return value


def sanitize_log_text(text: str) -> str:
    """Redact raw-PHI-like values from one log string."""

    if not text:
        return text
    redacted = _mask_sensitive_assignments(text)
    redacted = _redact_embedded_csv_payloads(redacted)
    if _looks_like_plain_csv(redacted):
        try:
            redacted = build_redaction_preview(redacted, action_override="mask").redacted_text
        except Exception:
            pass
    redacted = SSN_PATTERN.sub("[REDACTED:SSN]", redacted)
    redacted = EMAIL_PATTERN.sub("[REDACTED:EMAIL]", redacted)
    redacted = PHONE_PATTERN.sub("[REDACTED:PHONE]", redacted)
    return redacted


def scan_text_for_raw_phi(text: str, *, source_ref: str = "memory://log") -> LogPhiScanResult:
    """Scan log text for raw-PHI-like values."""

    findings: list[LogPhiFinding] = []
    for line_number, line in enumerate(text.splitlines() or [text], start=1):
        findings.extend(_line_findings(line, source_ref=source_ref, line_number=line_number))
    return LogPhiScanResult(
        source_ref=source_ref,
        finding_count=len(findings),
        findings=findings,
    )


def scan_paths_for_raw_phi(
    paths: list[Path],
    *,
    allow_missing: bool = False,
) -> list[LogPhiScanResult]:
    """Scan files or directories for raw-PHI-like log content."""

    results: list[LogPhiScanResult] = []
    for path in paths:
        if not path.exists():
            if allow_missing:
                continue
            results.append(
                LogPhiScanResult(
                    source_ref=str(path),
                    finding_count=1,
                    findings=[
                        LogPhiFinding(
                            source_ref=str(path),
                            line_number=0,
                            kind="missing_path",
                            reason="Configured log scan path does not exist.",
                        )
                    ],
                )
            )
            continue
        files = (
            [path]
            if path.is_file()
            else sorted(item for item in path.rglob("*") if item.is_file())
        )
        for file_path in files:
            if _should_skip_file(file_path):
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            result = scan_text_for_raw_phi(text, source_ref=str(file_path))
            if result.finding_count:
                results.append(result)
    return results


def _line_findings(
    line: str,
    *,
    source_ref: str,
    line_number: int,
) -> list[LogPhiFinding]:
    findings: list[LogPhiFinding] = []
    for match in SENSITIVE_ASSIGNMENT_PATTERN.finditer(line):
        if _is_redacted_value(match.group("value")):
            continue
        findings.append(
            LogPhiFinding(
                source_ref=source_ref,
                line_number=line_number,
                kind=match.group("key").lower(),
                value_preview=_preview(match.group("value")),
                reason="Sensitive key/value assignment found in log text.",
            )
        )
    for kind, pattern, reason in (
        ("ssn", SSN_PATTERN, "SSN-like value found in log text."),
        ("email", EMAIL_PATTERN, "Email address found in log text."),
        ("phone", PHONE_PATTERN, "Phone-like value found in log text."),
    ):
        for match in pattern.finditer(line):
            findings.append(
                LogPhiFinding(
                    source_ref=source_ref,
                    line_number=line_number,
                    kind=kind,
                    value_preview=_preview(match.group(0)),
                    reason=reason,
                )
            )
    return findings


def _is_redacted_value(value: str) -> bool:
    return any(value.startswith(prefix) for prefix in REDACTED_VALUE_PREFIXES)


def _mask_sensitive_assignments(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        kind = _kind_for_key(match.group("key"))
        return f"{match.group('key')}=[REDACTED:{kind}]"

    return SENSITIVE_ASSIGNMENT_PATTERN.sub(replace, text)


def _redact_embedded_csv_payloads(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    output: list[str] = []
    index = 0
    changed = False
    while index < len(lines):
        line = lines[index]
        if "=" not in line or "," not in line:
            output.append(line)
            index += 1
            continue
        prefix, candidate_header = line.split("=", 1)
        if not candidate_header or "," not in candidate_header:
            output.append(line)
            index += 1
            continue
        csv_lines = [candidate_header]
        cursor = index + 1
        while (
            cursor < len(lines)
            and "," in lines[cursor]
            and not _starts_assignment(lines[cursor])
        ):
            csv_lines.append(lines[cursor])
            cursor += 1
        if len(csv_lines) < 2:
            output.append(line)
            index += 1
            continue
        try:
            redacted_csv = build_redaction_preview(
                "\n".join(csv_lines),
                action_override="mask",
            ).redacted_text.splitlines()
        except Exception:
            output.append(line)
            index += 1
            continue
        output.append(f"{prefix}={redacted_csv[0]}")
        output.extend(redacted_csv[1:])
        changed = True
        index = cursor
    if not changed:
        return text
    trailing_newline = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + trailing_newline


def _looks_like_plain_csv(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    return (
        len(lines) >= 2
        and "," in lines[0]
        and "=" not in lines[0]
        and any("," in line for line in lines[1:])
    )


def _starts_assignment(line: str) -> bool:
    return bool(re.match(r"\s*[A-Za-z_][A-Za-z0-9_]*\s*[:=]", line))


def _kind_for_key(key: str) -> str:
    normalized = key.lower()
    if normalized in {"patient", "patient_id", "mrn"}:
        return "PATIENT_IDENTIFIER"
    if normalized == "dob":
        return "DATE_RELATED_TO_INDIVIDUAL"
    return normalized.upper()


def _add_filter_once(target: logging.Logger | logging.Handler) -> None:
    if any(isinstance(existing, NoRawPhiFilter) for existing in target.filters):
        return
    target.addFilter(NoRawPhiFilter())


def _should_skip_file(path: Path) -> bool:
    return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".db"}


def _preview(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}...{value[-2:]}"
