import type {
  RetrievalComparisonDiagnosis,
  RetrievalComparisonDiagnosticInput,
} from "./retrieval-comparison-types";

export function comparisonSourceDiagnosis(
  comparison: RetrievalComparisonDiagnosticInput,
): RetrievalComparisonDiagnosis[] {
  const diagnosis: RetrievalComparisonDiagnosis[] = [];

  if (
    comparison.facetComparisons.some(
      (facet) => facet.addedValues.length || facet.removedValues.length,
    )
  ) {
    diagnosis.push({
      code: "facet_coverage_changed",
      message:
        "Selected-hit source type, clinical domain, standard, or trust coverage changed.",
      severity: "warning",
    });
  }

  if (comparison.topSourceChanged) {
    diagnosis.push({
      code: "top_source_changed",
      message: "The highest-ranked source changed between runs.",
      severity: "warning",
    });
  }

  if (
    comparison.sourceDiversityComparison.selectionModeChanged ||
    comparison.sourceDiversityComparison.lambdaChanged
  ) {
    diagnosis.push({
      code: "source_diversity_policy_changed",
      message: "Source-diversity selection mode or lambda changed between runs.",
      severity: "warning",
    });
  }

  if (comparison.sourceDiversityComparison.duplicateSelectedSourceDelta > 0) {
    diagnosis.push({
      code: "source_diversity_regressed",
      message:
        "The active run selected more duplicate evidence from already selected sources.",
      severity: "warning",
    });
  } else if (
    comparison.sourceDiversityComparison.selectedSourceDelta > 0 ||
    comparison.sourceDiversityComparison.duplicateSelectedSourceDelta < 0
  ) {
    diagnosis.push({
      code: "source_diversity_improved",
      message:
        "The active run improved selected-source coverage or reduced duplicate-source evidence.",
      severity: "success",
    });
  }

  if (comparison.rankChanges.length) {
    diagnosis.push({
      code: "rank_movement",
      message: "Retained evidence moved position in the ranked result set.",
      severity: "warning",
    });
  }

  if (comparison.addedEvidenceIds.length || comparison.removedEvidenceIds.length) {
    diagnosis.push({
      code: "evidence_set_changed",
      message: "The retrieved evidence set added or removed source chunks.",
      severity: "warning",
    });
  }

  return diagnosis;
}
