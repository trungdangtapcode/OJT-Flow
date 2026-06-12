import type { RetrievalComparisonRecommendedAction } from "./retrieval-comparison-types";

export function stableComparisonAction(
  actions: RetrievalComparisonRecommendedAction[],
): RetrievalComparisonRecommendedAction[] {
  if (actions.length) {
    return actions;
  }

  return [
    {
      action: "Keep the active retrieval configuration; no comparison follow-up was detected.",
      priority: 5,
      reason: "Comparison diagnostics are stable and no missing review signal was detected.",
      severity: "success",
      source: "comparison_stable",
    },
  ];
}
