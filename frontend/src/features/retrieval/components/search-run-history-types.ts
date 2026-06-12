import type { ReactNode } from "react";

import type { RetrievalSearchPayload } from "../../../types";
import type { SearchRunSummaryView } from "../model/search-run-presentation";

export type SearchRunHistorySummary = SearchRunSummaryView & {
  candidateCount: number;
  conceptGrounding: unknown[];
  coverage: unknown[];
  queryAspects: unknown[];
  queryProfile: {
    label: string;
    retrievalMode: string;
    route: string;
  } | null;
  rulePackCount: number;
  serverSignature: string | null;
  topSourceId: string | null;
};

export type SearchRunHistoryRun = {
  payload: RetrievalSearchPayload;
  runId: string;
  submittedAt: string;
  summary: SearchRunHistorySummary;
};

export type SearchRunHistoryProps<TRun extends SearchRunHistoryRun> = {
  activeRunId: string | null;
  comparisonBaselineRunId: string | null;
  comparisonNode?: ReactNode;
  isSearchPending: boolean;
  onClear: () => void;
  onRestore: (run: TRun) => void;
  onSetComparisonBaseline: (runId: string | null) => void;
  runs: TRun[];
};
