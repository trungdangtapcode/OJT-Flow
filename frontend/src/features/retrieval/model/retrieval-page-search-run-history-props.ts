import type * as React from "react";

import { copyTextToClipboard } from "../components/copy-feedback";
import type { SearchRunHistoryPanel } from "../components/search-run-history-panel";
import {
  formatCount,
  formatDecimal,
  formatPercent,
} from "./retrieval-format";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";

export function retrievalPageSearchRunHistoryProps({
  searchMutation,
  workspace,
}: Pick<
  RetrievalPagePropsArgs,
  "searchMutation" | "workspace"
>): React.ComponentProps<typeof SearchRunHistoryPanel> {
  const { runSession } = workspace;

  return {
    activeRunId: runSession.activeRunId,
    comparisonBaselineRunId: runSession.comparisonBaselineRunId,
    copyTextToClipboard,
    formatCount,
    formatDecimal,
    formatPercent,
    isSearchPending: searchMutation.isPending,
    onClear: workspace.clearSearchRuns,
    onRestore: runSession.restoreSearchRun,
    onSetComparisonBaseline: runSession.setComparisonBaselineRunId,
    relevanceJudgments: workspace.judgmentSession.relevanceJudgments,
    runs: runSession.searchRuns,
  };
}
