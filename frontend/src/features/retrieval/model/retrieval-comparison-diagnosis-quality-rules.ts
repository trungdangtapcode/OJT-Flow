import type {
  RetrievalComparisonDiagnosis,
  RetrievalComparisonDiagnosticInput,
} from "./retrieval-comparison-types";

export function comparisonQualityDiagnosis(
  comparison: RetrievalComparisonDiagnosticInput,
): RetrievalComparisonDiagnosis[] {
  const diagnosis: RetrievalComparisonDiagnosis[] = [];

  if (
    comparison.coverageComparison.regressed.length ||
    comparison.coverageComparison.added.length
  ) {
    diagnosis.push({
      code: "coverage_diagnostics_changed",
      message: "Coverage diagnostics changed between runs.",
      severity: "warning",
    });
  } else if (comparison.coverageComparison.improved.length) {
    diagnosis.push({
      code: "coverage_improved",
      message: "Coverage diagnostics improved between runs.",
      severity: "success",
    });
  }

  if (
    comparison.qualitySignalComparison.added.length ||
    comparison.qualitySignalComparison.removed.length
  ) {
    diagnosis.push({
      code: "quality_signal_changed",
      message: "Package-level quality signals were added or removed.",
      severity: "warning",
    });
  }

  if (comparison.qualitySummaryChanged) {
    diagnosis.push({
      code: "quality_summary_changed",
      message: "Readiness status, score, or top action changed between runs.",
      severity:
        comparison.qualityScoreDelta !== null && comparison.qualityScoreDelta > 0
          ? "success"
          : "warning",
    });
  }

  return diagnosis;
}
