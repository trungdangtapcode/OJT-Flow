import type { RetrievalHit } from "../../../types";
import type {
  EvidenceHitSignals,
  EvidenceProvenanceEntry,
  EvidenceSupportMatrixRow,
  EvidenceSupportStatus,
  EvidenceSupportSummary,
} from "./retrieval-evidence-types";

export function evidenceSupportSummary({
  hit,
  provenanceEntries,
  signals,
}: {
  hit: RetrievalHit;
  provenanceEntries: EvidenceProvenanceEntry[];
  signals: EvidenceHitSignals;
}): EvidenceSupportSummary {
  return {
    aspect_count: signals.queryAspectMatches.length,
    concept_count: signals.conceptMatches.length,
    matched_term_count: hit.matched_terms.length,
    provenance_field_count: provenanceEntries.length,
    ranking_signal_count: signals.rankingBoostSignals.length,
  };
}

export function evidenceSupportStatus(
  summary: EvidenceSupportSummary,
): EvidenceSupportStatus {
  if (
    summary.matched_term_count > 0 &&
    summary.provenance_field_count > 0 &&
    (summary.concept_count > 0 || summary.aspect_count > 0)
  ) {
    return "strong";
  }
  if (summary.matched_term_count > 0 || summary.provenance_field_count > 0) {
    return "partial";
  }
  return "weak";
}

export function supportStatusBadgeVariant(
  status: EvidenceSupportMatrixRow["supportStatus"],
): "success" | "warning" | "destructive" | "muted" {
  if (status === "strong") return "success";
  if (status === "partial") return "warning";
  return "destructive";
}
