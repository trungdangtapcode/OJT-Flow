import type { ConceptCandidateStack } from "./retrieval-query-analysis-types";
import {
  numberValue,
  optionalStringValue,
  recordValue,
  stringArrayValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";

export function conceptCandidatesValue(value: unknown): ConceptCandidateStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      clinicalDomain: optionalStringValue(item.clinical_domain),
      code: optionalStringValue(item.code),
      conceptId: stringValue(item.concept_id, "concept"),
      confidence: numberValue(item.confidence) ?? 0,
      displayName: stringValue(item.display_name, "Unknown concept"),
      matchedAliases: stringArrayValue(item.matched_aliases),
      standardSystem: stringValue(item.standard_system, "unknown"),
    }))
    .filter((item) => item.conceptId !== "concept" && item.standardSystem !== "unknown");
}
