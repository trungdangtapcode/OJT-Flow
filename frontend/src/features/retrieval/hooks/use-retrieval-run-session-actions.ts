import type { UseRetrievalRunSessionArgs } from "./use-retrieval-run-session-types";
import type { useRetrievalRunSessionState } from "./use-retrieval-run-session-state";
import { useRetrievalRunHistoryActions } from "./use-retrieval-run-history-actions";
import { useRetrievalRunSearchAction } from "./use-retrieval-run-search-action";

type RetrievalRunSessionState = ReturnType<typeof useRetrievalRunSessionState>;

type UseRetrievalRunSessionActionsArgs = UseRetrievalRunSessionArgs & {
  createRunId: () => string;
  historyLimit: number;
  now: () => string;
  sessionState: RetrievalRunSessionState;
};

export function useRetrievalRunSessionActions({
  createRunId,
  formState,
  historyLimit,
  now,
  onValidationError,
  restoreSearchPayload,
  sessionState,
  submitSearch,
}: UseRetrievalRunSessionActionsArgs) {
  const { executeSearch, runSearch } = useRetrievalRunSearchAction({
    createRunId,
    formState,
    historyLimit,
    now,
    onValidationError,
    sessionState,
    submitSearch,
  });
  const {
    clearSearchRuns,
    restoreSearchRun,
    restoreSubmittedSearch,
  } = useRetrievalRunHistoryActions({
    restoreSearchPayload,
    sessionState,
  });

  return {
    clearSearchRuns,
    executeSearch,
    restoreSearchRun,
    restoreSubmittedSearch,
    runSearch,
  };
}
