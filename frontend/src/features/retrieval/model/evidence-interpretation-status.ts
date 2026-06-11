import type { RetrievalPackage } from "../../../types";
import {
  formatEvidenceInterpretationCount,
  packageWarnings,
} from "./evidence-interpretation-values";
import type { EvidenceSupportStatus } from "./evidence-interpretation-types";

export function evidenceSupportBadgeVariant(
  status: EvidenceSupportStatus,
): "success" | "warning" | "destructive" {
  if (status === "strong") return "success";
  if (status === "partial") return "warning";
  return "destructive";
}

export function fallbackEvidenceStatus(
  packageData: RetrievalPackage,
  missingRequiredBuckets: RetrievalPackage["evidence_buckets"],
): string {
  if (!packageData.hits.length) return "no ranked evidence";
  if (missingRequiredBuckets?.length) return "support gaps";
  if (packageWarnings(packageData).length) return "review warnings";
  return "ready to review";
}

export function fallbackEvidenceSummary(
  packageData: RetrievalPackage,
  missingRequiredBuckets: RetrievalPackage["evidence_buckets"],
): string {
  const topHit = packageData.hits[0] ?? null;
  if (!topHit) {
    return "No ranked evidence was returned. Treat this as a search coverage problem until filters, source inventory, and backend warnings have been reviewed.";
  }
  if (missingRequiredBuckets?.length) {
    return `The top result is ${topHit.evidence.source_id}, but required support is missing for ${missingRequiredBuckets.map((bucket) => bucket.label).join(", ")}.`;
  }
  if (packageWarnings(packageData).length) {
    return `The package returned ${formatEvidenceInterpretationCount(packageData.hits.length, "ranked hit")}; warnings indicate the search may need review before the result order is trusted.`;
  }
  return `The top result is ${topHit.evidence.source_id}. Review its source provenance, score drivers, and support status before using it.`;
}
