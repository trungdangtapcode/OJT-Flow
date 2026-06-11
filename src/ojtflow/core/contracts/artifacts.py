"""Uploaded artifact and document extraction contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.issue import SourceLocation
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


ArtifactSource = Literal["upload", "clipboard", "assistant_attachment", "api"]
RetentionAction = Literal["retain", "review", "delete_after_expiry"]
ArtifactAccessAction = Literal["download", "export_metadata", "view_metadata"]
ExtractionStepStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]
TableSourceKind = Literal["pdf", "excel", "csv", "screenshot", "image", "html", "unknown"]
PdfScanLikelihood = Literal["digital", "scanned", "mixed", "unknown"]
ExtractionQualityLevel = Literal["good", "review", "poor"]


class ArtifactRetentionPolicy(ContractModel):
    """Retention policy stamped onto an uploaded artifact at intake time."""

    policy_id: str = "default_upload_retention_v0"
    sensitivity_class: str = "unknown"
    action: RetentionAction = "review"
    retain_until: str | None = None
    reason: str = "Default local artifact retention; tenant policy can override later."
    mode: str | None = None
    source: ArtifactSource | None = None
    tenant_id: str | None = None


class ArtifactRetentionRule(ContractModel):
    """Configurable rule for upload retention policy resolution."""

    rule_id: str
    mode: str | None = None
    tenant_id: str | None = None
    source: ArtifactSource | None = None
    sensitivity_class: str | None = None
    action: RetentionAction = "review"
    retain_days: int | None = Field(default=None, ge=0)
    reason: str = ""


class UploadedArtifact(ContractModel):
    """Durable metadata for a user-supplied file or clipboard payload."""

    artifact_id: str = Field(default_factory=lambda: new_id("art"))
    owner_user_id: str
    filename: str
    mime_type: str
    extension: str
    byte_size: int = Field(ge=0)
    sha256: str
    source: ArtifactSource = "upload"
    storage_ref: str
    dataset_id: str | None = None
    duplicate_of_artifact_id: str | None = None
    retention_policy: ArtifactRetentionPolicy = Field(default_factory=ArtifactRetentionPolicy)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    @property
    def is_duplicate(self) -> bool:
        return self.duplicate_of_artifact_id is not None


class ArtifactAccessEvent(ContractModel):
    """Append-only audit event for artifact metadata/export/download access."""

    event_id: str = Field(default_factory=lambda: new_id("artevt"))
    artifact_id: str
    owner_user_id: str
    actor_user_id: str
    action: ArtifactAccessAction
    request_id: str | None = None
    timestamp: str = Field(default_factory=lambda: utc_now().isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractionStepTrace(ContractModel):
    """One extractor attempt within a parsing pipeline trace."""

    step_id: str = Field(default_factory=lambda: new_id("xstep"))
    extractor: str
    status: ExtractionStepStatus = "pending"
    started_at: str | None = None
    completed_at: str | None = None
    summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    input_ref: str | None = None
    output_ref: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsingPipelineTrace(ContractModel):
    """Source-linked trace for document extraction and text preparation."""

    trace_id: str = Field(default_factory=lambda: new_id("trace"))
    artifact_id: str
    owner_user_id: str
    job_id: str | None = None
    source_format: str
    requested_extractor: str
    extractor_chosen: str
    fallback_path: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    char_count: int = Field(default=0, ge=0)
    token_count_estimate: int = Field(default=0, ge=0)
    confidence: float = Field(default=1.0, ge=0, le=1)
    text_sha256: str | None = None
    text_storage_ref: str | None = None
    text_dataset_id: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    steps: list[ExtractionStepTrace] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: str = Field(default_factory=lambda: utc_now().isoformat())
    completed_at: str | None = None


class WorkbookSheetProfile(ContractModel):
    """Sheet-level spreadsheet profile for workbook intake."""

    sheet_name: str
    sheet_index: int = Field(ge=0)
    row_count: int = Field(default=0, ge=0)
    column_count: int = Field(default=0, ge=0)
    hidden_state: str = "visible"
    header_row: int | None = Field(default=None, ge=1)
    headers: list[str] = Field(default_factory=list)
    merged_cell_ranges: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class WorkbookParsingProfile(ContractModel):
    """Workbook-level spreadsheet profile."""

    filename: str
    source_format: str
    sheet_count: int = Field(default=0, ge=0)
    visible_sheet_count: int = Field(default=0, ge=0)
    hidden_sheet_count: int = Field(default=0, ge=0)
    sheets: list[WorkbookSheetProfile] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PdfContentProfile(ContractModel):
    """PDF text/image profile used to detect scanned documents."""

    filename: str
    page_count: int = Field(default=0, ge=0)
    digital_text_pages: int = Field(default=0, ge=0)
    image_pages: int = Field(default=0, ge=0)
    image_only_pages: int = Field(default=0, ge=0)
    scan_likelihood: PdfScanLikelihood = "unknown"
    requires_ocr: bool = False
    analyzer: str = "unavailable"
    warnings: list[str] = Field(default_factory=list)


class ExtractionQualityReport(ContractModel):
    """Quality score and review guidance for extracted document text."""

    score: float = Field(ge=0, le=1)
    level: ExtractionQualityLevel
    requires_review: bool = False
    factors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ExtractionExplanation(ContractModel):
    """User-facing explanation of extraction coverage and caveats."""

    read: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    needs_review: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class DocumentIntelligenceProfile(ContractModel):
    """Document analysis profile attached to a parse trace."""

    source_format: str
    workbook: WorkbookParsingProfile | None = None
    pdf: PdfContentProfile | None = None
    quality: ExtractionQualityReport
    explanation: ExtractionExplanation


class TableCell(ContractModel):
    """One extracted table cell with provenance."""

    row_index: int = Field(ge=0)
    column_index: int = Field(ge=0)
    value: str = ""
    row_label: str | None = None
    column_label: str | None = None
    location: SourceLocation | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedTable(ContractModel):
    """Format-neutral extracted table with source-linked cell coordinates."""

    table_id: str = Field(default_factory=lambda: new_id("tbl"))
    artifact_id: str | None = None
    trace_id: str | None = None
    source_kind: TableSourceKind = "unknown"
    title: str | None = None
    page: int | None = Field(default=None, ge=1)
    sheet_name: str | None = None
    row_count: int = Field(default=0, ge=0)
    column_count: int = Field(default=0, ge=0)
    cells: list[TableCell] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TableExtractionProfile(ContractModel):
    """Summary of tables found during document extraction."""

    profile_id: str = Field(default_factory=lambda: new_id("tblprof"))
    artifact_id: str | None = None
    trace_id: str | None = None
    extractor: str
    source_kind: TableSourceKind = "unknown"
    tables: list[ExtractedTable] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)
