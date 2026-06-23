import pytest

from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.errors import UnsupportedUploadError
from ojtflow.data_tools.extract import sanitize_upload_filename
from ojtflow.data_tools.parse import parse_data


def test_sanitize_upload_filename_rejects_path_traversal() -> None:
    with pytest.raises(UnsupportedUploadError):
        sanitize_upload_filename("../../lab.pdf")

    with pytest.raises(UnsupportedUploadError):
        sanitize_upload_filename("..\\lab.pdf")


def test_markdown_table_parse_preserves_rows() -> None:
    parsed = parse_data(
        "| lab_name | value | unit |\n| --- | --- | --- |\n| HbA1c | 7.4 | % |\n",
        DataFormat.MARKDOWN,
        source_ref="memory://fixture",
    )

    assert parsed.records == [
        {"lab_name": "HbA1c", "value": "7.4", "unit": "%", "_source_row": 2}
    ]
