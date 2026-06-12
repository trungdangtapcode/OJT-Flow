import type { RetrievalRecommendedAction } from "../../../types";
import { RecommendedActionCard } from "./recommended-action-card";
import { RecommendedActionsHeader } from "./recommended-actions-header";
import { TokenList } from "./token-list";
import type {
  RecommendedActionActiveFilter,
  RecommendedActionFilter,
  RecommendedActionFilterField,
} from "./recommended-actions-types";
export type {
  RecommendedActionFilter,
  RecommendedActionFilterField,
} from "./recommended-actions-types";

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

  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <RecommendedActionsHeader actions={actions} />
      <div className="grid gap-2">
        {actions.slice(0, 6).map((action) => {
          const filterAction = getActionFilter(action);
          const sourceLabel = getActionSourceLabel(action);
          return (
            <RecommendedActionCard
              action={action}
              activeFilters={activeFilters}
              filterAction={filterAction}
              filterFieldLabel={filterFieldLabel}
              formatFilterValue={formatFilterValue}
              isSearchPending={isSearchPending}
              key={action.action_id}
              onApplyFilter={onApplyFilter}
              onClearAllFilters={onClearAllFilters}
              onClearSourceScope={onClearSourceScope}
              sourceLabel={sourceLabel}
            />
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
