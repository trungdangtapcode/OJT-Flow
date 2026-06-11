import type {
  RetrievalPackage,
  RetrievalQualitySignal,
} from "../../../types";

export function qualitySummaryFingerprint(
  summary: RetrievalPackage["quality_summary"],
): string {
  if (!summary) return "none";
  return [
    summary.status,
    summary.score,
    summary.top_action,
    summary.blocker_codes.join(","),
    summary.warning_codes.join(","),
  ].join("|");
}

export function qualityWarningCount(signals: RetrievalQualitySignal[]): number {
  return signals.filter((signal) =>
    ["destructive", "error", "warning"].includes(signal.severity),
  ).length;
}
