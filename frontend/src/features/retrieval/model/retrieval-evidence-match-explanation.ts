import type {
  RetrievalEvidenceBucket,
  RetrievalHit,
} from "../../../types";
import {
  evidenceSupportSummary,
} from "./retrieval-evidence-support-summary";
import { backendMatchExplanationValues } from "./retrieval-evidence-match-explanation-backend";
import {
  fallbackMatchExplanationValues,
} from "./retrieval-evidence-match-explanation-fallback";
import { mergeMatchExplanationValues } from "./retrieval-evidence-match-explanation-merge";
import type {
  EvidenceHitMatchExplanation,
  EvidenceHitSignals,
  EvidenceProvenanceEntry,
} from "./retrieval-evidence-types";

export function hitMatchExplanation({
  buckets,
  hit,
  provenanceEntries,
  signals,
}: {
  buckets: RetrievalEvidenceBucket[];
  hit: RetrievalHit;
  provenanceEntries: EvidenceProvenanceEntry[];
  signals: EvidenceHitSignals;
}): EvidenceHitMatchExplanation {
  const supportSummary = evidenceSupportSummary({
    hit,
    provenanceEntries,
    signals,
  });
  const backendValues = backendMatchExplanationValues(hit);
  const fallbackValues = fallbackMatchExplanationValues({
    buckets,
    hit,
    provenanceEntries,
    signals,
  });
  return mergeMatchExplanationValues({
    backendValues,
    fallbackValues,
    supportSummary,
  });
}
