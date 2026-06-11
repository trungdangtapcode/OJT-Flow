import type { RetrievalSearchRun } from "../model/retrieval-run-summary";
import type { RetrievalSearchPayload } from "../../../types";

export type CompletedSearchRunState = {
  activeRunId: string;
  lastSearchSignature: string;
  submittedSearchPayload: RetrievalSearchPayload;
};

export function completedSearchRunState({
  payload,
  run,
  signature,
}: {
  payload: RetrievalSearchPayload;
  run: RetrievalSearchRun;
  signature: string;
}): CompletedSearchRunState {
  return {
    activeRunId: run.runId,
    lastSearchSignature: signature,
    submittedSearchPayload: payload,
  };
}

export type RestoredSearchRunState = {
  activeRunId: string;
  comparisonBaselineRunId: string | null;
  lastSearchSignature: string;
};

export function restoredSearchRunState({
  comparisonBaselineRunId,
  run,
}: {
  comparisonBaselineRunId: string | null;
  run: RetrievalSearchRun;
}): RestoredSearchRunState {
  return {
    activeRunId: run.runId,
    comparisonBaselineRunId:
      comparisonBaselineRunId === run.runId ? null : comparisonBaselineRunId,
    lastSearchSignature: run.signature,
  };
}

export type ClearedSearchRunState = {
  activeRunId: null;
  comparisonBaselineRunId: null;
  searchRuns: RetrievalSearchRun[];
};

export function clearedSearchRunState(): ClearedSearchRunState {
  return {
    activeRunId: null,
    comparisonBaselineRunId: null,
    searchRuns: [],
  };
}
