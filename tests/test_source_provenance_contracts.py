import pytest

from ojtflow.core.contracts.artifacts import ExtractedTable, TableCell, TableExtractionProfile
from ojtflow.core.contracts.issue import BoundingBox, SourceLocation, TableCellReference, TextSpan


def test_source_location_supports_row_page_bbox_text_and_table_cell_refs() -> None:
    location = SourceLocation(
        row=3,
        column="value",
        field="value",
        page=2,
        bbox=BoundingBox(x=10, y=20, width=120, height=16),
        text_span=TextSpan(start=40, end=48),
        table_cell=TableCellReference(
            table_id="tbl_lab",
            sheet_name="Sheet1",
            row_index=2,
            column_index=4,
            column_label="value",
        ),
        source_ref="file:///var/uploads/lab.pdf",
    )

    assert location.page == 2
    assert location.bbox.width == 120
    assert location.table_cell.column_label == "value"


def test_text_span_rejects_reversed_offsets() -> None:
    with pytest.raises(ValueError):
        TextSpan(start=10, end=2)


def test_table_extraction_profile_preserves_cell_provenance() -> None:
    cell = TableCell(
        row_index=0,
        column_index=1,
        value="HbA1c",
        column_label="lab_name",
        location=SourceLocation(
            page=1,
            bbox=BoundingBox(x=72, y=144, width=80, height=18),
            table_cell=TableCellReference(table_id="tbl_1", row_index=0, column_index=1),
            source_ref="file:///var/uploads/lab.png",
        ),
        confidence=0.91,
    )
    table = ExtractedTable(
        table_id="tbl_1",
        source_kind="screenshot",
        row_count=1,
        column_count=2,
        cells=[cell],
    )
    profile = TableExtractionProfile(
        artifact_id="art_1",
        trace_id="trace_1",
        extractor="tesseract",
        source_kind="screenshot",
        tables=[table],
    )

    assert profile.tables[0].cells[0].location.bbox.height == 18
    assert profile.tables[0].source_kind == "screenshot"
