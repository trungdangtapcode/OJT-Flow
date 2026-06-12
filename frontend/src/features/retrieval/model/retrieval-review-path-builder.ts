import type { RetrievalPackage } from "../../../types";
import { primaryRecommendedAction } from "./retrieval-review-actions";
import { retrievalReviewChecklist } from "./retrieval-review-checklist";
import { retrievalReviewGuidance } from "./retrieval-review-guidance";
import type { RetrievalReviewPath } from "./retrieval-review-types";

export function buildRetrievalReviewPath(packageData: RetrievalPackage): RetrievalReviewPath {
  const checks = retrievalReviewChecklist(packageData);
  return {
    candidateCount: packageData.trace.candidates_seen,
    checks,
    guidance: retrievalReviewGuidance(packageData, checks),
    hitCount: packageData.hits.length,
    primaryAction: primaryRecommendedAction(packageData),
    topSourceId: packageData.hits[0]?.evidence.source_id ?? null,
  };
}
