import type {
  RetrievalComparisonRecommendationInput,
  RetrievalComparisonRecommendedAction,
} from "./retrieval-comparison-types";

export function qualitySummaryActions(
  comparison: RetrievalComparisonRecommendationInput,
): RetrievalComparisonRecommendedAction[] {
  const activeTopAction = comparison.activeSummary.qualitySummary?.top_action;
  if (!activeTopAction) {
    return [];
  }

  return [
    {
      action: activeTopAction,
      priority: comparison.activeSummary.qualitySummary?.status === "blocked" ? 1 : 2,
      reason: "Active retrieval package readiness policy selected this top action.",
      severity:
        comparison.activeSummary.qualitySummary?.status === "blocked"
          ? "destructive"
          : "warning",
      source: "quality_summary.top_action",
    },
  ];
}

export function coverageActions(
  comparison: RetrievalComparisonRecommendationInput,
): RetrievalComparisonRecommendedAction[] {
  if (
    !comparison.coverageComparison.regressed.length &&
    !comparison.coverageComparison.added.length
  ) {
    return [];
  }

  return [
    {
      action: "Review coverage diagnostics and apply supported standard/aspect filters before accepting this run.",
      priority: 1,
      reason: "Coverage diagnostics were added or regressed between baseline and active runs.",
      severity: "warning",
      source: "coverage",
    },
  ];
}

export function qualitySignalActions(
  comparison: RetrievalComparisonRecommendationInput,
): RetrievalComparisonRecommendedAction[] {
  if (!comparison.qualitySignalComparison.added.length) {
    return [];
  }

  return [
    {
      action: "Inspect newly added quality signals before using the active evidence package downstream.",
      priority: 1,
      reason: "The active run added package-level quality signals.",
      severity: "warning",
      source: "quality_signals",
    },
  ];
}
