import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type {
  RunComparisonRecommendedActionSummaryView,
  RunComparisonRecommendedActionView,
} from "./run-comparison-summary-types";

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
