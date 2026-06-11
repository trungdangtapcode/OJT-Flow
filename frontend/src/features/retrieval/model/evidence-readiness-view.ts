import type { RetrievalPackage } from "../../../types";
import { readinessInterpretation } from "./evidence-readiness-interpretation";
import type { EvidenceReadinessView } from "./evidence-readiness-types";

export function evidenceReadinessView(
  packageData: RetrievalPackage,
): EvidenceReadinessView {
  const qualitySummary = packageData.quality_summary ?? null;
  const requiredBuckets = (packageData.evidence_buckets ?? []).filter(
    (bucket) => bucket.required,
  );
  const missingBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const bucketSignalAction =
    (packageData.quality_signals ?? []).find(
      (signal) => signal.code === "missing_required_evidence_buckets",
    )?.suggested_action ?? null;
  return {
    bucketSignalAction,
    interpretation: readinessInterpretation(qualitySummary, missingBuckets.length),
    missingBuckets,
    qualitySummary,
    ready: missingBuckets.length === 0 && qualitySummary?.status !== "blocked",
  };
}
