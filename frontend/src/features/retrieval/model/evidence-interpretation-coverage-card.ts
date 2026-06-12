import type { EvidenceInterpretationCard } from "./evidence-interpretation-types";
import type { EvidenceInterpretationCardContext } from "./evidence-interpretation-cards";
import {
  formatEvidenceInterpretationCount,
  packageWarnings,
} from "./evidence-interpretation-values";

export function coverageInterpretationCard({
  backend,
  missingRequiredBuckets,
  packageData,
  requiredBuckets,
}: Pick<
  EvidenceInterpretationCardContext,
  "backend" | "missingRequiredBuckets" | "packageData" | "requiredBuckets"
>): EvidenceInterpretationCard {
  const warningCount = packageWarnings(packageData).length;
  const coverageItemCount =
    (packageData.coverage?.standard_system.length ?? 0) +
    (packageData.coverage?.query_aspects?.length ?? 0);
  const requiredBucketCount = backend?.required_bucket_count ?? requiredBuckets.length;
  const coveredRequiredBucketCount =
    backend?.covered_required_bucket_count ??
    requiredBuckets.length - missingRequiredBuckets.length;
  const missingRequiredBucketLabels =
    backend?.missing_required_buckets?.length
      ? backend.missing_required_buckets
      : missingRequiredBuckets.map((bucket) => bucket.label);

  return {
    detail: missingRequiredBucketLabels.length
      ? `Missing required support: ${missingRequiredBucketLabels.join(", ")}`
      : "The package has no missing required evidence buckets.",
    items: [
      packageData.coverage ? `${formatEvidenceInterpretationCount(coverageItemCount, "coverage item")} checked` : null,
      warningCount ? `${formatEvidenceInterpretationCount(warningCount, "warning")} raised` : null,
    ].filter((item): item is string => Boolean(item)),
    label: "Coverage",
    title: requiredBucketCount
      ? `${coveredRequiredBucketCount}/${requiredBucketCount} required buckets`
      : "No required bucket policy",
  };
}
