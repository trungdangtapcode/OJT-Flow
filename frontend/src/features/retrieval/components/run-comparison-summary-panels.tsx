import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { SectionHelpText } from "./section-help-text";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export type RunComparisonOperatorSummaryView = {
  bullets: string[];
  headline: string;
  reviewFocus: string[];
  status: "stable" | "review" | "improved";
};

export type RunComparisonDiagnosisView = {
  code: string;
  message: string;
  severity: "success" | "warning" | "muted";
};

export type RunComparisonRecommendedActionView = {
  action: string;
  priority: number;
  reason: string;
  severity: BadgeVariant;
  source: string;
};

export type RunComparisonRecommendedActionSummaryView = {
  action_count: number;
  badge_variant: "success" | "warning" | "destructive";
  highest_priority: number | null;
  highest_severity: "success" | "warning" | "destructive";
  source_count: number;
  source_counts: Record<string, number>;
  sources: string[];
};

export type RunComparisonMetricsView = {
  changedRankCount: number;
  churnRate: number;
  meanAbsoluteRankDelta: number;
  overlapRatio: number;
  sharedCount: number;
  unionCount: number;
};

export function RunComparisonOperatorSummary({
  summary,
}: {
  summary: RunComparisonOperatorSummaryView;
}) {
  const variant =
    summary.status === "improved"
      ? "success"
      : summary.status === "stable"
        ? "muted"
        : "warning";
  return (
    <div
      aria-label="Comparison operator summary"
      className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="grid min-w-0 gap-1">
          <span className="font-bold text-muted-foreground">
            Operator summary
          </span>
          <span className="break-words text-sm font-semibold">
            {summary.headline}
          </span>
        </div>
        <Badge variant={variant}>{humanize(summary.status)}</Badge>
      </div>
      <div className="grid gap-1 sm:grid-cols-2">
        {summary.bullets.map((item) => (
          <span
            className="rounded-md border border-border bg-muted/30 px-2 py-1 text-muted-foreground"
            key={item}
          >
            {item}
          </span>
        ))}
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <span className="font-semibold text-muted-foreground">
          Review focus
        </span>
        {summary.reviewFocus.map((item) => (
          <Badge key={item} variant="muted">
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}

export function RunComparisonDiagnosis({
  diagnosis,
  formatCount,
}: {
  diagnosis: RunComparisonDiagnosisView[];
  formatCount: (count: number, singular: string) => string;
}) {
  const warningCount = diagnosis.filter((item) => item.severity === "warning").length;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">
          Comparison diagnosis
        </span>
        <Badge variant={warningCount ? "warning" : "success"}>
          {warningCount ? formatCount(warningCount, "change driver") : "stable"}
        </Badge>
      </div>
      <div className="grid gap-1">
        {diagnosis.map((item) => (
          <div
            className="flex min-w-0 flex-wrap items-start gap-2"
            key={item.code}
          >
            <Badge variant={item.severity}>{humanize(item.code)}</Badge>
            <span className="min-w-0 flex-1 break-words text-muted-foreground">
              {item.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function RunComparisonRecommendedActions({
  actions,
  actionSummary,
  formatCount,
}: {
  actions: RunComparisonRecommendedActionView[];
  actionSummary: RunComparisonRecommendedActionSummaryView;
  formatCount: (count: number, singular: string) => string;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">
          Recommended actions
        </span>
        <span className="flex flex-wrap justify-end gap-1.5">
          <Badge variant={actionSummary.badge_variant}>
            {formatCount(actionSummary.action_count, "action")}
          </Badge>
          <Badge variant="muted">P{actionSummary.highest_priority}</Badge>
          <Badge variant="muted">
            {formatCount(actionSummary.source_count, "source")}
          </Badge>
        </span>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {actionSummary.sources.map((source) => (
          <Badge key={source} variant="muted">
            {humanize(source)} {actionSummary.source_counts[source] ?? 0}
          </Badge>
        ))}
      </div>
      <div className="grid gap-1.5">
        {actions.map((item) => (
          <div className="grid gap-1" key={`${item.source}-${item.action}`}>
            <div className="flex min-w-0 flex-wrap items-start gap-2">
              <Badge variant={item.severity}>P{item.priority}</Badge>
              <Badge variant="muted">{humanize(item.source)}</Badge>
              <span className="min-w-0 flex-1 break-words font-semibold">
                {item.action}
              </span>
            </div>
            <span className="break-words pl-0 text-muted-foreground sm:pl-20">
              {item.reason}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

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

export function RunComparisonMetricCard({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "success" | "warning";
  value: string;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2">
      <span className="text-xs font-bold text-muted-foreground">{label}</span>
      <Badge variant={tone}>{value}</Badge>
    </div>
  );
}

export function RunComparisonMetric({
  delta,
  deltaBadgeVariant,
  formatSignedDelta,
  label,
  positiveIsGood,
}: {
  delta: number;
  deltaBadgeVariant: (delta: number, positiveIsGood: boolean) => BadgeVariant;
  formatSignedDelta: (delta: number) => string;
  label: string;
  positiveIsGood: boolean;
}) {
  return (
    <div className="flex min-w-0 items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
      <span className="text-xs font-bold text-muted-foreground">{label}</span>
      <Badge variant={deltaBadgeVariant(delta, positiveIsGood)}>
        {formatSignedDelta(delta)}
      </Badge>
    </div>
  );
}
