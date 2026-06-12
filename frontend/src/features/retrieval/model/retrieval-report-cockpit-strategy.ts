import type { RetrievalPackage } from "../../../types";

export function retrievalCockpitStrategyRecommendationReport(
  packageData: RetrievalPackage,
) {
  return (packageData.strategy_recommendations ?? []).map((recommendation) => ({
    recommendation_id: recommendation.recommendation_id,
    title: recommendation.title,
    technique: recommendation.technique,
    status: recommendation.status,
    rationale: recommendation.rationale,
    source_signal_codes: recommendation.source_signal_codes,
    suggested_filters: recommendation.suggested_filters,
    metadata: recommendation.metadata,
  }));
}
