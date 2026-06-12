import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RunComparisonOperatorSummaryView } from "./run-comparison-summary-types";

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
