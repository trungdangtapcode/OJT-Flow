import type { RetrievalComparisonReportInput } from "./retrieval-comparison-types";

export function comparisonDeltaReport(comparison: RetrievalComparisonReportInput) {
  return {
    candidates: comparison.candidateDelta,
    hits: comparison.hitDelta,
    quality_score: comparison.qualityScoreDelta,
    quality_warnings: comparison.qualityWarningDelta,
    source_diversity: {
      candidate_sources: comparison.sourceDiversityComparison.candidateSourceDelta,
      duplicate_selected_sources:
        comparison.sourceDiversityComparison.duplicateSelectedSourceDelta,
      selected_sources: comparison.sourceDiversityComparison.selectedSourceDelta,
    },
    warnings: comparison.warningDelta,
  };
}

export function comparisonDimensionReports(
  comparison: RetrievalComparisonReportInput,
) {
  return {
    coverage: comparisonChangeSetReport(comparison.coverageComparison),
    query_aspects: comparisonChangeSetReport(comparison.queryAspectComparison),
    concept_grounding: comparisonChangeSetReport(
      comparison.conceptGroundingComparison,
    ),
    quality_signals: comparisonChangeSetReport(comparison.qualitySignalComparison),
    facets: comparison.facetComparisons.map((facet) => ({
      field: facet.field,
      label: facet.label,
      active_count: facet.activeCount,
      baseline_count: facet.baselineCount,
      added_values: facet.addedValues,
      removed_values: facet.removedValues,
      retained_values: facet.retainedValues,
    })),
  };
}

function comparisonChangeSetReport<T>({
  added,
  improved,
  regressed,
  removed,
  retained,
}: {
  added: T[];
  improved?: T[];
  regressed?: T[];
  removed: T[];
  retained: T[];
}) {
  return {
    added,
    improved: improved ?? [],
    regressed: regressed ?? [],
    removed,
    retained,
  };
}
