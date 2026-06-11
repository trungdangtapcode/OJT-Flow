import type { RetrievalPackage } from "../../../types";
import {
  evidenceSignalsFromHit,
  evidenceSupportSummary,
  hitMatchExplanation,
  provenanceEntriesFromEvidence,
} from "./retrieval-evidence-model";

export function retrievalCockpitEvidenceHitReports(packageData: RetrievalPackage) {
  const buckets = packageData.evidence_buckets ?? [];
  return packageData.hits.map((hit, index) => {
    const provenanceEntries = provenanceEntriesFromEvidence(hit.evidence);
    const signals = evidenceSignalsFromHit(hit);
    return {
      rank: index + 1,
      evidence_id: hit.evidence.evidence_id,
      source_id: hit.evidence.source_id,
      source_type: hit.evidence.source_type,
      trust_level: hit.evidence.trust_level,
      confidence: hit.evidence.confidence ?? null,
      score: hit.score,
      support_summary: evidenceSupportSummary({
        hit,
        provenanceEntries,
        signals,
      }),
      match_explanation: hitMatchExplanation({
        buckets,
        hit,
        provenanceEntries,
        signals,
      }),
    };
  });
}
