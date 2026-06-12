import type { RetrievalPackage } from "../../../types";

export function topHitSupportSignalCount(hit: RetrievalPackage["hits"][number]): number {
  return (
    (hit.matched_terms ?? []).length +
    arrayLength(hit.source_locator.concept_matches) +
    arrayLength(hit.source_locator.query_aspect_matches) +
    Object.keys(hit.evidence.locator ?? {}).length +
    Object.keys(hit.source_locator ?? {}).length
  );
}

function arrayLength(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}
