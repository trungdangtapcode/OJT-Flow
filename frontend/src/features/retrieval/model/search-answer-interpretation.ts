import type { RetrievalPackage } from "../../../types";
import { searchAnswerFallbackRemediation } from "./search-answer-status";
import { searchAnswerWarnings } from "./search-answer-warnings";

export function fallbackInterpretation(packageData: RetrievalPackage) {
  const topHit = packageData.hits[0] ?? null;
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingRequiredBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  return {
    source: "frontend_search_answer_fallback",
    status: topHit
      ? missingRequiredBuckets.length
        ? "support_gaps"
        : "ready_to_review"
      : "no_ranked_evidence",
    summary: packageData.remediation_summary ?? searchAnswerFallbackRemediation(packageData),
    top_evidence_id: topHit?.evidence.evidence_id ?? null,
    top_source_id: topHit?.evidence.source_id ?? null,
    matched_terms: topHit?.matched_terms.slice(0, 6) ?? [],
    required_bucket_count: requiredBuckets.length,
    covered_required_bucket_count: requiredBuckets.length - missingRequiredBuckets.length,
    missing_required_buckets: missingRequiredBuckets.map((bucket) => bucket.label),
    warning_count: searchAnswerWarnings(packageData).length,
  };
}
