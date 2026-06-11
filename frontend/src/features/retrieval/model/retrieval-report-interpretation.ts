import type { RetrievalPackage } from "../../../types";
import {
  optionalStringValue,
  stringArrayValue,
} from "./retrieval-report-values";

export function retrievalInterpretationReport(packageData: RetrievalPackage) {
  const backendInterpretation = packageData.interpretation ?? null;
  if (backendInterpretation) {
    return {
      source: "backend",
      ...backendInterpretation,
    };
  }

  const topHit = packageData.hits[0] ?? null;
  const requiredBuckets =
    packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingRequiredBuckets = requiredBuckets.filter(
    (bucket) => bucket.hit_count === 0,
  );
  return {
    source: "frontend_fallback",
    status: topHit
      ? missingRequiredBuckets.length
        ? "support_gaps"
        : "ready_to_review"
      : "no_ranked_evidence",
    summary:
      packageData.remediation_summary ?? searchAnswerFallbackRemediation(packageData),
    top_evidence_id: topHit?.evidence.evidence_id ?? null,
    top_source_id: topHit?.evidence.source_id ?? null,
    top_score_driver:
      optionalStringValue(topHit?.match_explanation?.top_score_driver) ?? null,
    support_status:
      optionalStringValue(topHit?.match_explanation?.support_status) ?? null,
    matched_terms: topHit?.matched_terms.slice(0, 6) ?? [],
    concept_labels: stringArrayValue(topHit?.match_explanation?.concept_labels).slice(
      0,
      4,
    ),
    aspect_labels: stringArrayValue(topHit?.match_explanation?.aspect_labels).slice(
      0,
      4,
    ),
    required_bucket_count: requiredBuckets.length,
    covered_required_bucket_count:
      requiredBuckets.length - missingRequiredBuckets.length,
    missing_required_buckets: missingRequiredBuckets.map((bucket) => bucket.label),
    warning_count:
      (packageData.trace.warnings?.length ?? 0) +
      (packageData.coverage?.warnings?.length ?? 0),
    next_action_title: packageData.recommended_actions?.[0]?.title ?? null,
    next_action_detail: packageData.recommended_actions?.[0]?.description ?? null,
    metadata: {
      compatibility_fallback: true,
    },
  };
}

function searchAnswerFallbackRemediation(packageData: RetrievalPackage): string {
  const topAction = packageData.recommended_actions?.[0];
  if (topAction) return `${topAction.title}: ${topAction.description}`;
  const qualityAction = packageData.quality_summary?.top_action;
  if (qualityAction) return qualityAction;
  if (!packageData.hits.length) {
    return "Broaden search scope or inspect source inventory.";
  }
  return "Review the top evidence hit, readiness score, and source provenance before using this package.";
}
