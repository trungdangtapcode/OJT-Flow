import type {
  RetrievalJudgmentEvaluationResult,
  RetrievalRelevanceJudgmentSummary,
} from "../../../types";
import { JudgmentEvaluationHelp } from "./judgment-evaluation-help";
import { JudgmentEvaluationOutcomeBadges } from "./judgment-evaluation-outcome-badges";
import {
  LocalJudgmentMetricGrid,
  ServerJudgmentMetricGrid,
} from "./judgment-evaluation-metrics";
import { EvaluationReadinessPanel } from "./judgment-evaluation-readiness";
import { EvaluationRecommendationList } from "./judgment-evaluation-recommendations";
import type {
  BadgeVariant,
  RelevanceJudgmentMetricsView,
} from "./judgment-evaluation-types";

export function JudgmentEvaluationDetailStack({
  formatCount,
  formatDecimal,
  formatNullableDecimal,
  formatNullablePercent,
  formatPercent,
  metrics,
  persistedEvaluation,
  persistedSummary,
  qualitySignalBadgeVariant,
}: {
  formatCount: (count: number, singular: string, plural?: string) => string;
  formatDecimal: (value: number) => string;
  formatNullableDecimal: (value: number | null) => string;
  formatNullablePercent: (value: number | null) => string;
  formatPercent: (value: number) => string;
  metrics: RelevanceJudgmentMetricsView;
  persistedEvaluation: RetrievalJudgmentEvaluationResult | null;
  persistedSummary: RetrievalRelevanceJudgmentSummary | null;
  qualitySignalBadgeVariant: (severity: string) => BadgeVariant;
}) {
  return (
    <>
      <JudgmentEvaluationHelp />
      {persistedEvaluation ? (
        <EvaluationReadinessPanel
          evaluation={persistedEvaluation}
          formatCount={formatCount}
          formatPercent={formatPercent}
        />
      ) : null}
      <LocalJudgmentMetricGrid
        formatNullableDecimal={formatNullableDecimal}
        formatNullablePercent={formatNullablePercent}
        formatPercent={formatPercent}
        metrics={metrics}
      />
      {persistedEvaluation ? (
        <ServerJudgmentMetricGrid
          evaluation={persistedEvaluation}
          formatCount={formatCount}
          formatDecimal={formatDecimal}
          formatNullableDecimal={formatNullableDecimal}
          formatPercent={formatPercent}
        />
      ) : null}
      {persistedEvaluation ? (
        <EvaluationRecommendationList
          evaluation={persistedEvaluation}
          qualitySignalBadgeVariant={qualitySignalBadgeVariant}
        />
      ) : null}
      <JudgmentEvaluationOutcomeBadges
        formatCount={formatCount}
        formatNullableDecimal={formatNullableDecimal}
        metrics={metrics}
        persistedSummary={persistedSummary}
      />
    </>
  );
}
