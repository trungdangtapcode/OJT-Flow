import type {
  RetrievalPackage,
  RetrievalRecommendedAction,
} from "../../../types";
import type { CorrectiveActionSummary } from "./retrieval-run-summary-types";

export function correctiveActionSummaryFromPackage(
  packageData: RetrievalPackage,
): CorrectiveActionSummary {
  const backendSummary = packageData.recommended_action_summary;
  if (backendSummary) {
    const actionTypeCounts = backendSummary.action_type_counts ?? {
      apply_filter: backendSummary.apply_filter_count,
      broaden_query: backendSummary.broaden_query_count ?? 0,
    };
    return {
      count: backendSummary.count,
      highestPriority: backendSummary.highest_priority ?? null,
      highestSeverity: backendSummary.highest_severity ?? null,
      topActionTitle: backendSummary.top_action_title ?? null,
      applyFilterCount: backendSummary.apply_filter_count,
      broadenQueryCount: backendSummary.broaden_query_count ?? actionTypeCounts.broaden_query ?? 0,
      actionTypeCounts,
    };
  }
  const actions = packageData.recommended_actions ?? [];
  const topAction = actions[0] ?? null;
  const actionTypeCounts = recommendedActionTypeCounts(actions);
  return {
    count: actions.length,
    highestPriority: topAction?.priority ?? null,
    highestSeverity: topAction?.severity ?? null,
    topActionTitle: topAction?.title ?? null,
    applyFilterCount: actionTypeCounts.apply_filter ?? 0,
    broadenQueryCount: actionTypeCounts.broaden_query ?? 0,
    actionTypeCounts,
  };
}

function recommendedActionTypeCounts(
  actions: RetrievalRecommendedAction[],
): Record<string, number> {
  return actions.reduce<Record<string, number>>((counts, action) => {
    counts[action.action_type] = (counts[action.action_type] ?? 0) + 1;
    return counts;
  }, {});
}
