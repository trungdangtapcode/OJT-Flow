import type {
  RetrievalEvidenceBucket,
  RetrievalScoreComponent,
} from "../../../types";
import type { EvidenceHitMatchExplanation } from "./retrieval-evidence-types";
import { formatSignedDelta, uniqueValues } from "./retrieval-evidence-utils";

export function matchedBucketsForEvidence(
  buckets: RetrievalEvidenceBucket[],
  evidenceId: string,
): RetrievalEvidenceBucket[] {
  return buckets.filter((bucket) => bucket.evidence_ids.includes(evidenceId));
}

export function matchedBucketLabels(
  buckets: RetrievalEvidenceBucket[],
  evidenceId: string,
): string[] {
  return matchedBucketsForEvidence(buckets, evidenceId).map((bucket) => bucket.label);
}

export function topScoreComponentValue(
  scoreComponents: RetrievalScoreComponent[],
): EvidenceHitMatchExplanation["topScoreComponent"] {
  const topComponent = [...scoreComponents].sort(
    (left, right) => Math.abs(right.value) - Math.abs(left.value),
  )[0];
  return topComponent
    ? {
        component: topComponent.component,
        label: topComponent.label,
        rank: topComponent.rank ?? null,
        value: topComponent.value,
      }
    : null;
}

export function topScoreDriverValue(
  topScoreComponent: EvidenceHitMatchExplanation["topScoreComponent"],
): string | null {
  return topScoreComponent
    ? `${topScoreComponent.label} ${formatSignedDelta(topScoreComponent.value)}`
    : null;
}

export function matchedBucketIds(
  buckets: RetrievalEvidenceBucket[],
  evidenceId: string,
): string[] {
  return uniqueValues(
    matchedBucketsForEvidence(buckets, evidenceId).map((bucket) => bucket.bucket_id),
  ).slice(0, 8);
}
