import type * as React from "react";

import type { RetrievalTracePanel } from "../components/retrieval-trace-panel";
import { recommendedActionFilter } from "./retrieval-cockpit-signals";
import {
  activeFilterEntriesForSearch,
  coverageSuggestedAction,
  coverageSuggestedFilter,
  filterFieldLabel,
  formatFilterValue,
  isSupportedFilterField,
} from "./retrieval-filter-model";
import { formatCount } from "./retrieval-format";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";
import { recommendedActionSourceLabel } from "./search-run-presentation";

export function retrievalPageTraceProps({
  searchMutation,
  workspace,
}: Pick<
  RetrievalPagePropsArgs,
  "searchMutation" | "workspace"
>): React.ComponentProps<typeof RetrievalTracePanel> {
  const { runSession, searchActions } = workspace;

  return {
    activeFilters: activeFilterEntriesForSearch(
      workspace.activeFacetFilters,
      runSession.submittedSearchPayload,
    ),
    filterFieldLabel,
    formatCount,
    formatFilterValue,
    getActionFilter: recommendedActionFilter,
    getActionSourceLabel: recommendedActionSourceLabel,
    getCoverageSuggestedAction: coverageSuggestedAction,
    getCoverageSuggestedFilter: coverageSuggestedFilter,
    isSearchPending: searchMutation.isPending,
    isSuggestionSupported: isSupportedFilterField,
    onApplyCoverageFilter: searchActions.applySearchFilter,
    onApplyFilterSuggestion: searchActions.applyFilterSuggestion,
    onClearAllFilters: searchActions.clearAllSearchFilters,
    onClearSourceScope: () => searchActions.clearSearchFilter("source_id"),
    view: workspace.tracePanelView,
  };
}
