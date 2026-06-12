import { Badge } from "../../../components/ui/badge";
import type {
  QueryAspectSummaryView,
  RetrievalQueryAspectComparisonView,
} from "./run-comparison-detail-types";

export function RunComparisonQueryAspects({
  comparison,
  formatCount,
}: {
  comparison: RetrievalQueryAspectComparisonView;
  formatCount: (count: number, singular: string) => string;
}) {
  const changed = comparison.added.length + comparison.removed.length;
  const total = changed + comparison.retained.length;
  if (!total) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Search aspects</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Search aspects</span>
        <Badge variant={changed ? "warning" : "success"}>
          {changed ? formatCount(changed, "changed aspect") : "stable"}
        </Badge>
      </div>
      <QueryAspectChangeList
        aspects={comparison.added}
        label="Added"
        variant="warning"
      />
      <QueryAspectChangeList
        aspects={comparison.removed}
        label="Removed"
        variant="warning"
      />
      <QueryAspectChangeList
        aspects={comparison.retained}
        label="Retained"
        variant="muted"
      />
    </div>
  );
}

function QueryAspectChangeList({
  aspects,
  label,
  variant,
}: {
  aspects: QueryAspectSummaryView[];
  label: string;
  variant: "warning" | "muted";
}) {
  if (!aspects.length) return null;
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-semibold text-muted-foreground">{label}:</span>
        {aspects.slice(0, 4).map((aspect) => (
          <Badge key={`${label}-${aspect.aspectId}`} variant={variant}>
            {aspect.label}
          </Badge>
        ))}
        {aspects.length > 4 ? <Badge variant="muted">+{aspects.length - 4}</Badge> : null}
      </div>
      <div className="grid gap-1">
        {aspects.slice(0, 2).map((aspect) => (
          <div className="break-words text-muted-foreground" key={`${label}-${aspect.aspectId}-question`}>
            {aspect.question}
          </div>
        ))}
      </div>
    </div>
  );
}
