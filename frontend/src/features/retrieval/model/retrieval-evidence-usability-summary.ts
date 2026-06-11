import type {
  EvidenceHitMatchExplanation,
  EvidenceSupportSummary,
  EvidenceUsabilitySummary,
  RetrievalEvidenceJudgment,
} from "./retrieval-evidence-types";
import { evidenceSupportStatus } from "./retrieval-evidence-support-summary";
import { evidenceUseGuidance } from "./retrieval-evidence-use-guidance-action";

export function evidenceUsabilitySummary({
  explanation,
  formatCount,
  judgment,
  judgmentLabel,
  summary,
}: {
  explanation: EvidenceHitMatchExplanation;
  formatCount: (count: number, singular: string) => string;
  judgment: RetrievalEvidenceJudgment | null;
  judgmentLabel: (value: RetrievalEvidenceJudgment["value"]) => string;
  summary: EvidenceSupportSummary;
}): EvidenceUsabilitySummary {
  const status = evidenceSupportStatus(summary);
  const guidance = evidenceUseGuidance({
    explanation,
    judgment,
    judgmentLabel,
    summary,
  });
  const traceability =
    summary.provenance_field_count > 0
      ? `${formatCount(summary.provenance_field_count, "provenance field")}`
      : "missing provenance";
  const grounding =
    summary.concept_count > 0 || summary.aspect_count > 0
      ? `${formatCount(
          summary.concept_count + summary.aspect_count,
          "grounding signal",
        )}`
      : "missing medical grounding";
  const judgmentLabelText = judgment
    ? `operator judged ${judgmentLabel(judgment.value)}`
    : "not operator-judged";
  const headline =
    status === "strong"
      ? "This result has enough support signals for operator evidence review."
      : status === "partial"
        ? "This result has partial support and needs review before use."
        : "This result is weak support for the submitted search.";
  const limitation =
    status === "strong"
      ? "Still verify the claim text and source locator before using it in an explanation."
      : summary.provenance_field_count === 0
        ? "Traceability is limited because no provenance field is available."
        : "Medical grounding or exact query support is incomplete.";

  return {
    checks: [
      `${formatCount(summary.matched_term_count, "matched term")}`,
      traceability,
      grounding,
      judgmentLabelText,
      explanation.bucketLabels.length
        ? "evidence bucket matched"
        : "not in evidence bucket",
    ],
    headline,
    limitation,
    recommendation: guidance.action,
    status,
  };
}
