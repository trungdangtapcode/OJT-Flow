import type {
  EvidenceHitMatchExplanation,
  EvidenceSupportSummary,
  EvidenceUseGuidance,
  RetrievalEvidenceJudgment,
} from "./retrieval-evidence-types";
import { evidenceUseGuidanceReasons } from "./retrieval-evidence-use-guidance-reasons";

export function evidenceUseGuidance({
  explanation,
  judgment,
  judgmentLabel,
  summary,
}: {
  explanation: EvidenceHitMatchExplanation;
  judgment: RetrievalEvidenceJudgment | null;
  judgmentLabel: (value: RetrievalEvidenceJudgment["value"]) => string;
  summary: EvidenceSupportSummary;
}): EvidenceUseGuidance {
  const reasons = evidenceUseGuidanceReasons({
    explanation,
    judgment,
    judgmentLabel,
    summary,
  });
  if (explanation.supportStatus === "strong" && judgment?.value !== "not_relevant") {
    return {
      action:
        "Good candidate for evidence review. Confirm the claim and provenance before using it in a workflow explanation.",
      reasons,
      status: "strong",
      title: "Use with provenance check",
    };
  }
  if (explanation.supportStatus === "partial") {
    return {
      action:
        "Needs review before use. It has some support, but missing grounding or traceability can make the explanation weak.",
      reasons,
      status: "partial",
      title: "Review before relying on it",
    };
  }
  return {
    action:
      "Treat as weak support. Broaden or adjust the query, inspect source scope, or mark the hit not relevant if it does not answer the submitted question.",
    reasons,
    status: "weak",
    title: "Weak evidence support",
  };
}
