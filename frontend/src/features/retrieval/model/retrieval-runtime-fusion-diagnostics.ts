import { humanize } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";
import { numberValue, recordValue, stringValue } from "./retrieval-runtime-values";
import type { RetrievalFusionDiagnosticsView } from "./retrieval-runtime-ranking-types";

export function fusionDiagnosticsFromPackage(
  packageData: RetrievalPackage,
): RetrievalFusionDiagnosticsView {
  const diagnostics = recordValue(packageData.trace.fusion_diagnostics);
  const overlapRatio = numberValue(diagnostics.top_overlap_ratio);
  const rankDelta = numberValue(diagnostics.mean_selected_rank_delta);
  const interpretation = stringValue(diagnostics.interpretation, "fusion diagnostics unavailable");
  if (overlapRatio === null) {
    return {
      interpretation,
      label: "unreported",
      tone: "info",
    };
  }
  const rankDeltaText = rankDelta === null ? "rank delta unknown" : `delta ${formatDecimal(rankDelta)}`;
  return {
    interpretation: `${humanize(interpretation)} / ${rankDeltaText}`,
    label: formatPercent(overlapRatio),
    tone: overlapRatio >= 0.75 ? "success" : overlapRatio <= 0.25 ? "warning" : "info",
  };
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDecimal(value: number): string {
  return Number.isFinite(value) ? value.toFixed(3) : "n/a";
}
