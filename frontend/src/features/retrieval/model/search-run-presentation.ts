import { humanize } from "../../../lib/utils";
import type { RetrievalQualitySummary, RetrievalSearchPayload } from "../../../types";
import { correctiveActionTypeCountEntries } from "./corrective-actions";

export type CorrectiveActionSummaryView = {
  actionTypeCounts: Record<string, number>;
  count: number;
  highestPriority: number | null;
  topActionTitle: string | null;
};

export type SearchRunSummaryView = {
  correctiveActionSummary: CorrectiveActionSummaryView;
  hitCount: number;
  qualitySummary: RetrievalQualitySummary | null;
  qualityWarningCount: number;
  remediationSummary: string | null;
  warningCount: number;
};

export function searchRunScopeLabels(payload: RetrievalSearchPayload): string[] {
  return [
    payload.schema_id ? `schema ${payload.schema_id}` : null,
    payload.detected_format ? `format ${humanize(payload.detected_format)}` : null,
    payload.resource_type ? `resource ${payload.resource_type}` : null,
    payload.clinical_domain ? `domain ${humanize(payload.clinical_domain)}` : null,
    payload.standard_system ? `standard ${payload.standard_system}` : null,
    payload.source_type ? `source ${humanize(payload.source_type)}` : null,
    payload.filters?.source_id ? `source ID ${payload.filters.source_id}` : null,
    payload.trust_level ? `trust ${humanize(payload.trust_level)}` : null,
    payload.fields.length ? formatCount(payload.fields.length, "field") : null,
  ].filter((label): label is string => Boolean(label));
}

export function searchRunQualityBadgeVariant(
  summary: RetrievalQualitySummary,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
}

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

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
