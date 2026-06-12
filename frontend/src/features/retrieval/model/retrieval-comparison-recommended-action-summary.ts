import type {
  RetrievalComparisonRecommendedAction,
  RetrievalComparisonRecommendedActionSummary,
} from "./retrieval-comparison-types";

export function comparisonRecommendedActionSummary(
  actions: RetrievalComparisonRecommendedAction[],
): RetrievalComparisonRecommendedActionSummary {
  const sources = new Set(actions.map((action) => action.source));
  const sourceCounts = actions.reduce<Record<string, number>>((counts, action) => {
    counts[action.source] = (counts[action.source] ?? 0) + 1;
    return counts;
  }, {});
  const highestPriority = Math.min(...actions.map((action) => action.priority));
  const hasDestructive = actions.some((action) => action.severity === "destructive");
  const hasWarning = actions.some((action) => action.severity === "warning");

  return {
    action_count: actions.length,
    badge_variant: hasDestructive ? "destructive" : hasWarning ? "warning" : "success",
    highest_priority: Number.isFinite(highestPriority) ? highestPriority : null,
    highest_severity: hasDestructive ? "destructive" : hasWarning ? "warning" : "success",
    source_count: sources.size,
    source_counts: sourceCounts,
    sources: Array.from(sources).sort(),
  };
}
