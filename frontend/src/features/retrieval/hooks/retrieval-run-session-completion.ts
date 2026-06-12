import type * as React from "react";

import type { RetrievalSearchPayload } from "../../../types";
import type { RetrievalSearchRun } from "../model/retrieval-run-summary";
import { upsertSearchRunHistory } from "./retrieval-run-session-history";
import { completedSearchRunState } from "./retrieval-run-session-transitions";

export type CompletedRunSessionSetters = {
  setActiveRunId: (value: string) => void;
  setLastSearchSignature: (value: string) => void;
  setSearchRuns: React.Dispatch<React.SetStateAction<RetrievalSearchRun[]>>;
  setSubmittedSearchPayload: (value: RetrievalSearchPayload) => void;
};

export function commitCompletedSearchRun({
  historyLimit,
  payload,
  run,
  sessionState,
  signature,
}: {
  historyLimit: number;
  payload: RetrievalSearchPayload;
  run: RetrievalSearchRun;
  sessionState: CompletedRunSessionSetters;
  signature: string;
}) {
  const completed = completedSearchRunState({ payload, run, signature });
  sessionState.setSearchRuns((current) =>
    upsertSearchRunHistory(current, run, historyLimit),
  );
  sessionState.setActiveRunId(completed.activeRunId);
  sessionState.setSubmittedSearchPayload(completed.submittedSearchPayload);
  sessionState.setLastSearchSignature(completed.lastSearchSignature);
}
