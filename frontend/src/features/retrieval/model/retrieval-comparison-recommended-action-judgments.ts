import type {
  RetrievalComparisonJudgmentInput,
  RetrievalComparisonRecommendedAction,
} from "./retrieval-comparison-types";

export function judgmentActions(
  judgments: RetrievalComparisonJudgmentInput[],
): RetrievalComparisonRecommendedAction[] {
  if (judgments.length) {
    return [];
  }

  return [
    {
      action: "Add explicit relevance judgments for top hits before using this comparison as an evaluation record.",
      priority: 4,
      reason: "The copied comparison does not include any operator judgments.",
      severity: "muted",
      source: "judgments",
    },
  ];
}
