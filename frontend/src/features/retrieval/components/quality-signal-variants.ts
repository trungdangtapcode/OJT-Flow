import type { RetrievalQualitySignal } from "../../../types";
import type { BadgeVariant } from "./quality-signal-types";

export function qualitySignalBadgeVariant(severity: string): BadgeVariant {
  if (severity === "success") return "success";
  if (severity === "warning") return "warning";
  if (severity === "destructive" || severity === "error") return "destructive";
  if (severity === "info") return "muted";
  return "default";
}

export function qualitySignalSummaryVariant(
  signals: RetrievalQualitySignal[],
): BadgeVariant {
  if (
    signals.some(
      (signal) => signal.severity === "destructive" || signal.severity === "error",
    )
  ) {
    return "destructive";
  }
  if (signals.some((signal) => signal.severity === "warning")) return "warning";
  if (signals.some((signal) => signal.severity === "success")) return "success";
  return "muted";
}
