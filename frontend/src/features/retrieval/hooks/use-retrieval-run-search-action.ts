import * as React from "react";

import type { RetrievalSearchPayload } from "../../../types";
import { executeRetrievalRunSearch } from "./retrieval-run-search-executor";
import type { UseRetrievalRunSessionArgs } from "./use-retrieval-run-session-types";
import type { useRetrievalRunSessionState } from "./use-retrieval-run-session-state";

type RetrievalRunSessionState = ReturnType<typeof useRetrievalRunSessionState>;

type UseRetrievalRunSearchActionArgs = Pick<
  UseRetrievalRunSessionArgs,
  "formState" | "onValidationError" | "submitSearch"
> & {
  createRunId: () => string;
  historyLimit: number;
  now: () => string;
  sessionState: Pick<
    RetrievalRunSessionState,
    | "setActiveRunId"
    | "setLastSearchSignature"
    | "setSearchRuns"
    | "setSubmittedSearchPayload"
  >;
};

export function useRetrievalRunSearchAction({
  createRunId,
  formState,
  historyLimit,
  now,
  onValidationError,
  sessionState,
  submitSearch,
}: UseRetrievalRunSearchActionArgs) {
  const {
    setActiveRunId,
    setLastSearchSignature,
    setSearchRuns,
    setSubmittedSearchPayload,
  } = sessionState;
  const completedRunSessionSetters = React.useMemo(
    () => ({
      setActiveRunId,
      setLastSearchSignature,
      setSearchRuns,
      setSubmittedSearchPayload,
    }),
    [
      setActiveRunId,
      setLastSearchSignature,
      setSearchRuns,
      setSubmittedSearchPayload,
    ],
  );

  const executeSearch = React.useCallback(
    async (overrides: Partial<RetrievalSearchPayload> = {}) => {
      await executeRetrievalRunSearch({
        createRunId,
        formState,
        historyLimit,
        now,
        onValidationError,
        overrides,
        sessionState: completedRunSessionSetters,
        submitSearch,
      });
    },
    [
      createRunId,
      formState,
      historyLimit,
      now,
      onValidationError,
      completedRunSessionSetters,
      submitSearch,
    ],
  );

  const runSearch = React.useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      await executeSearch();
    },
    [executeSearch],
  );

  return { executeSearch, runSearch };
}
