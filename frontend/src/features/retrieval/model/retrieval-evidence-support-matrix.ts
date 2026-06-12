import type {
  RetrievalEvidenceBucket,
  RetrievalHit,
  RetrievalPackage,
} from "../../../types";
import { provenanceEntriesFromEvidence } from "./retrieval-evidence-provenance";
import { evidenceSupportStatus } from "./retrieval-evidence-support-summary";
import type {
  EvidenceProvenanceEntry,
  EvidenceSupportMatrixRow,
  EvidenceSupportSummary,
  RetrievalEvidenceJudgment,
} from "./retrieval-evidence-types";

export function evidenceSupportMatrixRows({
  formatConfidence,
  packageData,
  relevanceJudgments,
  runId,
  standardSystemValue,
  summaryForHit,
}: {
  formatConfidence: (confidence: number | null | undefined) => string;
  packageData: RetrievalPackage;
  relevanceJudgments: Record<string, RetrievalEvidenceJudgment | null | undefined>;
  runId: string | null;
  standardSystemValue: (value: unknown) => string | null;
  summaryForHit: (
    hit: RetrievalHit,
    provenanceEntries: EvidenceProvenanceEntry[],
  ) => EvidenceSupportSummary;
}): EvidenceSupportMatrixRow[] {
  const bucketLabelsByEvidenceId = evidenceBucketLabelsByEvidenceId(
    packageData.evidence_buckets ?? [],
  );
  return packageData.hits.map((hit, index) => {
    const provenanceEntries = provenanceEntriesFromEvidence(hit.evidence);
    const summary = summaryForHit(hit, provenanceEntries);
    const judgment = runId
      ? relevanceJudgments[`${runId}:${hit.evidence.evidence_id}`] ?? null
      : null;
    return {
      aspectCount: summary.aspect_count,
      bucketLabels: bucketLabelsByEvidenceId.get(hit.evidence.evidence_id) ?? [],
      conceptCount: summary.concept_count,
      confidenceLabel: formatConfidence(hit.evidence.confidence),
      evidenceId: hit.evidence.evidence_id,
      judgment,
      matchedTermCount: summary.matched_term_count,
      provenanceCount: summary.provenance_field_count,
      rank: index + 1,
      score: hit.score,
      sourceId: hit.evidence.source_id,
      sourceType: String(hit.evidence.source_type),
      standardSystem: standardSystemValue(hit.evidence.locator.standard_system),
      supportStatus: evidenceSupportStatus(summary),
    };
  });
}

export function evidenceBucketLabelsByEvidenceId(
  buckets: RetrievalEvidenceBucket[],
): Map<string, string[]> {
  const labelsByEvidenceId = new Map<string, string[]>();
  for (const bucket of buckets) {
    for (const evidenceId of bucket.evidence_ids ?? []) {
      const labels = labelsByEvidenceId.get(evidenceId) ?? [];
      labels.push(bucket.label);
      labelsByEvidenceId.set(evidenceId, labels);
    }
  }
  return labelsByEvidenceId;
}
