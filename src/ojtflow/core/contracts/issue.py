"""Validation, policy, and data-quality issue contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import Severity
from ojtflow.core.ids import new_id


class BoundingBox(ContractModel):
    """Page-relative bounding box for OCR/layout evidence."""

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    unit: str = "pt"


class TextSpan(ContractModel):
    """Character offsets in extracted text."""

    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_order(self) -> "TextSpan":
        if self.end < self.start:
            raise ValueError("TextSpan.end must be greater than or equal to start")
        return self


class TableCellReference(ContractModel):
    """Stable cell coordinate for extracted tables and spreadsheets."""

    table_id: str | None = None
    sheet_name: str | None = None
    row_index: int | None = Field(default=None, ge=0)
    column_index: int | None = Field(default=None, ge=0)
    row_label: str | None = None
    column_label: str | None = None


class SourceLocation(ContractModel):
    """Human and machine-readable location for an issue."""

    row: int | None = None
    column: str | None = None
    field: str | None = None
    page: int | None = Field(default=None, ge=1)
    bbox: BoundingBox | None = None
    text_span: TextSpan | None = None
    table_cell: TableCellReference | None = None
    source_ref: str | None = None


class Issue(ContractModel):
    """A precise issue that can drive review, UI, metrics, and audit."""

    issue_id: str = Field(default_factory=lambda: new_id("iss"))
    kind: str
    severity: Severity
    message: str
    location: SourceLocation | None = None
    suggested_action: str | None = None
    requires_review: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
