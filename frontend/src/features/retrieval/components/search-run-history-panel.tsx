import { SearchRunComparisonNode } from "./search-run-comparison-node";
import { SearchRunHistory } from "./search-run-history";
import type { SearchRunHistoryPanelProps } from "./search-run-history-panel-types";
import { useSearchRunComparisonView } from "./use-search-run-comparison-view";

export function SearchRunHistoryPanel({
  activeRunId,
  comparisonBaselineRunId,
  copyTextToClipboard,
  formatCount,
  formatDecimal,
  formatPercent,
  isSearchPending,
  onClear,
  onRestore,
  onSetComparisonBaseline,
  relevanceJudgments,
  runs,
}: SearchRunHistoryPanelProps) {
  const comparisonView = useSearchRunComparisonView({
    activeRunId,
    comparisonBaselineRunId,
    relevanceJudgments,
    runs,
  });

  return (
    <SearchRunHistory
      activeRunId={activeRunId}
      comparisonBaselineRunId={comparisonBaselineRunId}
      comparisonNode={
        <SearchRunComparisonNode
          comparisonView={comparisonView}
          copyTextToClipboard={copyTextToClipboard}
          formatCount={formatCount}
          formatDecimal={formatDecimal}
          formatPercent={formatPercent}
        />
      }
      isSearchPending={isSearchPending}
      onClear={onClear}
      onRestore={onRestore}
      onSetComparisonBaseline={onSetComparisonBaseline}
      runs={runs}
    />
  );
}
