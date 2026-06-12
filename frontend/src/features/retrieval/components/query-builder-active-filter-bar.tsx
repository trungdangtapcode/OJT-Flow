import { activeFilterEntries } from "../model/retrieval-filter-model";
import { ActiveFilterBar } from "./active-filter-bar";
import type {
  RetrievalQueryBuilderActions,
  RetrievalQueryBuilderValue,
} from "./query-builder-panel-types";

export function QueryBuilderActiveFilterBar({
  actions,
  value,
}: {
  actions: RetrievalQueryBuilderActions;
  value: RetrievalQueryBuilderValue;
}) {
  return (
    <ActiveFilterBar
      filters={activeFilterEntries(value.activeFilters)}
      isSearchPending={value.isSearchPending}
      onClearAll={actions.onClearAllFilters}
      onRemove={actions.onRemoveFilter}
    />
  );
}
