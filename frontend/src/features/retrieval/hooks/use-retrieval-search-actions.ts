import type {
  UseRetrievalSearchActionsArgs,
} from "./retrieval-search-action-types";
import { useRetrievalFilterSearchActions } from "./use-retrieval-filter-search-actions";
import { useRetrievalPlannedTaskAction } from "./use-retrieval-planned-task-action";

export function useRetrievalSearchActions({
  applyFilterControl,
  clearAllFilterControls,
  clearFilterControl,
  executeSearch,
  hasCurrentPackage,
  hasPlanPreviewPackage,
  isSupportedFilterField,
  markCustomSearch,
  setClinicalDomain,
  setPlanControlNotice,
  setQuery,
  setSourceId,
  setSourceType,
  setStandardSystem,
  setTrustLevel,
}: UseRetrievalSearchActionsArgs) {
  const runPlannedTask = useRetrievalPlannedTaskAction({
    executeSearch,
    markCustomSearch,
    setClinicalDomain,
    setQuery,
    setSourceId,
    setSourceType,
    setStandardSystem,
    setTrustLevel,
  });
  const filterSearchActions = useRetrievalFilterSearchActions({
    applyFilterControl,
    clearAllFilterControls,
    clearFilterControl,
    executeSearch,
    hasCurrentPackage,
    hasPlanPreviewPackage,
    isSupportedFilterField,
    markCustomSearch,
    setPlanControlNotice,
    setSourceId,
  });

  return {
    ...filterSearchActions,
    runPlannedTask,
  };
}
