import type { RetrievalRecommendedAction } from "../../../types";

export function recommendedActionTypeCounts(
  actions: RetrievalRecommendedAction[],
): Record<string, number> {
  return actions.reduce<Record<string, number>>((counts, action) => {
    counts[action.action_type] = (counts[action.action_type] ?? 0) + 1;
    return counts;
  }, {});
}

export function formatRecommendedActionCount(
  count: number,
  singular: string,
  plural = `${singular}s`,
) {
  return `${count} ${count === 1 ? singular : plural}`;
}
