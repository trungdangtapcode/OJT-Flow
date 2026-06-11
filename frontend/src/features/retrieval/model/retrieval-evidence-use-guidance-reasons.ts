import type {
  EvidenceHitMatchExplanation,
  EvidenceSupportSummary,
  RetrievalEvidenceJudgment,
} from "./retrieval-evidence-types";

export function evidenceUseGuidanceReasons({
  explanation,
  judgment,
  judgmentLabel,
  summary,
}: {
  explanation: EvidenceHitMatchExplanation;
  judgment: RetrievalEvidenceJudgment | null;
  judgmentLabel: (value: RetrievalEvidenceJudgment["value"]) => string;
  summary: EvidenceSupportSummary;
}): string[] {
  const reasons: string[] = [];
  if (summary.matched_term_count > 0) reasons.push("terms matched");
  else reasons.push("no exact terms");
  if (summary.provenance_field_count > 0) reasons.push("provenance present");
  else reasons.push("missing provenance");
  if (summary.concept_count > 0) reasons.push("concept grounded");
  if (summary.aspect_count > 0) reasons.push("query aspect supported");
  if (summary.concept_count === 0 && summary.aspect_count === 0) {
    reasons.push("missing medical grounding");
  }
  if (summary.ranking_signal_count > 0) reasons.push("ranking rule support");
  if (judgment) reasons.push(`judged ${judgmentLabel(judgment.value)}`);
  else reasons.push("unjudged");
  if (explanation.bucketLabels.length) reasons.push("evidence bucket matched");
  else reasons.push("not in evidence bucket");
  return reasons.slice(0, 8);
}
