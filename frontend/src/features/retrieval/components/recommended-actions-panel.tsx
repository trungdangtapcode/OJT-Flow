import { ListFilter, X } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { RetrievalRecommendedAction } from "../../../types";
import { qualitySignalBadgeVariant } from "./quality-signal-list";
import { TokenList } from "./token-list";

export type RecommendedActionFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type RecommendedActionFilter = {
  field: RecommendedActionFilterField;
  value: string;
};

type RecommendedActionActiveFilter = {
  field: RecommendedActionFilterField;
};

export function RecommendedActionsPanel({
  activeFilters,
  actions,
  filterFieldLabel,
  formatFilterValue,
  getActionFilter,
  getActionSourceLabel,
  isSearchPending,
  onApplyFilter,
  onClearAllFilters,
  onClearSourceScope,
}: {
  activeFilters: RecommendedActionActiveFilter[];
  actions: RetrievalRecommendedAction[];
  filterFieldLabel: (field: RecommendedActionFilterField) => string;
  formatFilterValue: (field: RecommendedActionFilterField, value: string) => string;
  getActionFilter: (action: RetrievalRecommendedAction) => RecommendedActionFilter | null;
  getActionSourceLabel: (action: RetrievalRecommendedAction) => string | null;
  isSearchPending: boolean;
  onApplyFilter: (field: RecommendedActionFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
}) {
  if (!actions.length) {
    return <TokenList items={[]} title="Corrective actions" />;
  }
  const actionTypeCounts = recommendedActionTypeCounts(actions);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Corrective actions
          </div>
          <div className="mt-1 break-words text-sm text-muted-foreground">
            Backend-derived next steps from retrieval quality signals.
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant="warning">{formatCount(actions.length, "action")}</Badge>
          {Object.entries(actionTypeCounts).map(([actionType, count]) => (
            <Badge key={actionType} variant="muted">
              {humanize(actionType)} {count}
            </Badge>
          ))}
        </div>
      </div>
      <div className="grid gap-2">
        {actions.slice(0, 6).map((action) => {
          const filterAction = getActionFilter(action);
          const isBroadeningAction = action.action_type === "broaden_query";
          const sourceFilter = activeFilters.find((filter) => filter.field === "source_id");
          const sourceLabel = getActionSourceLabel(action);
          return (
            <div
              className="grid gap-2 rounded-md border border-border bg-card p-3"
              key={action.action_id}
            >
              <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                    <Badge variant={qualitySignalBadgeVariant(action.severity)}>
                      P{action.priority}
                    </Badge>
                    <Badge variant="muted">{humanize(action.action_type)}</Badge>
                    {sourceLabel ? <Badge variant="muted">{sourceLabel}</Badge> : null}
                    {action.source_signal_codes.slice(0, 2).map((code) => (
                      <Badge
                        className="max-w-full break-words"
                        key={`${action.action_id}-${code}`}
                        variant="muted"
                      >
                        {humanize(code)}
                      </Badge>
                    ))}
                  </div>
                  <div className="mt-2 break-words text-sm font-black">
                    {action.title}
                  </div>
                  <div className="mt-1 break-words text-xs leading-5 text-muted-foreground">
                    {action.description}
                  </div>
                </div>
                {filterAction ? (
                  <Button
                    disabled={isSearchPending}
                    onClick={() => onApplyFilter(filterAction.field, filterAction.value)}
                    size="sm"
                    type="button"
                    variant="outline"
                  >
                    <ListFilter className="h-4 w-4" />
                    Apply
                  </Button>
                ) : null}
                {isBroadeningAction ? (
                  <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
                    {sourceFilter ? (
                      <Button
                        disabled={isSearchPending}
                        onClick={onClearSourceScope}
                        size="sm"
                        title="Clear exact source scope and rerun search"
                        type="button"
                        variant="outline"
                      >
                        <X className="h-4 w-4" />
                        Clear source scope
                      </Button>
                    ) : null}
                    <Button
                      disabled={isSearchPending || !activeFilters.length}
                      onClick={onClearAllFilters}
                      size="sm"
                      title="Clear all active metadata filters and rerun search"
                      type="button"
                      variant="outline"
                    >
                      <ListFilter className="h-4 w-4" />
                      Broaden search
                    </Button>
                  </div>
                ) : null}
              </div>
              {filterAction ? (
                <div className="break-words rounded-md bg-muted px-2 py-1 text-xs font-semibold text-muted-foreground">
                  {filterFieldLabel(filterAction.field)}:{" "}
                  {formatFilterValue(filterAction.field, filterAction.value)}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
      {actions.length > 6 ? (
        <div className="text-xs font-semibold text-muted-foreground">
          Showing first 6 actions by backend priority.
        </div>
      ) : null}
    </div>
  );
}

function recommendedActionTypeCounts(
  actions: RetrievalRecommendedAction[],
): Record<string, number> {
  return actions.reduce<Record<string, number>>((counts, action) => {
    counts[action.action_type] = (counts[action.action_type] ?? 0) + 1;
    return counts;
  }, {});
}

function formatCount(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}
