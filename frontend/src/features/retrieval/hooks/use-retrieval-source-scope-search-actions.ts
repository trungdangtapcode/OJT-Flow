import {
  executeSearchWhen,
  sourceScopeOverride,
  type ExecuteRetrievalSearch,
} from "./retrieval-filter-search-action-policy";

type UseRetrievalSourceScopeSearchActionsArgs = {
  executeSearch: ExecuteRetrievalSearch;
  hasCurrentPackage: boolean;
  markCustomSearch: () => void;
  setSourceId: (value: string) => void;
};

export function useRetrievalSourceScopeSearchActions({
  executeSearch,
  hasCurrentPackage,
  markCustomSearch,
  setSourceId,
}: UseRetrievalSourceScopeSearchActionsArgs) {
  const applySourceIdFilter = (nextSourceId: string) => {
    markCustomSearch();
    setSourceId(nextSourceId);
    executeSearchWhen({
      condition: hasCurrentPackage,
      executeSearch,
      overrides: sourceScopeOverride(nextSourceId),
    });
  };

  const clearSourceScope = () => {
    markCustomSearch();
    setSourceId("");
    executeSearchWhen({
      condition: hasCurrentPackage,
      executeSearch,
      overrides: sourceScopeOverride(null),
    });
  };

  return { applySourceIdFilter, clearSourceScope };
}
