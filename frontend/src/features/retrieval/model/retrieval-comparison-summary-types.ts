import type { RetrievalComparisonDiagnosis } from "./retrieval-comparison-diagnosis-types";
import type { RetrievalComparisonRecommendationInput } from "./retrieval-comparison-recommendation-types";

export type RetrievalComparisonOperatorSummary = {
  bullets: string[];
  headline: string;
  reviewFocus: string[];
  status: "stable" | "review" | "improved";
};

export type RetrievalComparisonOperatorSummaryInput =
  RetrievalComparisonRecommendationInput & {
    diagnosis: RetrievalComparisonDiagnosis[];
    qualityScoreDelta: number | null;
  };
