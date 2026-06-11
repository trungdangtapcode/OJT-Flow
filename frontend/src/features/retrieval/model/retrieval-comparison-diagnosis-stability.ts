import type { RetrievalComparisonDiagnosis } from "./retrieval-comparison-types";

export function comparisonStableDiagnosis(
  diagnosis: RetrievalComparisonDiagnosis[],
): RetrievalComparisonDiagnosis[] {
  if (diagnosis.length) {
    return diagnosis;
  }

  return [
    {
      code: "comparison_stable",
      message:
        "Comparison is stable across query profile, concept grounding, search aspects, rules, quality, facets, evidence, and ranks.",
      severity: "success",
    },
  ];
}
