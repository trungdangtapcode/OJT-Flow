import type { RetrievalPackage } from "../../../types";

export function retrievalCockpitRetrievalReport(packageData: RetrievalPackage) {
  return {
    strategy: packageData.trace.strategy,
    candidates_seen: packageData.trace.candidates_seen,
    hit_count: packageData.hits.length,
    top_evidence_ids: packageData.hits
      .slice(0, 10)
      .map((hit) => hit.evidence.evidence_id),
    filters_applied: packageData.trace.filters_applied,
    safety_flags: packageData.trace.safety_flags,
    warnings: packageData.trace.warnings,
  };
}
