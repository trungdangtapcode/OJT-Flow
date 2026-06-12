import { humanize } from "../../../lib/utils";
import { correctiveActionTypeCountEntries } from "./corrective-actions";
import { formatCount } from "./retrieval-format";
import type { SearchRunSummaryView } from "./search-run-presentation-types";

export function searchRunRemediationSummary(summary: SearchRunSummaryView): string | null {
  const actions = summary.correctiveActionSummary;
  if (actions.count > 0) {
    const actionTypes = correctiveActionTypeCountEntries(actions.actionTypeCounts)
      .slice(0, 3)
      .map(([actionType, count]) => `${humanize(actionType)} ${count}`)
      .join(", ");
    const priority = actions.highestPriority ? `P${actions.highestPriority}` : "priority unreported";
    const topAction = actions.topActionTitle ?? "inspect backend corrective actions";
    return actionTypes
      ? `${topAction} (${priority}; ${actionTypes})`
      : `${topAction} (${priority})`;
  }
  if (summary.qualitySummary?.top_action) {
    return summary.qualitySummary.top_action;
  }
  if (summary.qualityWarningCount > 0 || summary.warningCount > 0) {
    return `inspect ${formatCount(
      summary.qualityWarningCount + summary.warningCount,
      "warning",
    )} before using this evidence`;
  }
  if (summary.hitCount === 0) {
    return "broaden search scope or inspect source inventory";
  }
  return null;
}
