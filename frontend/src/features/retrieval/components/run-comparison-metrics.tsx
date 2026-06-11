import { SectionHelpText } from "./section-help-text";
import { RunComparisonMetricCard } from "./run-comparison-metric-card";
import type { RunComparisonMetricsView } from "./run-comparison-summary-types";

export function RunComparisonMetrics({
  formatDecimal,
  formatPercent,
  metrics,
}: {
  formatDecimal: (value: number) => string;
  formatPercent: (value: number) => string;
  metrics: RunComparisonMetricsView;
}) {
  return (
    <div aria-label="Search comparison metrics" className="grid gap-2">
      <SectionHelpText>
        Overlap shows shared evidence; churn shows how much the result set changed; mean rank delta shows ordering instability among retained evidence.
      </SectionHelpText>
      <div className="grid gap-2 sm:grid-cols-2">
        <RunComparisonMetricCard
          label="Overlap"
          tone={metrics.overlapRatio >= 0.5 ? "success" : "warning"}
          value={formatPercent(metrics.overlapRatio)}
        />
        <RunComparisonMetricCard
          label="Result churn"
          tone={metrics.churnRate > 0.5 ? "warning" : "success"}
          value={formatPercent(metrics.churnRate)}
        />
        <RunComparisonMetricCard
          label="Shared evidence"
          tone={metrics.sharedCount ? "success" : "warning"}
          value={`${metrics.sharedCount}/${metrics.unionCount}`}
        />
        <RunComparisonMetricCard
          label="Mean rank delta"
          tone={metrics.meanAbsoluteRankDelta > 1 ? "warning" : "success"}
          value={formatDecimal(metrics.meanAbsoluteRankDelta)}
        />
      </div>
    </div>
  );
}
