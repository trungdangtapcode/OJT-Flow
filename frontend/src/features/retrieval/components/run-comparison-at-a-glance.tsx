import { RunComparisonMetricCard } from "./run-comparison-metric-card";
import type {
  RunComparisonAtAGlanceView,
  RunComparisonRecommendedActionSummaryView,
} from "./run-comparison-summary-types";

export function RunComparisonAtAGlance({
  actionSummary,
  comparison,
  formatPercent,
  formatSignedDelta,
  readinessLabel,
}: {
  actionSummary: RunComparisonRecommendedActionSummaryView;
  comparison: RunComparisonAtAGlanceView;
  formatPercent: (value: number) => string;
  formatSignedDelta: (delta: number) => string;
  readinessLabel: string;
}) {
  return (
    <div aria-label="Comparison at a glance" className="grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
      <RunComparisonMetricCard
        label="Readiness"
        tone={comparison.qualitySummaryChanged ? "warning" : "success"}
        value={readinessLabel}
      />
      <RunComparisonMetricCard
        label="Action priority"
        tone={actionSummary.badge_variant === "success" ? "success" : "warning"}
        value={`P${actionSummary.highest_priority ?? "-"}`}
      />
      <RunComparisonMetricCard
        label="Evidence overlap"
        tone={comparison.metrics.overlapRatio >= 0.5 ? "success" : "warning"}
        value={formatPercent(comparison.metrics.overlapRatio)}
      />
      <RunComparisonMetricCard
        label="Result churn"
        tone={comparison.metrics.churnRate > 0.5 ? "warning" : "success"}
        value={formatPercent(comparison.metrics.churnRate)}
      />
      <RunComparisonMetricCard
        label="Top source"
        tone={comparison.topSourceChanged ? "warning" : "success"}
        value={comparison.topSourceChanged ? "changed" : "stable"}
      />
      <RunComparisonMetricCard
        label="Source spread"
        tone={
          comparison.sourceDiversityComparison.duplicateSelectedSourceDelta > 0
            ? "warning"
            : "success"
        }
        value={formatSignedDelta(
          comparison.sourceDiversityComparison.selectedSourceDelta,
        )}
      />
    </div>
  );
}
