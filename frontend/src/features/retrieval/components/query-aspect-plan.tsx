import { CheckCircle2, ListFilter, Loader2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type {
  FilterSuggestionStack,
  QueryAspectStack,
} from "./search-plan-detail-panels";
import { TokenList } from "./token-list";

export type QueryAspectFilterEntryView = {
  applied: boolean;
  displayValue: string;
  field: string;
  label: string;
  supported: boolean;
  value: string;
};

export type QueryAspectPlanItemView = QueryAspectStack & {
  filterEntries: QueryAspectFilterEntryView[];
};

export function QueryAspectPlan({
  aspects,
  formatCount,
  isSearchPending,
  onApplyFilter,
}: {
  aspects: QueryAspectPlanItemView[];
  formatCount: (count: number, singular: string) => string;
  isSearchPending: boolean;
  onApplyFilter: (suggestion: FilterSuggestionStack) => void;
}) {
  if (!aspects.length) {
    return <TokenList items={[]} title="Search aspect plan" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Search aspect plan
        </div>
        <Badge variant="muted">{formatCount(aspects.length, "aspect")}</Badge>
      </div>
      <div className="grid gap-2">
        {aspects.map((aspect) => (
          <div
            className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
            key={aspect.aspectId}
          >
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
                  <Badge variant="muted">
                    +{aspect.suggestedTerms.length - 5}
                  </Badge>
                ) : null}
              </div>
            ) : null}
            {aspect.filterEntries.length ? (
              <div className="flex min-w-0 flex-wrap gap-1">
                {aspect.filterEntries.map((entry) => (
                  <Badge
                    key={`${aspect.aspectId}-${entry.field}`}
                    variant={entry.applied ? "success" : "muted"}
                  >
                    {entry.label}={entry.displayValue}
                  </Badge>
                ))}
              </div>
            ) : null}
            {aspect.filterEntries.length ? (
              <div className="flex min-w-0 flex-wrap gap-1.5">
                {aspect.filterEntries.map((entry) =>
                  entry.supported ? (
                    <Button
                      disabled={isSearchPending || entry.applied}
                      key={`${aspect.aspectId}-${entry.field}-${entry.value}-apply`}
                      onClick={() =>
                        onApplyFilter({
                          applied: false,
                          confidence: 1,
                          field: entry.field,
                          reason: `Suggested by search aspect ${aspect.aspectId}.`,
                          value: entry.value,
                        })
                      }
                      size="sm"
                      title={`Apply ${entry.label}=${entry.displayValue}`}
                      type="button"
                      variant={entry.applied ? "secondary" : "outline"}
                    >
                      {entry.applied ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : isSearchPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <ListFilter className="h-4 w-4" />
                      )}
                      {entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`}
                    </Button>
                  ) : (
                    <Badge
                      key={`${aspect.aspectId}-${entry.field}-${entry.value}-unsupported`}
                      variant="warning"
                    >
                      unsupported {humanize(entry.field)}
                    </Badge>
                  ),
                )}
              </div>
            ) : null}
            <code className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px] text-muted-foreground">
              {aspect.ruleId}
            </code>
          </div>
        ))}
      </div>
    </div>
  );
}
