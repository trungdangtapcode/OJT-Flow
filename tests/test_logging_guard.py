import io
import logging

from ojtflow.observability.logging_guard import (
    NoRawPhiFilter,
    sanitize_log_text,
    scan_paths_for_raw_phi,
    scan_text_for_raw_phi,
)


def test_no_raw_phi_filter_redacts_message_args_and_extra_fields() -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(NoRawPhiFilter())
    formatter = logging.Formatter("%(message)s %(patient_context)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger("ojtflow.tests.logging_guard")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addFilter(NoRawPhiFilter())

    logger.info(
        "failed row patient_id=%s ssn=%s",
        "P001",
        "123-45-6789",
        extra={"patient_context": "email=patient@example.com"},
    )

    output = stream.getvalue()
    assert "P001" not in output
    assert "123-45-6789" not in output
    assert "patient@example.com" not in output
    assert "patient_id=[REDACTED:PATIENT_IDENTIFIER]" in output
    assert "[REDACTED:SSN]" in output
    assert "email=[REDACTED:EMAIL]" in output


def test_sanitize_log_text_handles_csv_and_key_value_shapes() -> None:
    sanitized = sanitize_log_text(
        "payload=patient_id,ssn\nP001,123-45-6789\n diagnosis=diabetes"
    )

    assert "P001" not in sanitized
    assert "123-45-6789" not in sanitized
    assert "diabetes" not in sanitized
    assert "[REDACTED:PATIENT_IDENTIFIER]" in sanitized
    assert "[REDACTED:SSN]" in sanitized
    assert "diagnosis=[REDACTED:DIAGNOSIS]" in sanitized


def test_log_scanner_detects_raw_phi_and_ignores_redacted_placeholders(tmp_path) -> None:
    unsafe = tmp_path / "unsafe.log"
    safe = tmp_path / "safe.log"
    unsafe.write_text("request patient_id=P001 ssn=123-45-6789\n", encoding="utf-8")
    safe.write_text(
        "request patient_id=[REDACTED:PATIENT_IDENTIFIER] ssn=[REDACTED:SSN]\n",
        encoding="utf-8",
    )

    unsafe_result = scan_text_for_raw_phi(unsafe.read_text(encoding="utf-8"))
    assert unsafe_result.finding_count >= 2

    results = scan_paths_for_raw_phi([tmp_path])
    assert [result.source_ref for result in results] == [str(unsafe)]
