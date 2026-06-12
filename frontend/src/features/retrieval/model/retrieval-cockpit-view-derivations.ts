import { humanize } from "../../../lib/utils";
import type { RetrievalEvidenceBucket } from "../../../types";
import type { RetrievalCockpitQueryAnalysisStack } from "./retrieval-cockpit-runtime";

export function requiredEvidenceBucketSummary(
  buckets: RetrievalEvidenceBucket[] | undefined,
) {
  const requiredBuckets = buckets?.filter((bucket) => bucket.required) ?? [];
  return {
    coveredRequiredBucketCount: requiredBuckets.filter(
      (bucket) => bucket.hit_count > 0,
    ).length,
    requiredBucketCount: requiredBuckets.length,
    requiredBuckets,
  };
}

export function cockpitRouteLabel({
  queryProfile,
  strategy,
}: {
  queryProfile: RetrievalCockpitQueryAnalysisStack["queryProfile"];
  strategy: string;
}) {
  if (!queryProfile) return humanize(strategy);
  return `${queryProfile.label} / ${humanize(queryProfile.retrievalMode)}`;
}
