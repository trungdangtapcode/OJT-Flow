import * as React from "react";

import {
  defaultSearchRunHistoryLimit,
  shouldClearComparisonBaseline,
} from "./retrieval-run-session-history";
import type { UseRetrievalRunSessionArgs } from "./use-retrieval-run-session-types";
import { useRetrievalRunSessionState } from "./use-retrieval-run-session-state";
import { useActiveRetrievalRunState } from "./use-active-retrieval-run-state";
import { useRetrievalRunSessionActions } from "./use-retrieval-run-session-actions";

export function useRetrievalRunSession({
  createRunId = () => crypto.randomUUID(),
  formState,
  historyLimit = defaultSearchRunHistoryLimit,
  latestPackageData,
  now = () => new Date().toISOString(),
  onValidationError,
  restoreSearchPayload,
  submitSearch,
}: UseRetrievalRunSessionArgs) {
  const sessionState = useRetrievalRunSessionState();
  const {
    activeRunId,
    comparisonBaselineRunId,
    lastSearchSignature,
    searchRuns,
    setActiveRunId,
    setComparisonBaselineRunId,
    submittedSearchPayload,
  } = sessionState;

  const { activeRun, packageData } = useActiveRetrievalRunState({
    activeRunId,
    latestPackageData,
    searchRuns,
  });
  const {
    clearSearchRuns,
    executeSearch,
    restoreSearchRun,
    restoreSubmittedSearch,
    runSearch,
  } = useRetrievalRunSessionActions({
    createRunId,
    formState,
    historyLimit,
    latestPackageData,
    now,
    onValidationError,
    restoreSearchPayload,
    sessionState,
    submitSearch,
  });

  React.useEffect(() => {
    if (shouldClearComparisonBaseline(comparisonBaselineRunId, searchRuns)) {
      setComparisonBaselineRunId(null);
    }
  }, [comparisonBaselineRunId, searchRuns, setComparisonBaselineRunId]);

  return {
    activeRun,
    activeRunId,
    clearSearchRuns,
    comparisonBaselineRunId,
    executeSearch,
    lastSearchSignature,
    packageData,
    restoreSearchRun,
    restoreSubmittedSearch,
    runSearch,
    searchRuns,
    setActiveRunId,
    setComparisonBaselineRunId,
    submittedSearchPayload,
  };
}
