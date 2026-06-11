import type * as React from "react";

import type { SearchResults } from "../components/search-results-panel";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";

export function retrievalPageSearchResultsProps({
  searchMutation,
  workspace,
}: Pick<
  RetrievalPagePropsArgs,
  "searchMutation" | "workspace"
>): React.ComponentProps<typeof SearchResults> {
  const { runSession, searchActions } = workspace;
  const { activeRun, packageData, submittedSearchPayload } = runSession;
  const judgmentSession = workspace.judgmentSession;

  return {
    activeFilters: workspace.activeFacetFilters,
    isJudgmentSyncing: judgmentSession.isJudgmentSyncing,
    isSearchPending: searchMutation.isPending,
    isStale: workspace.planSession.isSearchResultStale,
    onApplyFacet: searchActions.applySearchFilter,
    onClearAllFilters: searchActions.clearAllSearchFilters,
    onClearFilter: searchActions.clearSearchFilter,
    onRestoreSubmittedSearch: runSession.restoreSubmittedSearch,
    onSetJudgment: (evidence, value) =>
      judgmentSession.setHitJudgment(
        activeRun?.runId ?? null,
        activeRun?.payload.query ?? submittedSearchPayload?.query ?? "",
        activeRun?.signature ?? runSession.lastSearchSignature,
        evidence,
        value,
      ),
    packageData,
    persistedJudgmentEvaluation: judgmentSession.persistedJudgmentEvaluation,
    persistedJudgmentSummary: judgmentSession.persistedJudgmentSummary,
    relevanceJudgments: judgmentSession.relevanceJudgments,
    runId: activeRun?.runId ?? null,
    submittedSearchPayload,
  };
}
