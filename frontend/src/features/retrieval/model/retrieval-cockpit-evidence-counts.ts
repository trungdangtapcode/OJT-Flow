import type { RetrievalPackage } from "../../../types";
import { recordValue, stringArrayValue } from "./retrieval-runtime-values";

export function coverageGapCountFromPackage(packageData: RetrievalPackage): number {
  const coverage = packageData.coverage;
  return [...(coverage?.standard_system ?? []), ...(coverage?.query_aspects ?? [])]
    .filter((item) => item.selected_count === 0)
    .length;
}

export function conceptGroundingCountFromPackage(packageData: RetrievalPackage): number {
  const conceptKeys = new Set<string>();
  for (const hit of packageData.hits) {
    const explanation = recordValue(hit.match_explanation);
    for (const conceptId of stringArrayValue(explanation.concept_ids)) {
      conceptKeys.add(conceptId);
    }
  }
  return conceptKeys.size;
}
