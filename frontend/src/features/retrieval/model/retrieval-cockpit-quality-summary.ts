import type { RetrievalQualitySummary } from "../../../types";
import type { RetrievalSearchCockpitView } from "./retrieval-cockpit-view-types";

export function qualitySummaryView(summary: RetrievalQualitySummary): NonNullable<
  RetrievalSearchCockpitView["qualitySummary"]
> {
  return {
    score: summary.score,
    status: summary.status,
    topAction: summary.top_action,
    variant: qualitySummaryBadgeVariant(summary),
  };
}

export function qualitySummaryBadgeVariant(
  summary: RetrievalQualitySummary,
): "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
}
