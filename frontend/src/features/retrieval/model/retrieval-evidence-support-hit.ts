import type { RetrievalHit } from "../../../types";
import { evidenceSignalsFromHit } from "./retrieval-evidence-signals";
import { evidenceSupportSummary } from "./retrieval-evidence-support-summary";
import type {
  EvidenceProvenanceEntry,
  EvidenceSupportSummary,
} from "./retrieval-evidence-types";

export function evidenceSupportSummaryForHit(
  hit: RetrievalHit,
  provenanceEntries: EvidenceProvenanceEntry[],
): EvidenceSupportSummary {
  return evidenceSupportSummary({
    hit,
    provenanceEntries,
    signals: evidenceSignalsFromHit(hit),
  });
}
