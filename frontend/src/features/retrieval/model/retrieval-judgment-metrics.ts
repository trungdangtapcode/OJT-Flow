import type { RetrievalHit } from "../../../types";
import { isNonPositiveJudgment } from "./retrieval-judgment-labels";
import type {
  RelevanceJudgment,
  RelevanceJudgmentMetrics,
} from "./retrieval-judgment-types";

export function relevanceJudgmentMetrics(
  hits: RetrievalHit[],
  judgments: RelevanceJudgment[],
): RelevanceJudgmentMetrics {
  const totalHits = hits.length;
  const ratingsByEvidenceId = new Map(
    judgments.map((judgment) => [
      judgment.evidenceId,
      judgment.rating,
    ]),
  );
  const rankedRatings = hits.map(
    (hit) => ratingsByEvidenceId.get(hit.evidence.evidence_id) ?? 0,
  );
  const judgedRatings = judgments.map((judgment) => judgment.rating);
  const relevantCount = judgments.filter(
    (judgment) => judgment.value === "relevant",
  ).length;
  const partialCount = judgments.filter(
    (judgment) => judgment.value === "partial",
  ).length;
  const notRelevantCount = judgments.filter(
    (judgment) =>
      judgment.value === "not_relevant" || isNonPositiveJudgment(judgment.value),
  ).length;
  const unsafeCount = judgments.filter((judgment) => judgment.value === "unsafe").length;
  const staleCount = judgments.filter((judgment) => judgment.value === "stale").length;
  const sourcePolicyBlockedCount = judgments.filter(
    (judgment) => judgment.value === "source_policy_blocked",
  ).length;
  const positiveJudgments = relevantCount + partialCount;
  const dcg = discountedCumulativeGain(rankedRatings);
  const idealDcg = discountedCumulativeGain(
    [...rankedRatings].sort((left, right) => right - left),
  );

  return {
    averageRating: judgedRatings.length
      ? judgedRatings.reduce((total, rating) => total + rating, 0) / judgedRatings.length
      : null,
    judgedCount: judgments.length,
    judgedPrecision: judgments.length ? positiveJudgments / judgments.length : null,
    judgmentCoverage: totalHits ? judgments.length / totalHits : 0,
    ndcgAtK: idealDcg ? dcg / idealDcg : null,
    notRelevantCount,
    partialCount,
    precisionAtK: totalHits ? positiveJudgments / totalHits : 0,
    relevantCount,
    sourcePolicyBlockedCount,
    staleCount,
    totalHits,
    unsafeCount,
  };
}

export function discountedCumulativeGain(ratings: number[]): number {
  return ratings.reduce((total, rating, index) => {
    if (rating <= 0) return total;
    return total + (2 ** rating - 1) / Math.log2(index + 2);
  }, 0);
}
