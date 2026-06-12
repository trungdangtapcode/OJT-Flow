import { ListFilter } from "lucide-react";

import { Button } from "../../../components/ui/button";
import type { RetrievalRecommendedAction } from "../../../types";
import { RecommendedActionBroadenControls } from "./recommended-action-broaden-controls";
import { RecommendedActionCardHeader } from "./recommended-action-card-header";
import { RecommendedActionFilterSummary } from "./recommended-action-filter-summary";
import type {
  RecommendedActionActiveFilter,
  RecommendedActionFilter,
  RecommendedActionFilterField,
} from "./recommended-actions-types";

export function RecommendedActionCard({
  action,
  activeFilters,
  filterAction,
  filterFieldLabel,
  formatFilterValue,
  isSearchPending,
  onApplyFilter,
  onClearAllFilters,
  onClearSourceScope,
  sourceLabel,
}: {
  action: RetrievalRecommendedAction;
  activeFilters: RecommendedActionActiveFilter[];
  filterAction: RecommendedActionFilter | null;
  filterFieldLabel: (field: RecommendedActionFilterField) => string;
  formatFilterValue: (field: RecommendedActionFilterField, value: string) => string;
  isSearchPending: boolean;
  onApplyFilter: (field: RecommendedActionFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
  sourceLabel: string | null;
}) {
  const isBroadeningAction = action.action_type === "broaden_query";

  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <RecommendedActionCardHeader action={action} sourceLabel={sourceLabel} />
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
          <RecommendedActionBroadenControls
            activeFilters={activeFilters}
            isSearchPending={isSearchPending}
            onClearAllFilters={onClearAllFilters}
            onClearSourceScope={onClearSourceScope}
          />
        ) : null}
      </div>
      <RecommendedActionFilterSummary
        filterAction={filterAction}
        filterFieldLabel={filterFieldLabel}
        formatFilterValue={formatFilterValue}
      />
    </div>
  );
}
