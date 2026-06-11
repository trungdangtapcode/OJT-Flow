import type { RetrievalRunEvidenceComparison } from "./retrieval-run-comparison-evidence";
import type { RetrievalRankChange } from "./retrieval-run-comparison-types";

export type RetrievalRunComparisonMetricInput = {
  activeCount: number;
  addedCount: number;
  baselineCount: number;
  rankChanges: RetrievalRankChange[];
  retainedCount: number;
  removedCount: number;
};

export function retrievalRunComparisonMetricInput({
  evidenceComparison,
  rankChanges,
}: {
  evidenceComparison: RetrievalRunEvidenceComparison;
  rankChanges: RetrievalRankChange[];
}): RetrievalRunComparisonMetricInput {
  return {
    activeCount: evidenceComparison.activeEvidenceIds.length,
    addedCount: evidenceComparison.addedEvidenceIds.length,
    baselineCount: evidenceComparison.baselineEvidenceIds.length,
    rankChanges,
    retainedCount: evidenceComparison.retainedEvidenceIds.length,
    removedCount: evidenceComparison.removedEvidenceIds.length,
  };
}
