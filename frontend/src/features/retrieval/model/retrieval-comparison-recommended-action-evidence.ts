import type {
  RetrievalComparisonRecommendationInput,
  RetrievalComparisonRecommendedAction,
} from "./retrieval-comparison-types";

export function evidenceChangeActions(
  comparison: RetrievalComparisonRecommendationInput,
): RetrievalComparisonRecommendedAction[] {
  if (comparison.metrics.churnRate <= 0.5 && !comparison.topSourceChanged) {
    return [];
  }

  return [
    {
      action: "Compare added, removed, and retained evidence before treating the active run as equivalent to baseline.",
      priority: 2,
      reason: "Evidence churn or top-source movement is high enough to affect review conclusions.",
      severity: "warning",
      source: "evidence",
    },
  ];
}

export function sourceDiversityActions(
  comparison: RetrievalComparisonRecommendationInput,
): RetrievalComparisonRecommendedAction[] {
  const actions: RetrievalComparisonRecommendedAction[] = [];

  if (comparison.sourceDiversityComparison.duplicateSelectedSourceDelta > 0) {
    actions.push({
      action: "Review whether active results over-concentrate evidence from the same source family before accepting the tuning change.",
      priority: 2,
      reason: "The active run selected more duplicate-source evidence than the baseline.",
      severity: "warning",
      source: "source_diversity",
    });
  }

  if (
    comparison.sourceDiversityComparison.selectionModeChanged ||
    comparison.sourceDiversityComparison.lambdaChanged
  ) {
    actions.push({
      action: "Document source-diversity policy changes with this comparison result.",
      priority: 3,
      reason: "Selection mode or lambda changed, so source spread is not directly comparable without configuration context.",
      severity: "warning",
      source: "source_diversity",
    });
  }

  return actions;
}
