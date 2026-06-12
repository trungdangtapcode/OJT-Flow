import { humanize } from "../../../lib/utils";
import {
  formatCount,
  formatPercent,
  formatSignedDelta,
  uniqueValues,
} from "./retrieval-comparison-action-format";
import type {
  RetrievalComparisonOperatorSummary,
  RetrievalComparisonOperatorSummaryInput,
  RetrievalComparisonRecommendedAction,
} from "./retrieval-comparison-types";

export function comparisonOperatorSummary(
  comparison: RetrievalComparisonOperatorSummaryInput,
  recommendedActions: RetrievalComparisonRecommendedAction[],
): RetrievalComparisonOperatorSummary {
  const warnings = comparison.diagnosis.filter(
    (item) => item.severity === "warning",
  );
  const improvements = comparison.diagnosis.filter(
    (item) => item.severity === "success" && item.code !== "comparison_stable",
  );
  const diversity = comparison.sourceDiversityComparison;
  const status: RetrievalComparisonOperatorSummary["status"] = warnings.length
    ? "review"
    : improvements.length
      ? "improved"
      : "stable";
  const headline =
    status === "review"
      ? `Review ${formatCount(warnings.length, "change driver")} before accepting this retrieval tuning run.`
      : status === "improved"
        ? "Active run improved one or more retrieval readiness signals without warning drivers."
        : "Active run is stable against the selected baseline.";
  const topAction =
    recommendedActions.find((action) => action.severity !== "success") ??
    recommendedActions[0] ??
    null;
  const sourceSpread =
    diversity.selectedSourceDelta === 0 &&
    diversity.duplicateSelectedSourceDelta === 0
      ? "Source spread is unchanged."
      : `Source spread ${formatSignedDelta(
          diversity.selectedSourceDelta,
        )}; duplicate-source evidence ${formatSignedDelta(
          diversity.duplicateSelectedSourceDelta,
        )}.`;
  const bullets = [
    `Evidence overlap ${formatPercent(comparison.metrics.overlapRatio)}; churn ${formatPercent(comparison.metrics.churnRate)}.`,
    `Quality score delta ${
      comparison.qualityScoreDelta === null
        ? "n/a"
        : formatSignedDelta(comparison.qualityScoreDelta)
    }; quality warnings ${formatSignedDelta(comparison.qualityWarningDelta)}.`,
    sourceSpread,
    topAction
      ? `Next action: ${topAction.action}`
      : "No follow-up action detected.",
  ];
  const reviewFocus = uniqueValues([
    ...warnings.slice(0, 4).map((item) => humanize(item.code)),
    ...(diversity.duplicateSelectedSourceDelta > 0 ? ["source concentration"] : []),
    ...(comparison.metrics.churnRate > 0.5 ? ["evidence churn"] : []),
    ...(comparison.rankChanges.length ? ["rank movement"] : []),
    ...(comparison.qualitySummaryChanged ? ["quality readiness"] : []),
  ]);

  return {
    bullets,
    headline,
    reviewFocus: reviewFocus.length ? reviewFocus : ["no immediate review focus"],
    status,
  };
}
