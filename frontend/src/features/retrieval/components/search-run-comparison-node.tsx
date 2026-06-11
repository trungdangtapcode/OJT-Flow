import {
  deltaBadgeVariant,
  formatSignedDelta,
  readinessGlanceLabel,
} from "../model/search-run-presentation";
import { SearchRunComparisonPanel } from "./search-run-comparison-panel";
import type { SearchRunHistoryPanelProps } from "./search-run-history-panel-types";
import type { useSearchRunComparisonView } from "./use-search-run-comparison-view";

export function SearchRunComparisonNode({
  comparisonView,
  copyTextToClipboard,
  formatCount,
  formatDecimal,
  formatPercent,
}: Pick<
  SearchRunHistoryPanelProps,
  "copyTextToClipboard" | "formatCount" | "formatDecimal" | "formatPercent"
> & {
  comparisonView: ReturnType<typeof useSearchRunComparisonView>;
}) {
  const {
    activeRunComparison,
    comparisonActionSummary,
    comparisonOperatorView,
    comparisonRecommendedActions,
    comparisonReportJson,
    comparisonRulePackViews,
  } = comparisonView;

  if (!activeRunComparison || !comparisonOperatorView) return null;

  return (
    <SearchRunComparisonPanel
      actionSummary={comparisonActionSummary}
      comparison={activeRunComparison}
      copyTextToClipboard={copyTextToClipboard}
      deltaBadgeVariant={deltaBadgeVariant}
      formatCount={formatCount}
      formatDecimal={formatDecimal}
      formatPercent={formatPercent}
      formatSignedDelta={formatSignedDelta}
      operatorSummary={comparisonOperatorView}
      readinessLabel={readinessGlanceLabel(activeRunComparison)}
      recommendedActions={comparisonRecommendedActions}
      reportJson={comparisonReportJson}
      rulePackChanges={comparisonRulePackViews}
    />
  );
}
