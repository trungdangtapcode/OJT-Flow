import type {
  RetrievalEvidenceBucket,
  RetrievalHit,
  RetrievalPackage,
} from "../../../types";
import { provenanceEntriesFromEvidence } from "./retrieval-evidence-provenance";
import type {
  EvidenceHitMatchExplanation,
  EvidenceHitSignals,
  EvidenceProvenanceEntry,
  EvidenceSupportMatrixRow,
  EvidenceSupportStatus,
  EvidenceSupportSummary,
  EvidenceUsabilitySummary,
  EvidenceUseGuidance,
  RetrievalEvidenceJudgment,
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
