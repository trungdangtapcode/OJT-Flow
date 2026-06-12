import { humanize } from "../../../lib/utils";
import type { RetrievalQualitySummary } from "../../../types";
import type { RetrievalRunComparison } from "./retrieval-run-comparison";

export function searchRunQualityBadgeVariant(
  summary: RetrievalQualitySummary,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
}

export function qualitySummaryBadgeVariant(
  summary: RetrievalQualitySummary,
): "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
}

export function qualitySummaryTone(
  summary: RetrievalQualitySummary | null,
): "default" | "success" | "warning" | "info" | "neutral" {
  if (!summary) return "neutral";
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked" || summary.status === "review") return "warning";
  return "info";
}

export function deltaBadgeVariant(
  delta: number,
  positiveIsGood: boolean,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (delta === 0) return "muted";
  const good = positiveIsGood ? delta > 0 : delta < 0;
  return good ? "success" : "warning";
}

export function readinessGlanceLabel(comparison: RetrievalRunComparison): string {
  const beforeStatus = humanize(
    comparison.baselineSummary.qualitySummary?.status ?? "unknown",
  );
  const afterStatus = humanize(
    comparison.activeSummary.qualitySummary?.status ?? "unknown",
  );
  const statusLabel =
    beforeStatus === afterStatus ? afterStatus : `${beforeStatus} -> ${afterStatus}`;
  const scoreLabel =
    comparison.qualityScoreDelta === null
      ? "score n/a"
      : formatSignedDelta(comparison.qualityScoreDelta);

  return `${statusLabel} / ${scoreLabel}`;
}

export function formatSignedDelta(delta: number): string {
  return delta > 0 ? `+${delta}` : String(delta);
}
