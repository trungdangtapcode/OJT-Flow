import type { RetrievalPackage } from "../../../types";
import type {
  RetrievalCockpitDiversitySelection,
  RetrievalCockpitDiversityStack,
} from "./retrieval-cockpit-runtime-types";
import { booleanValue, numberValue, recordValue, stringValue } from "./retrieval-runtime-values";

export function diversityFromPackage(
  packageData: RetrievalPackage,
): RetrievalCockpitDiversityStack {
  const diversity = recordValue(packageData.diversity ?? packageData.handoff_context.diversity);
  return {
    candidateSourceCount: numberValue(diversity.candidate_source_count) ?? 0,
    duplicateSelectedSourceCount:
      numberValue(diversity.duplicate_selected_source_count) ?? 0,
    enabled: booleanValue(diversity.enabled),
    lambda: numberValue(diversity.lambda_value) ?? numberValue(diversity.lambda),
    selectedHits: diversitySelectionDetailsValue(diversity.selected_hits),
    selectedSourceCount: numberValue(diversity.selected_source_count) ?? 0,
    selectionMode: stringValue(diversity.selection_mode, "unknown"),
  };
}

function diversitySelectionDetailsValue(
  value: unknown,
): RetrievalCockpitDiversitySelection[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      evidenceId: stringValue(item.evidence_id, ""),
      originalRank: numberValue(item.original_rank) ?? 0,
      reason: stringValue(item.reason, "Selected retrieval evidence."),
      redundancyScore: numberValue(item.redundancy_score) ?? 0,
      relevanceScore: numberValue(item.relevance_score) ?? 0,
      selectedRank: numberValue(item.selected_rank) ?? 0,
      selectionScore: numberValue(item.selection_score) ?? 0,
      sourceId: stringValue(item.source_id, ""),
    }))
    .filter((item) => item.evidenceId && item.selectedRank > 0);
}
