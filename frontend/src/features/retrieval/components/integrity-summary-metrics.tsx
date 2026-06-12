import { humanize } from "../../../lib/utils";
import { IntegrityMetric } from "./metric-primitives";
import type { IntegrityPanelProps } from "./integrity-panel-types";

export function IntegritySummaryMetrics({
  integrityBadgeVariant,
  report,
}: Pick<IntegrityPanelProps, "integrityBadgeVariant" | "report">) {
  if (!report) return null;
  return (
    <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-6">
      <IntegrityMetric
        label="Status"
        tone={integrityBadgeVariant(report.status)}
        value={humanize(report.status)}
      />
      <IntegrityMetric label="Expected" value={report.expected_source_count} />
      <IntegrityMetric label="Indexed" value={report.indexed_source_count} />
      <IntegrityMetric label="OK" tone="success" value={report.ok_count} />
      <IntegrityMetric
        label="Stale"
        tone={report.stale_count ? "warning" : "muted"}
        value={report.stale_count}
      />
      <IntegrityMetric
        label="Missing"
        tone={report.missing_count ? "destructive" : "muted"}
        value={report.missing_count}
      />
    </div>
  );
}
