"""Storage contracts."""

from __future__ import annotations

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.ids import new_id


class DatasetRecord(ContractModel):
    """Stored input or output dataset metadata."""

    dataset_id: str = Field(default_factory=lambda: new_id("ds"))
    workflow_id: str | None = None
    source_kind: str = "inline"
    declared_format: str | None = None
    detected_format: str | None = None
    byte_size: int
    sha256: str
    storage_ref: str

