from pathlib import Path

from ojtflow.core.contracts.enums import DataFormat
from ojtflow.data_tools.detect import detect_format
from ojtflow.data_tools.parse import parse_data
from ojtflow.data_tools.profile import profile_data
from ojtflow.data_tools.validate import validate_against_schema
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository


ROOT = Path(__file__).resolve().parents[1]


def test_csv_parse_profile_and_validate_messy_lab_fixture() -> None:
    text = (ROOT / "data/fixtures/structured/lab_results_messy.csv").read_text()
    detection = detect_format(text)
    assert detection.format == DataFormat.CSV

    parsed = parse_data(text, detection.format, source_ref="memory://fixture")
    profile = profile_data(parsed)
    schema = StaticKnowledgeRepository(ROOT / "knowledge").get_schema("lab_result_v1")
    report = validate_against_schema(parsed, profile, schema)

    assert profile.row_count == 3
    assert report.requires_review is True
    assert {issue.kind for issue in report.issues} >= {
        "missing_value",
        "date_format_inconsistency",
        "possible_phi",
    }


def test_prompt_injection_cell_is_flagged_as_data() -> None:
    text = (ROOT / "data/fixtures/prompt_injection/injection_cell.csv").read_text()
    parsed = parse_data(text, DataFormat.CSV, source_ref="memory://fixture")
    profile = profile_data(parsed)
    schema = StaticKnowledgeRepository(ROOT / "knowledge").get_schema("lab_result_v1")
    report = validate_against_schema(parsed, profile, schema)

    assert any(issue.kind == "prompt_injection_pattern" for issue in report.issues)

