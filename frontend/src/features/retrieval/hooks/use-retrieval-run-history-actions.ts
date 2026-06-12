import * as React from "react";

import {
  type RetrievalSearchRun,
} from "../model/retrieval-run-summary";
import {
  clearedSearchRunState,
  restoredSearchRunState,
} from "./retrieval-run-session-transitions";
import type { UseRetrievalRunSessionArgs } from "./use-retrieval-run-session-types";
import type { useRetrievalRunSessionState } from "./use-retrieval-run-session-state";

type RetrievalRunSessionState = ReturnType<typeof useRetrievalRunSessionState>;

type UseRetrievalRunHistoryActionsArgs = Pick<
  UseRetrievalRunSessionArgs,
  "restoreSearchPayload"
> & {
  sessionState: Pick<
    RetrievalRunSessionState,
    | "comparisonBaselineRunId"
    | "setActiveRunId"
    | "setComparisonBaselineRunId"
    | "setLastSearchSignature"
    | "setSearchRuns"
    | "setSubmittedSearchPayload"
    | "submittedSearchPayload"
  >;
};

export function useRetrievalRunHistoryActions({
  restoreSearchPayload,
  sessionState,
}: UseRetrievalRunHistoryActionsArgs) {
  const {
    comparisonBaselineRunId,
    setActiveRunId,
    setComparisonBaselineRunId,
    setLastSearchSignature,
    setSearchRuns,
    setSubmittedSearchPayload,
    submittedSearchPayload,
  } = sessionState;

  const restoreSubmittedSearch = React.useCallback(() => {
    if (!submittedSearchPayload) return;
    restoreSearchPayload(submittedSearchPayload);
  }, [restoreSearchPayload, submittedSearchPayload]);

  const restoreSearchRun = React.useCallback(
    (run: RetrievalSearchRun) => {
      const restored = restoredSearchRunState({ comparisonBaselineRunId, run });
      restoreSearchPayload(run.payload);
      setSubmittedSearchPayload(run.payload);
      setLastSearchSignature(restored.lastSearchSignature);
      setActiveRunId(restored.activeRunId);
      setComparisonBaselineRunId(restored.comparisonBaselineRunId);
    },
    [
      comparisonBaselineRunId,
      restoreSearchPayload,
      setActiveRunId,
      setComparisonBaselineRunId,
      setLastSearchSignature,
      setSubmittedSearchPayload,
    ],
  );

  const clearSearchRuns = React.useCallback(() => {
    const cleared = clearedSearchRunState();
    setSearchRuns(cleared.searchRuns);
    setActiveRunId(cleared.activeRunId);
    setComparisonBaselineRunId(cleared.comparisonBaselineRunId);
  }, [setActiveRunId, setComparisonBaselineRunId, setSearchRuns]);

  return {
    clearSearchRuns,
    restoreSearchRun,
    restoreSubmittedSearch,
  };
}
