"""Artifact consistency scanner for local file-backed storage."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from ojtflow.core.contracts.storage_consistency import (
    StorageConsistencyExample,
    StorageConsistencyReport,
    StorageRepairCandidate,
    StorageRepairMarker,
    StorageRepairPlan,
)
from ojtflow.core.contracts.storage import DatasetRecord
from ojtflow.core.contracts.workflow import WorkflowState
from ojtflow.infrastructure.storage.file_refs import artifact_path_from_file_ref


@dataclass(frozen=True)
class WorkflowArtifactRef:
    """Internal artifact reference extracted from workflow state."""

    workflow_id: str
    label: str
    storage_ref: str
    expected_hash: str | None = None


def scan_workflow_artifacts(
    workflows: list[WorkflowState],
    *,
    data_dir: Path,
    required: bool,
    dataset_records: list[DatasetRecord] | None = None,
) -> StorageConsistencyReport:
    """Check sampled workflow and dataset artifact refs without exposing local paths."""

    if not required:
        return StorageConsistencyReport(
            required=False,
            sampled_workflow_count=0,
            artifact_ref_count=0,
        )

    roots = [data_dir / "datasets", data_dir / "outputs"]
    refs = workflow_artifact_refs(workflows)
    records = dataset_records or []
    records_by_ref = {record.storage_ref: record for record in records}
    workflow_ref_values = {ref.storage_ref for ref in refs}
    sampled_workflow_ids = {workflow.workflow_id for workflow in workflows}
    missing: list[StorageConsistencyExample] = []
    missing_dataset_records: list[StorageConsistencyExample] = []
    missing_dataset_files: list[StorageConsistencyExample] = []
    hash_mismatches: list[StorageConsistencyExample] = []
    dataset_hash_mismatches: list[StorageConsistencyExample] = []
    checked_hash_count = 0
    checked_dataset_file_count = 0
    unreferenced_dataset_record_count = 0

    for ref in refs:
        if records and ref.storage_ref not in records_by_ref:
            missing_dataset_records.append(_example(ref, "MissingDatasetRecord"))

        try:
            path = artifact_path_from_file_ref(ref.storage_ref, roots)
        except Exception as exc:
            missing.append(_example(ref, type(exc).__name__))
            continue

        expected_hash = _normalized_sha256(ref.expected_hash)
        if not expected_hash:
            continue
        checked_hash_count += 1
        if _file_sha256(path) != expected_hash:
            hash_mismatches.append(_example(ref, "HashMismatch"))

    for record in records:
        try:
            path = artifact_path_from_file_ref(record.storage_ref, roots)
        except Exception as exc:
            missing_dataset_files.append(_dataset_example(record, type(exc).__name__))
            continue
        checked_dataset_file_count += 1
        if _file_sha256(path) != _normalized_sha256(record.sha256):
            dataset_hash_mismatches.append(_dataset_example(record, "HashMismatch"))
        if (
            record.storage_ref not in workflow_ref_values
            and (record.workflow_id is None or record.workflow_id in sampled_workflow_ids)
        ):
            unreferenced_dataset_record_count += 1

    examples = [
        *missing[:2],
        *missing_dataset_records[:2],
        *missing_dataset_files[:2],
        *hash_mismatches[:2],
        *dataset_hash_mismatches[:2],
    ][:5]
    return StorageConsistencyReport(
        required=True,
        sampled_workflow_count=len(workflows),
        artifact_ref_count=len(refs),
        dataset_record_count=len(records),
        checked_hash_count=checked_hash_count,
        checked_dataset_file_count=checked_dataset_file_count,
        missing_count=len(missing),
        missing_dataset_file_count=len(missing_dataset_files),
        missing_dataset_record_count=len(missing_dataset_records),
        hash_mismatch_count=len(hash_mismatches),
        dataset_hash_mismatch_count=len(dataset_hash_mismatches),
        unreferenced_dataset_record_count=unreferenced_dataset_record_count,
        examples=examples,
    )


def build_storage_repair_plan(
    workflows: list[WorkflowState],
    *,
    data_dir: Path,
    required: bool,
    dataset_records: list[DatasetRecord] | None = None,
    max_candidates: int = 100,
) -> StorageRepairPlan:
    """Build a non-destructive repair plan for artifact and dataset drift."""

    if not required:
        return StorageRepairPlan(required=False)

    roots = [data_dir / "datasets", data_dir / "outputs"]
    refs = workflow_artifact_refs(workflows)
    records = dataset_records or []
    records_by_ref = {record.storage_ref: record for record in records}
    workflow_ref_values = {ref.storage_ref for ref in refs}
    sampled_workflow_ids = {workflow.workflow_id for workflow in workflows}
    candidates: list[StorageRepairCandidate] = []
    scanned_file_count = 0

    for ref in refs:
        if records and ref.storage_ref not in records_by_ref:
            candidates.append(
                _repair_candidate(
                    kind="missing_dataset_record",
                    severity="error",
                    recommended_action="recreate_dataset_metadata_or_investigate_ref",
                    label=ref.label,
                    workflow_id=ref.workflow_id,
                    storage_ref=ref.storage_ref,
                )
            )

        try:
            path = artifact_path_from_file_ref(ref.storage_ref, roots)
        except Exception as exc:
            candidates.append(
                _repair_candidate(
                    kind="missing_artifact_ref",
                    severity="error",
                    recommended_action="mark_workflow_artifact_ref_missing",
                    label=ref.label,
                    workflow_id=ref.workflow_id,
                    storage_ref=ref.storage_ref,
                    evidence={"error_type": type(exc).__name__},
                )
            )
            continue

        expected_hash = _normalized_sha256(ref.expected_hash)
        if not expected_hash:
            continue
        actual_hash = _file_sha256(path)
        if actual_hash != expected_hash:
            candidates.append(
                _repair_candidate(
                    kind="hash_mismatch",
                    severity="error",
                    recommended_action="quarantine_artifact_for_review",
                    label=ref.label,
                    workflow_id=ref.workflow_id,
                    storage_ref=ref.storage_ref,
                    evidence={
                        "expected_hash_prefix": expected_hash[:12],
                        "actual_hash_prefix": actual_hash[:12],
                    },
                )
            )

    for record in records:
        try:
            path = artifact_path_from_file_ref(record.storage_ref, roots)
        except Exception as exc:
            candidates.append(
                _repair_candidate(
                    kind="missing_dataset_file",
                    severity="error",
                    recommended_action="mark_dataset_row_missing_file",
                    label=f"dataset:{record.source_kind}",
                    workflow_id=record.workflow_id,
                    dataset_id=record.dataset_id,
                    storage_ref=record.storage_ref,
                    evidence={"error_type": type(exc).__name__},
                )
            )
            continue

        actual_hash = _file_sha256(path)
        expected_hash = _normalized_sha256(record.sha256)
        if expected_hash and actual_hash != expected_hash:
            candidates.append(
                _repair_candidate(
                    kind="dataset_hash_mismatch",
                    severity="error",
                    recommended_action="quarantine_dataset_row_for_review",
                    label=f"dataset:{record.source_kind}",
                    workflow_id=record.workflow_id,
                    dataset_id=record.dataset_id,
                    storage_ref=record.storage_ref,
                    evidence={
                        "expected_hash_prefix": expected_hash[:12],
                        "actual_hash_prefix": actual_hash[:12],
                    },
                )
            )

        if (
            record.storage_ref not in workflow_ref_values
            and (record.workflow_id is None or record.workflow_id in sampled_workflow_ids)
        ):
            candidates.append(
                _repair_candidate(
                    kind="orphaned_dataset_record",
                    severity="warning",
                    recommended_action="mark_orphaned_dataset_row",
                    label=f"dataset:{record.source_kind}",
                    workflow_id=record.workflow_id,
                    dataset_id=record.dataset_id,
                    storage_ref=record.storage_ref,
                    evidence={
                        "byte_size": record.byte_size,
                        "declared_format": record.declared_format,
                        "detected_format": record.detected_format,
                    },
                )
            )

    known_file_refs = {ref.storage_ref for ref in refs}
    known_file_refs.update(record.storage_ref for record in records)
    for directory_kind, path in _artifact_files(data_dir):
        scanned_file_count += 1
        storage_ref = path.resolve().as_uri()
        if storage_ref in known_file_refs:
            continue
        candidates.append(
            _repair_candidate(
                kind="orphaned_file_artifact",
                severity="warning",
                recommended_action="mark_orphaned_file_artifact",
                label=f"file:{directory_kind}",
                storage_ref=storage_ref,
                evidence={
                    "directory_kind": directory_kind,
                    "extension": path.suffix.lower(),
                    "byte_size": path.stat().st_size,
                },
            )
        )

    bounded_candidates = candidates[: max(0, max_candidates)]
    return StorageRepairPlan(
        required=True,
        sampled_workflow_count=len(workflows),
        dataset_record_count=len(records),
        scanned_file_count=scanned_file_count,
        total_candidate_count=len(candidates),
        returned_candidate_count=len(bounded_candidates),
        candidates=bounded_candidates,
    )


def write_storage_repair_marker(
    plan: StorageRepairPlan,
    *,
    data_dir: Path,
) -> StorageRepairMarker:
    """Persist a sanitized repair marker without changing data rows or artifacts."""

    marker = StorageRepairMarker(
        candidate_count=plan.returned_candidate_count,
        candidate_ids=[candidate.candidate_id for candidate in plan.candidates],
    )
    marker_dir = data_dir / "repair_markers" / "storage_consistency"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker_path = marker_dir / f"{marker.marker_id}.json"
    marker.marker_ref_hash = _ref_hash(marker_path.resolve().as_uri())
    payload = {
        "marker": marker.model_dump(mode="json"),
        "plan": plan.model_dump(mode="json"),
    }
    marker_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return marker


def workflow_artifact_refs(workflows: list[WorkflowState]) -> list[WorkflowArtifactRef]:
    """Extract unique artifact refs from workflow state."""

    refs: list[WorkflowArtifactRef] = []
    seen: set[tuple[str, str]] = set()

    def add(
        workflow_id: str,
        label: str,
        storage_ref: str | None,
        expected_hash: str | None = None,
    ) -> None:
        if not storage_ref:
            return
        key = (workflow_id, storage_ref)
        if key in seen:
            return
        seen.add(key)
        refs.append(
            WorkflowArtifactRef(
                workflow_id=workflow_id,
                label=label,
                storage_ref=storage_ref,
                expected_hash=expected_hash,
            )
        )

    for workflow in workflows:
        if workflow.input:
            add(
                workflow.workflow_id,
                "input",
                workflow.input.dataset_ref,
                workflow.input.input_hash,
            )
        extracted_ref = workflow.handoff_context.get("extracted_dataset_ref")
        if isinstance(extracted_ref, str):
            add(workflow.workflow_id, "extracted_dataset", extracted_ref)
        for step in workflow.steps:
            add(workflow.workflow_id, f"step:{step.name}", step.output_ref)
        output = workflow.output.transformation if workflow.output else None
        if output:
            add(
                workflow.workflow_id,
                "output",
                output.output_ref,
                output.output_hash,
            )
    return refs


def _example(ref: WorkflowArtifactRef, error_type: str) -> StorageConsistencyExample:
    return StorageConsistencyExample(
        workflow_id=ref.workflow_id,
        label=ref.label,
        error_type=error_type,
    )


def _dataset_example(
    record: DatasetRecord,
    error_type: str,
) -> StorageConsistencyExample:
    return StorageConsistencyExample(
        workflow_id=record.workflow_id,
        dataset_id=record.dataset_id,
        label=f"dataset:{record.source_kind}",
        error_type=error_type,
    )


def _repair_candidate(
    *,
    kind: str,
    severity: str,
    recommended_action: str,
    label: str,
    workflow_id: str | None = None,
    dataset_id: str | None = None,
    storage_ref: str | None = None,
    evidence: dict | None = None,
) -> StorageRepairCandidate:
    artifact_ref_hash = _ref_hash(storage_ref) if storage_ref else None
    candidate_seed = "|".join(
        value or "-"
        for value in [
            kind,
            workflow_id,
            dataset_id,
            label,
            artifact_ref_hash,
        ]
    )
    return StorageRepairCandidate(
        candidate_id=f"repair_{sha256(candidate_seed.encode('utf-8')).hexdigest()[:16]}",
        kind=kind,
        severity=severity,
        recommended_action=recommended_action,
        label=label,
        workflow_id=workflow_id,
        dataset_id=dataset_id,
        artifact_ref_hash=artifact_ref_hash,
        evidence=evidence or {},
        destructive=False,
    )


def _artifact_files(data_dir: Path) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for directory_kind in ["datasets", "outputs"]:
        root = data_dir / directory_kind
        if not root.exists() or not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                files.append((directory_kind, path))
    return files


def _ref_hash(storage_ref: str) -> str:
    return sha256(storage_ref.encode("utf-8")).hexdigest()


def _normalized_sha256(value: str | None) -> str | None:
    if not value:
        return None
    return value.removeprefix("sha256:")


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
