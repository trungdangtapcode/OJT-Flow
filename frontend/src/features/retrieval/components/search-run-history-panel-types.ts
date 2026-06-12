import type { RetrievalSearchRun } from "../model/retrieval-run-summary";
import type { RelevanceJudgmentIndex } from "../model/retrieval-judgment-model";

export type SearchRunHistoryPanelProps = {
  activeRunId: string | null;
  comparisonBaselineRunId: string | null;
  copyTextToClipboard: (text: string) => Promise<void>;
  formatCount: (count: number, singular: string) => string;
  formatDecimal: (value: number) => string;
  formatPercent: (value: number) => string;
  isSearchPending: boolean;
  onClear: () => void;
  onRestore: (run: RetrievalSearchRun) => void;
  onSetComparisonBaseline: (runId: string | null) => void;
  relevanceJudgments: RelevanceJudgmentIndex;
  runs: RetrievalSearchRun[];
};
