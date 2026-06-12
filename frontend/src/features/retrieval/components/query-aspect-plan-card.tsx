import { Badge } from "../../../components/ui/badge";
import {
  QueryAspectFilterBadges,
  QueryAspectFilterControls,
} from "./query-aspect-filter-controls";
import type {
  QueryAspectFilterApplyHandler,
  QueryAspectPlanItemView,
} from "./query-aspect-plan-types";

export function QueryAspectPlanCard({
  aspect,
  isSearchPending,
  onApplyFilter,
}: {
  aspect: QueryAspectPlanItemView;
  isSearchPending: boolean;
  onApplyFilter: QueryAspectFilterApplyHandler;
}) {
  return (
    <div className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="break-words font-bold">{aspect.label}</span>
        <Badge variant="muted">priority {aspect.priority}</Badge>
      </div>
      <div className="break-words font-semibold text-foreground">
        {aspect.question}
      </div>
      <div className="break-words text-muted-foreground">
        {aspect.rationale}
      </div>
      {aspect.suggestedTerms.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {aspect.suggestedTerms.slice(0, 5).map((term) => (
            <Badge key={`${aspect.aspectId}-${term}`} variant="muted">
              {term}
            </Badge>
          ))}
          {aspect.suggestedTerms.length > 5 ? (
            <Badge variant="muted">+{aspect.suggestedTerms.length - 5}</Badge>
          ) : null}
        </div>
      ) : null}
      <QueryAspectFilterBadges
        aspectId={aspect.aspectId}
        entries={aspect.filterEntries}
      />
      <QueryAspectFilterControls
        aspectId={aspect.aspectId}
        entries={aspect.filterEntries}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
      />
      <code className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px] text-muted-foreground">
        {aspect.ruleId}
      </code>
    </div>
  );
}
