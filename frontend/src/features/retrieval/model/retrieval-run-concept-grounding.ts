import type { RetrievalHit, RetrievalPackage } from "../../../types";
import type {
  ConceptGroundingSummary,
  ConceptMatchSignal,
} from "./retrieval-run-summary-types";
import {
  optionalStringValue,
  recordValue,
  stringValue,
} from "./retrieval-run-summary-values";

export function conceptGroundingSummariesFromPackage(
  packageData: RetrievalPackage,
): ConceptGroundingSummary[] {
  const counts = new Map<string, ConceptGroundingSummary>();
  for (const hit of packageData.hits) {
    for (const concept of conceptMatchesFromHit(hit)) {
      const key = conceptGroundingKey(concept);
      const current = counts.get(key);
      if (current) {
        current.evidenceCount += 1;
      } else {
        counts.set(key, {
          code: concept.code,
          conceptId: concept.conceptId,
          displayName: concept.displayName,
          evidenceCount: 1,
          standardSystem: concept.standardSystem,
        });
      }
    }
  }
  return [...counts.values()].sort(
    (left, right) =>
      left.standardSystem.localeCompare(right.standardSystem) ||
      left.displayName.localeCompare(right.displayName),
  );
}

export function conceptGroundingKey(
  concept: Pick<ConceptGroundingSummary, "code" | "conceptId" | "standardSystem">,
): string {
  return `${concept.standardSystem}:${concept.code ?? ""}:${concept.conceptId}`;
}

function conceptMatchesFromHit(hit: RetrievalHit): ConceptMatchSignal[] {
  const matches = hit.source_locator.concept_matches;
  if (!Array.isArray(matches)) return [];
  return matches
    .map((item) => recordValue(item))
    .map((item) => ({
      code: optionalStringValue(item.code),
      conceptId: stringValue(item.concept_id, ""),
      displayName: stringValue(item.display_name, "Medical concept"),
      standardSystem: stringValue(item.standard_system, "unknown"),
    }))
    .filter((item) => item.conceptId);
}
