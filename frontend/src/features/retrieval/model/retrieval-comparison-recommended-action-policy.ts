import type {
  RetrievalComparisonJudgmentInput,
  RetrievalComparisonRecommendationInput,
  RetrievalComparisonRecommendedAction,
} from "./retrieval-comparison-types";
import {
  queryProfileActions,
  rulePackActions,
} from "./retrieval-comparison-recommended-action-configuration";
import {
  evidenceChangeActions,
  sourceDiversityActions,
} from "./retrieval-comparison-recommended-action-evidence";
import { judgmentActions } from "./retrieval-comparison-recommended-action-judgments";
import {
  coverageActions,
  qualitySignalActions,
  qualitySummaryActions,
} from "./retrieval-comparison-recommended-action-quality";
import { stableComparisonAction } from "./retrieval-comparison-recommended-action-stable";

export function comparisonReportRecommendedActions(
  comparison: RetrievalComparisonRecommendationInput,
  judgments: RetrievalComparisonJudgmentInput[],
): RetrievalComparisonRecommendedAction[] {
  const actions: RetrievalComparisonRecommendedAction[] = [
    ...qualitySummaryActions(comparison),
    ...coverageActions(comparison),
    ...queryProfileActions(comparison),
    ...rulePackActions(comparison),
    ...qualitySignalActions(comparison),
    ...evidenceChangeActions(comparison),
    ...sourceDiversityActions(comparison),
    ...judgmentActions(judgments),
  ];

  return stableComparisonAction(actions).sort(
    (left, right) =>
      left.priority - right.priority || left.source.localeCompare(right.source),
  );
}
