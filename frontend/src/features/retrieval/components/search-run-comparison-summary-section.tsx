import {
  RunComparisonAtAGlance,
  RunComparisonDiagnosis,
  RunComparisonMetrics,
  RunComparisonOperatorSummary,
  RunComparisonRecommendedActions,
  type RunComparisonOperatorSummaryView,
  type RunComparisonRecommendedActionSummaryView,
  type RunComparisonRecommendedActionView,
} from "./run-comparison-summary-panels";
import { SearchRunComparisonBaseline } from "./search-run-comparison-baseline";
import { SearchRunComparisonMetricGrid } from "./search-run-comparison-metric-grid";
import type {
  BadgeVariant,
  SearchRunComparisonPanelView,
} from "./search-run-comparison-types";
import { RunComparisonSourceDiversity } from "./source-diversity-panel";

export function SearchRunComparisonSummarySection({
  actionSummary,
  comparison,
  deltaBadgeVariant,
  formatCount,
  formatDecimal,
  formatPercent,
  formatSignedDelta,
  operatorSummary,
  readinessLabel,
  recommendedActions,
}: {
  actionSummary: RunComparisonRecommendedActionSummaryView;
  comparison: SearchRunComparisonPanelView;
  deltaBadgeVariant: (delta: number, positiveIsGood: boolean) => BadgeVariant;
  formatCount: (count: number, singular: string) => string;
  formatDecimal: (value: number) => string;
  formatPercent: (value: number) => string;
  formatSignedDelta: (delta: number) => string;
  operatorSummary: RunComparisonOperatorSummaryView;
  readinessLabel: string;
  recommendedActions: RunComparisonRecommendedActionView[];
}) {
  return (
    <>
      <RunComparisonOperatorSummary summary={operatorSummary} />
      <SearchRunComparisonBaseline baselineQuery={comparison.baselineQuery} />
      <RunComparisonAtAGlance
        actionSummary={actionSummary}
        comparison={comparison}
        formatPercent={formatPercent}
        formatSignedDelta={formatSignedDelta}
        readinessLabel={readinessLabel}
      />
      <RunComparisonDiagnosis diagnosis={comparison.diagnosis} formatCount={formatCount} />
      <RunComparisonRecommendedActions
        actions={recommendedActions}
        actionSummary={actionSummary}
        formatCount={formatCount}
      />
      <RunComparisonMetrics
        formatDecimal={formatDecimal}
        formatPercent={formatPercent}
        metrics={comparison.metrics}
      />
      <RunComparisonSourceDiversity
        comparison={comparison.sourceDiversityComparison}
        formatPercent={formatPercent}
        formatSignedDelta={formatSignedDelta}
      />
      <SearchRunComparisonMetricGrid
        candidateDelta={comparison.candidateDelta}
        deltaBadgeVariant={deltaBadgeVariant}
        formatSignedDelta={formatSignedDelta}
        hitDelta={comparison.hitDelta}
        qualityWarningDelta={comparison.qualityWarningDelta}
        warningDelta={comparison.warningDelta}
      />
    </>
  );
}
