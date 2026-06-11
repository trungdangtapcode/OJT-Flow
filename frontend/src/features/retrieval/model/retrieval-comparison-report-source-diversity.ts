import type { RetrievalComparisonReportInput } from "./retrieval-comparison-types";

export function comparisonSourceDiversityReport(
  comparison: RetrievalComparisonReportInput,
) {
  return {
    active: sourceDiversityRunReport(
      comparison.sourceDiversityComparison.active,
      comparison.sourceDiversityComparison.activeSelectedSourceIds,
    ),
    baseline: sourceDiversityRunReport(
      comparison.sourceDiversityComparison.baseline,
      comparison.sourceDiversityComparison.baselineSelectedSourceIds,
    ),
    added_source_ids: comparison.sourceDiversityComparison.addedSourceIds,
    removed_source_ids: comparison.sourceDiversityComparison.removedSourceIds,
    retained_source_ids: comparison.sourceDiversityComparison.retainedSourceIds,
    source_overlap_ratio: comparison.sourceDiversityComparison.sourceOverlapRatio,
    selection_mode_changed:
      comparison.sourceDiversityComparison.selectionModeChanged,
    lambda_changed: comparison.sourceDiversityComparison.lambdaChanged,
  };
}

function sourceDiversityRunReport(
  run: RetrievalComparisonReportInput["sourceDiversityComparison"]["active"],
  selectedSourceIds: string[],
) {
  return {
    candidate_source_count: run.candidateSourceCount,
    duplicate_selected_source_count: run.duplicateSelectedSourceCount,
    enabled: run.enabled,
    lambda: run.lambda,
    selected_source_count: run.selectedSourceCount,
    selection_mode: run.selectionMode,
    selected_source_ids: selectedSourceIds,
  };
}
