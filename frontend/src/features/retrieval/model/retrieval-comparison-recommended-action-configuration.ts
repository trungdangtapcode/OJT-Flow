import type {
  RetrievalComparisonRecommendationInput,
  RetrievalComparisonRecommendedAction,
} from "./retrieval-comparison-types";

export function queryProfileActions(
  comparison: RetrievalComparisonRecommendationInput,
): RetrievalComparisonRecommendedAction[] {
  if (!comparison.queryProfileChanged) {
    return [];
  }

  return [
    {
      action: "Confirm the active query profile, route, and retrieval mode match the intended search task.",
      priority: 3,
      reason: "Adaptive query-profile guidance changed between runs.",
      severity: "warning",
      source: "query_profile",
    },
  ];
}

export function rulePackActions(
  comparison: RetrievalComparisonRecommendationInput,
): RetrievalComparisonRecommendedAction[] {
  if (!comparison.rulePackChanged) {
    return [];
  }

  return [
    {
      action: "Record the active rule-pack fingerprints with any relevance-tuning decision.",
      priority: 3,
      reason: "Rule-pack data changed, so ranking movement may not be caused only by query edits.",
      severity: "warning",
      source: "rule_packs",
    },
  ];
}
