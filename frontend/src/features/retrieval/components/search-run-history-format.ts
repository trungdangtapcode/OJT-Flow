import type { SearchRunHistorySummary } from "./search-run-history-types";

export function searchRunSummaryVariant(
  summary: SearchRunHistorySummary,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (summary.qualityWarningCount > 0 || summary.warningCount > 0) return "warning";
  if (summary.hitCount > 0) return "success";
  return "destructive";
}

export function formatRunTime(submittedAt: string): string {
  const date = new Date(submittedAt);
  if (Number.isNaN(date.getTime())) return "recent";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function formatShortSignature(signature: string): string {
  const digest = signature.includes(":")
    ? signature.split(":").pop() ?? signature
    : signature;
  return `sig ${digest.slice(0, 10)}`;
}

export function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
