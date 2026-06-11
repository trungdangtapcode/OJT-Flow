import type {
  RetrievalComparisonDiagnosis,
  RetrievalComparisonDiagnosticInput,
} from "./retrieval-comparison-types";

export function comparisonProfileDiagnosis(
  comparison: RetrievalComparisonDiagnosticInput,
): RetrievalComparisonDiagnosis[] {
  const diagnosis: RetrievalComparisonDiagnosis[] = [];

  if (comparison.queryProfileChanged) {
    diagnosis.push({
      code: "query_profile_changed",
      message:
        "Query profile, route, retrieval mode, or complexity changed between runs.",
      severity: "warning",
    });
  }

  if (comparison.rulePackChanged) {
    diagnosis.push({
      code: "rule_pack_changed",
      message: "Retrieval rule-pack fingerprints changed between runs.",
      severity: "warning",
    });
  }

  if (
    comparison.queryAspectComparison.added.length ||
    comparison.queryAspectComparison.removed.length
  ) {
    diagnosis.push({
      code: "query_aspect_plan_changed",
      message: "Search aspect coverage plan changed between runs.",
      severity: "warning",
    });
  }

  if (
    comparison.conceptGroundingComparison.added.length ||
    comparison.conceptGroundingComparison.removed.length
  ) {
    diagnosis.push({
      code: "concept_grounding_changed",
      message: "Controlled medical concept grounding changed between runs.",
      severity: "warning",
    });
  }

  return diagnosis;
}
