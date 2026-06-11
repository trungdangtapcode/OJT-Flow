import type { RetrievalSearchPayload } from "../../../types";
import type { SupportedFilterField } from "../model/retrieval-filter-model";
import {
  executeSearchWhen,
  type ExecuteRetrievalSearch,
} from "./retrieval-filter-search-action-policy";
import type { SearchFilterSuggestion } from "./retrieval-search-action-types";

type UseRetrievalMetadataFilterSearchActionsArgs = {
  applyFilterControl: (
    field: SupportedFilterField,
    value: string,
  ) => Partial<RetrievalSearchPayload>;
  clearAllFilterControls: () => Partial<RetrievalSearchPayload>;
  clearFilterControl: (field: SupportedFilterField) => Partial<RetrievalSearchPayload>;
  executeSearch: ExecuteRetrievalSearch;
  hasCurrentPackage: boolean;
  isSupportedFilterField: (field: string) => field is SupportedFilterField;
  markCustomSearch: () => void;
};

export function useRetrievalMetadataFilterSearchActions({
  applyFilterControl,
  clearAllFilterControls,
  clearFilterControl,
  executeSearch,
  hasCurrentPackage,
  isSupportedFilterField,
  markCustomSearch,
}: UseRetrievalMetadataFilterSearchActionsArgs) {
  const applySearchFilter = (field: SupportedFilterField, value: string) => {
    markCustomSearch();
    const overrides = applyFilterControl(field, value);
    void executeSearch(overrides);
  };

  const clearSearchFilter = (field: SupportedFilterField) => {
    markCustomSearch();
    const overrides = clearFilterControl(field);
    executeSearchWhen({ condition: hasCurrentPackage, executeSearch, overrides });
  };

  const clearAllSearchFilters = () => {
    markCustomSearch();
    const overrides = clearAllFilterControls();
    executeSearchWhen({ condition: hasCurrentPackage, executeSearch, overrides });
  };

  const applyFilterSuggestion = (suggestion: SearchFilterSuggestion) => {
    if (!isSupportedFilterField(suggestion.field)) return;
    applySearchFilter(suggestion.field, suggestion.value);
  };

  return {
    applyFilterSuggestion,
    applySearchFilter,
    clearAllSearchFilters,
    clearSearchFilter,
  };
}
