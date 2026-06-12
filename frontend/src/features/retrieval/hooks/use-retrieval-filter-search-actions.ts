import type {
  UseRetrievalSearchActionsArgs,
} from "./retrieval-search-action-types";
import { useRetrievalMetadataFilterSearchActions } from "./use-retrieval-metadata-filter-search-actions";
import { useRetrievalPlanFilterAction } from "./use-retrieval-plan-filter-action";
import { useRetrievalSourceScopeSearchActions } from "./use-retrieval-source-scope-search-actions";

type UseRetrievalFilterSearchActionsArgs = Pick<
  UseRetrievalSearchActionsArgs,
  | "applyFilterControl"
  | "clearAllFilterControls"
  | "clearFilterControl"
  | "executeSearch"
  | "hasCurrentPackage"
  | "hasPlanPreviewPackage"
  | "isSupportedFilterField"
  | "markCustomSearch"
  | "setPlanControlNotice"
  | "setSourceId"
>;

export function useRetrievalFilterSearchActions({
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
}: UseRetrievalFilterSearchActionsArgs) {
  const applyPlanFilterSuggestion = useRetrievalPlanFilterAction({
    applyFilterControl,
    executeSearch,
    hasPlanPreviewPackage,
    isSupportedFilterField,
    markCustomSearch,
    setPlanControlNotice,
  });

  const metadataFilterActions = useRetrievalMetadataFilterSearchActions({
    applyFilterControl,
    clearAllFilterControls,
    clearFilterControl,
    executeSearch,
    hasCurrentPackage,
    isSupportedFilterField,
    markCustomSearch,
  });
  const sourceScopeActions = useRetrievalSourceScopeSearchActions({
    executeSearch,
    hasCurrentPackage,
    markCustomSearch,
    setSourceId,
  });

  return {
    ...metadataFilterActions,
    applyPlanFilterSuggestion,
    ...sourceScopeActions,
  };
}
