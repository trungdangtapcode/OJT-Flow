"""Storage consistency contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now

RepairCandidateKind = Literal[
    "missing_artifact_ref",
    "missing_dataset_record",
    "missing_dataset_file",
    "hash_mismatch",
    "dataset_hash_mismatch",
    "orphaned_dataset_record",
    "orphaned_file_artifact",
]
RepairSeverity = Literal["info", "warning", "error"]


class StorageConsistencyExample(ContractModel):
    """Sanitized example of a storage consistency problem."""

    workflow_id: str | None = None
    dataset_id: str | None = None
    label: str
    error_type: str


class StorageConsistencyReport(ContractModel):
    """Artifact reference and hash consistency report."""

    required: bool
    sampled_workflow_count: int = 0
    artifact_ref_count: int = 0
    dataset_record_count: int = 0
    checked_hash_count: int = 0
    checked_dataset_file_count: int = 0
    missing_count: int = 0
    missing_dataset_file_count: int = 0
    missing_dataset_record_count: int = 0
    hash_mismatch_count: int = 0
    dataset_hash_mismatch_count: int = 0
    unreferenced_dataset_record_count: int = 0
    examples: list[StorageConsistencyExample] = Field(default_factory=list)

    @property
    def is_consistent(self) -> bool:
        """Return whether checked artifact refs are present and hash-consistent."""

        return (
            self.missing_count == 0
            and self.missing_dataset_file_count == 0
            and self.missing_dataset_record_count == 0
            and self.hash_mismatch_count == 0
            and self.dataset_hash_mismatch_count == 0
        )


class StorageRepairCandidate(ContractModel):
    """Non-destructive storage repair candidate."""

    candidate_id: str
    kind: RepairCandidateKind
    severity: RepairSeverity
    recommended_action: str
    label: str
    workflow_id: str | None = None
    dataset_id: str | None = None
    artifact_ref_hash: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    destructive: bool = False


class StorageRepairPlan(ContractModel):
    """Sanitized repair plan for operator review."""

    required: bool
    dry_run: bool = True
    mutation_applied: bool = False
    sampled_workflow_count: int = 0
    dataset_record_count: int = 0
    scanned_file_count: int = 0
    total_candidate_count: int = 0
    returned_candidate_count: int = 0
    candidates: list[StorageRepairCandidate] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: utc_now().isoformat())


class StorageRepairMarker(ContractModel):
    """Runtime marker artifact proving candidates were reviewed for repair."""

    marker_id: str = Field(default_factory=lambda: new_id("repairmark"))
    marked_at: str = Field(default_factory=lambda: utc_now().isoformat())
    candidate_count: int = 0
    candidate_ids: list[str] = Field(default_factory=list)
    marker_ref_hash: str | None = None
    destructive: bool = False
