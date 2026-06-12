import type { RetrievalPackage } from "../../../types";
import { diversityFromPackage } from "./retrieval-runtime-stack";

export function retrievalDiversityReport(packageData: RetrievalPackage) {
  const diversity = diversityFromPackage(packageData);
  return {
    enabled: diversity.enabled,
    selection_mode: diversity.selectionMode,
    candidate_source_count: diversity.candidateSourceCount,
    selected_source_count: diversity.selectedSourceCount,
    duplicate_selected_source_count: diversity.duplicateSelectedSourceCount,
    lambda: diversity.lambda,
    selected_hits: diversity.selectedHits.map((selection) => ({
      evidence_id: selection.evidenceId,
      source_id: selection.sourceId,
      selected_rank: selection.selectedRank,
      original_rank: selection.originalRank,
      relevance_score: selection.relevanceScore,
      redundancy_score: selection.redundancyScore,
      selection_score: selection.selectionScore,
      reason: selection.reason,
    })),
  };
}
