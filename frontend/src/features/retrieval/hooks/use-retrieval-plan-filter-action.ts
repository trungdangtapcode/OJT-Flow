import {
  executeSearchWhen,
} from "./retrieval-filter-search-action-policy";
import { planFilterControlNotice } from "./retrieval-search-plan-notice";
import type {
  SearchFilterSuggestion,
  UseRetrievalSearchActionsArgs,
} from "./retrieval-search-action-types";

type UseRetrievalPlanFilterActionArgs = Pick<
  UseRetrievalSearchActionsArgs,
  | "applyFilterControl"
  | "executeSearch"
  | "hasPlanPreviewPackage"
  | "isSupportedFilterField"
  | "markCustomSearch"
  | "setPlanControlNotice"
>;

export function useRetrievalPlanFilterAction({
  applyFilterControl,
  executeSearch,
  hasPlanPreviewPackage,
  isSupportedFilterField,
  markCustomSearch,
  setPlanControlNotice,
}: UseRetrievalPlanFilterActionArgs) {
  return (suggestion: SearchFilterSuggestion) => {
    if (!isSupportedFilterField(suggestion.field)) return;
    markCustomSearch();
    const overrides = applyFilterControl(suggestion.field, suggestion.value);
    executeSearchWhen({
      condition: hasPlanPreviewPackage,
      executeSearch,
      overrides,
    });
    if (!hasPlanPreviewPackage) {
      setPlanControlNotice(planFilterControlNotice(suggestion.field, suggestion.value));
    }
  };
}
