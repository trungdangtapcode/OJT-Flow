import * as React from "react";

import type { RetrievalSearchPayload } from "../../../types";
import type { RetrievalSearchRun } from "../model/retrieval-run-summary";

export function useRetrievalRunSessionState() {
  const [lastSearchSignature, setLastSearchSignature] = React.useState<string | null>(null);
  const [submittedSearchPayload, setSubmittedSearchPayload] =
    React.useState<RetrievalSearchPayload | null>(null);
  const [searchRuns, setSearchRuns] = React.useState<RetrievalSearchRun[]>([]);
  const [activeRunId, setActiveRunId] = React.useState<string | null>(null);
  const [comparisonBaselineRunId, setComparisonBaselineRunId] =
    React.useState<string | null>(null);

  return {
    activeRunId,
    comparisonBaselineRunId,
    lastSearchSignature,
    searchRuns,
    setActiveRunId,
    setComparisonBaselineRunId,
    setLastSearchSignature,
    setSearchRuns,
    setSubmittedSearchPayload,
    submittedSearchPayload,
  };
}
