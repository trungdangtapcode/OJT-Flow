import { humanize } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";
import type { RetrievalReviewCheck } from "./retrieval-review-types";
import { topHitSupportSignalCount } from "./retrieval-review-support";
import {
  formatReviewCount,
  retrievalPackageWarnings,
} from "./retrieval-review-warnings";

export function retrievalReviewChecklist(packageData: RetrievalPackage): RetrievalReviewCheck[] {
  const qualitySummary = packageData.quality_summary ?? null;
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const warnings = retrievalPackageWarnings(packageData);
  const topHit = packageData.hits[0] ?? null;
  const supportSignalCount = topHit ? topHitSupportSignalCount(topHit) : 0;

  return [
    {
      code: "readiness",
      detail: qualitySummary
        ? `${humanize(qualitySummary.status)} package, score ${qualitySummary.score}/100. ${qualitySummary.top_action}`
        : "No quality summary was returned; treat the package as needing manual review.",
      label: "Readiness",
      status: qualitySummary
        ? qualitySummary.status === "ready"
          ? "ok"
          : qualitySummary.status === "blocked"
            ? "blocked"
            : "review"
        : "review",
    },
    {
      code: "required_support",
      detail: requiredBuckets.length
        ? `${requiredBuckets.length - missingBuckets.length}/${requiredBuckets.length} required evidence buckets are covered.`
        : "No required evidence bucket policy was returned for this package.",
      label: "Required support",
      status: missingBuckets.length ? "review" : "ok",
    },
    {
      code: "top_hit_support",
      detail: topHit
        ? `${topHit.evidence.source_id} has ${formatReviewCount(supportSignalCount, "support signal")} across terms, concepts, aspects, and provenance.`
        : "No ranked evidence was returned; review filters, corpus integrity, and query specificity.",
      label: "Top evidence",
      status: topHit ? (supportSignalCount > 0 ? "ok" : "review") : "blocked",
    },
    {
      code: "warnings",
      detail: warnings.length
        ? `${formatReviewCount(warnings.length, "warning")} must be reviewed before using the result order.`
        : "No retrieval trace or coverage warnings were returned.",
      label: "Warnings",
      status: warnings.length ? "review" : "ok",
    },
  ];
}
