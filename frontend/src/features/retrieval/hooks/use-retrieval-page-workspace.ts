import { useRetrievalFormSession } from "./use-retrieval-form-session";
import { useRetrievalJudgmentSession } from "./use-retrieval-judgment-session";
import { useRetrievalPlanSession } from "./use-retrieval-plan-session";
import { useRetrievalRunSession } from "./use-retrieval-run-session";
import { useRetrievalWorkspaceClearActions } from "./use-retrieval-workspace-clear-actions";
import { useRetrievalWorkspaceSearchActions } from "./use-retrieval-workspace-search-actions";
import { useRetrievalWorkspaceSearchSubmit } from "./use-retrieval-workspace-search-submit";
import { useRetrievalWorkspaceView } from "./use-retrieval-workspace-view";
import type { UseRetrievalPageWorkspaceArgs } from "./use-retrieval-page-workspace-types";

export function useRetrievalPageWorkspace({
  presets,
  searchMutation,
}: UseRetrievalPageWorkspaceArgs) {
  const formSession = useRetrievalFormSession(presets);
  const {
    activeFacetFilters,
    activePresetId,
    applyFilterControl,
    clearAllFilterControls,
    clearFilterControl,
    currentSearchSignature,
    formError,
    formState,
    markCustomSearch,
    planControlNotice,
    queryBuilderDraftActions,
    restoreSearchPayload,
    setClinicalDomain,
    setFormError,
    setPlanControlNotice,
    setQuery,
    setSourceId,
    setSourceType,
    setStandardSystem,
    setTrustLevel,
    values,
  } = formSession;
  const submitSearch = useRetrievalWorkspaceSearchSubmit({
    searchMutation,
    setFormError,
    setPlanControlNotice,
  });
  const runSession = useRetrievalRunSession({
    formState,
    latestPackageData: searchMutation.data,
    onValidationError: setFormError,
    restoreSearchPayload,
    submitSearch,
  });
  const {
    activeRun,
    clearSearchRuns: clearSearchRunSession,
    executeSearch,
    packageData,
    searchRuns,
    submittedSearchPayload,
  } = runSession;
  const judgmentSession = useRetrievalJudgmentSession({ activeRun, searchRuns });
  const planSession = useRetrievalPlanSession({
    currentSearchSignature,
    formState,
    packageData,
    submittedSearchPayload,
  });
  const searchActions = useRetrievalWorkspaceSearchActions({
    applyFilterControl,
    clearAllFilterControls,
    clearFilterControl,
    executeSearch,
    hasCurrentPackage: Boolean(packageData),
    hasPlanPreviewPackage: Boolean(planSession.packageDataForPlanPreview),
    markCustomSearch,
    setClinicalDomain,
    setPlanControlNotice,
    setQuery,
    setSourceId,
    setSourceType,
    setStandardSystem,
    setTrustLevel,
  });
  const { tracePanelView } = useRetrievalWorkspaceView(packageData);
  const { clearSearchRuns } = useRetrievalWorkspaceClearActions({
    clearRelevanceJudgments: judgmentSession.clearRelevanceJudgments,
    clearSearchRunSession,
  });

  return {
    activeFacetFilters,
    activePresetId,
    clearSearchRuns,
    formError,
    formState,
    judgmentSession,
    planControlNotice,
    planSession,
    queryBuilderDraftActions,
    runSession,
    searchActions,
    tracePanelView,
    values,
  };
}
