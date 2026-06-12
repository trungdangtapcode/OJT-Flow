import type * as React from "react";

import { workflowErrorMessage } from "../../../lib/server-state";
import type { QueryBuilderPanel } from "../components/query-builder-panel";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";
import { retrievalQueryBuilderOptionsView } from "./retrieval-search-options-model";

export function retrievalPageQueryBuilderProps({
  presetsQuery,
  schemasQuery,
  searchMutation,
  searchOptionsQuery,
  sourcesQuery,
  workspace,
}: RetrievalPagePropsArgs): React.ComponentProps<typeof QueryBuilderPanel> {
  const presets = presetsQuery.data ?? [];
  const sources = sourcesQuery.data ?? [];
  const queryBuilderOptions = retrievalQueryBuilderOptionsView({
    formState: workspace.formState,
    presets,
    searchOptions: searchOptionsQuery.data,
    sources,
  });
  const { runSession, searchActions } = workspace;

  return {
    actions: {
      ...workspace.queryBuilderDraftActions,
      onClearAllFilters: searchActions.clearAllSearchFilters,
      onClearSourceScope: searchActions.clearSourceScope,
      onRemoveFilter: searchActions.clearSearchFilter,
      onSearch: (event) => void runSession.runSearch(event),
    },
    options: {
      ...queryBuilderOptions,
      presets,
      schemas: schemasQuery.data ?? [],
      sources,
    },
    status: {
      presetsError: presetsQuery.isError
        ? workflowErrorMessage(presetsQuery.error)
        : null,
      presetsLoading: presetsQuery.isLoading,
      searchError: searchMutation.isError
        ? workflowErrorMessage(searchMutation.error)
        : null,
      searchOptionsError: searchOptionsQuery.isError
        ? workflowErrorMessage(searchOptionsQuery.error)
        : null,
    },
    value: {
      ...workspace.values,
      activeFilters: workspace.activeFacetFilters,
      activePresetId: workspace.activePresetId,
      formError: workspace.formError,
      isSearchPending: searchMutation.isPending,
      isSearchResultStale: workspace.planSession.isSearchResultStale,
      planControlNotice: workspace.planControlNotice,
    },
  };
}
