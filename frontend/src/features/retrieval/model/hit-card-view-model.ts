import type {
  RetrievalEvidenceBucket,
  RetrievalHit,
} from "../../../types";
import {
  evidenceSignalsFromHit,
  evidenceSupportSummary,
  evidenceUsabilitySummary,
  hitMatchExplanation,
  provenanceEntriesFromEvidence,
} from "./retrieval-evidence-model";
import type {
  EvidenceHitMatchExplanation,
  EvidenceHitSignals,
  EvidenceProvenanceEntry,
  EvidenceSupportSummary,
  EvidenceUsabilitySummary,
  RetrievalEvidenceJudgment,
} from "./retrieval-evidence-types";

export type HitCardView = {
  evidenceCopyKey: string;
  hitSignals: EvidenceHitSignals;
  matchExplanation: EvidenceHitMatchExplanation;
  provenanceEntries: EvidenceProvenanceEntry[];
  supportSummary: EvidenceSupportSummary;
  usabilitySummary: EvidenceUsabilitySummary;
};

export function hitCardViewModel({
  evidenceBuckets,
  formatCount,
  hit,
  index,
  judgment,
  judgmentLabel,
}: {
  evidenceBuckets: RetrievalEvidenceBucket[];
  formatCount: (count: number, singular: string) => string;
  hit: RetrievalHit;
  index: number;
  judgment: RetrievalEvidenceJudgment | null;
  judgmentLabel: (value: RetrievalEvidenceJudgment["value"]) => string;
}): HitCardView {
  const provenanceEntries = provenanceEntriesFromEvidence(hit.evidence);
  const hitSignals = evidenceSignalsFromHit(hit);
  const supportSummary = evidenceSupportSummary({
    hit,
    provenanceEntries,
    signals: hitSignals,
  });
  const matchExplanation = hitMatchExplanation({
    buckets: evidenceBuckets,
    hit,
    provenanceEntries,
    signals: hitSignals,
  });
  const usabilitySummary = evidenceUsabilitySummary({
    explanation: matchExplanation,
    formatCount,
    judgment,
    judgmentLabel,
    summary: supportSummary,
  });

  return {
    evidenceCopyKey: `evidence-report-${hit.evidence.source_id}-${index}`,
    hitSignals,
    matchExplanation,
    provenanceEntries,
    supportSummary,
    usabilitySummary,
  };
}
