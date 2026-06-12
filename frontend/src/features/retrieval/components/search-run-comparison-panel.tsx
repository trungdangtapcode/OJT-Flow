import {
  type RunComparisonOperatorSummaryView,
  type RunComparisonRecommendedActionSummaryView,
  type RunComparisonRecommendedActionView,
} from "./run-comparison-summary-panels";
import {
  type RetrievalRulePackChangeView,
} from "./run-comparison-detail-panels";
import { SearchRunComparisonDetailSection } from "./search-run-comparison-detail-section";
import { SearchRunComparisonHelp } from "./search-run-comparison-help";
import { SearchRunComparisonHeader } from "./search-run-comparison-header";
import { SearchRunComparisonSummarySection } from "./search-run-comparison-summary-section";
import { SearchRunComparisonTopSource } from "./search-run-comparison-top-source";
import type {
  BadgeVariant,
  SearchRunComparisonPanelView,
} from "./search-run-comparison-types";
export type { SearchRunComparisonPanelView } from "./search-run-comparison-types";

export function SearchRunComparisonPanel({
  actionSummary,
  comparison,
  copyTextToClipboard,
  deltaBadgeVariant,
  formatCount,
  formatDecimal,
  formatPercent,
  formatSignedDelta,
  operatorSummary,
  readinessLabel,
  recommendedActions,
  reportJson,
  rulePackChanges,
}: {
  actionSummary: RunComparisonRecommendedActionSummaryView;
  comparison: SearchRunComparisonPanelView;
  copyTextToClipboard: (text: string) => Promise<void>;
  deltaBadgeVariant: (delta: number, positiveIsGood: boolean) => BadgeVariant;
  formatCount: (count: number, singular: string) => string;
  formatDecimal: (value: number) => string;
  formatPercent: (value: number) => string;
  formatSignedDelta: (delta: number) => string;
  operatorSummary: RunComparisonOperatorSummaryView;
  readinessLabel: string;
  recommendedActions: RunComparisonRecommendedActionView[];
  reportJson: string;
  rulePackChanges: RetrievalRulePackChangeView[];
}) {
  return (
    <div
      aria-label="Search run comparison"
      className="mt-1 grid gap-3 rounded-md border border-border bg-muted/25 p-3 text-sm"
    >
      <SearchRunComparisonHeader
        copyTextToClipboard={copyTextToClipboard}
        qualitySummaryChanged={comparison.qualitySummaryChanged}
        queryProfileChanged={comparison.queryProfileChanged}
        reportJson={reportJson}
        rulePackChanged={comparison.rulePackChanged}
        topSourceChanged={comparison.topSourceChanged}
      />
      <SearchRunComparisonHelp />
      <SearchRunComparisonSummarySection
        actionSummary={actionSummary}
        comparison={comparison}
        deltaBadgeVariant={deltaBadgeVariant}
        formatCount={formatCount}
        formatDecimal={formatDecimal}
        formatPercent={formatPercent}
        formatSignedDelta={formatSignedDelta}
        operatorSummary={operatorSummary}
        readinessLabel={readinessLabel}
        recommendedActions={recommendedActions}
      />
      <SearchRunComparisonDetailSection
        comparison={comparison}
        formatCount={formatCount}
        rulePackChanges={rulePackChanges}
      />
      <SearchRunComparisonTopSource comparison={comparison} />
    </div>
  );
}
