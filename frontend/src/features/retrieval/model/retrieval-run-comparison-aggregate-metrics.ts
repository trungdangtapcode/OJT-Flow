import type {
  RetrievalRankChange,
  RetrievalRunComparisonMetrics,
} from "./retrieval-run-comparison-types";

export function comparisonMetrics({
  activeCount,
  addedCount,
  baselineCount,
  rankChanges,
  retainedCount,
  removedCount,
}: {
  activeCount: number;
  addedCount: number;
  baselineCount: number;
  rankChanges: RetrievalRankChange[];
  retainedCount: number;
  removedCount: number;
}): RetrievalRunComparisonMetrics {
  const unionCount = Math.max(0, activeCount + baselineCount - retainedCount);
  const totalRankDelta = rankChanges.reduce(
    (total, change) => total + Math.abs(change.rankDelta),
    0,
  );
  return {
    changedRankCount: rankChanges.length,
    churnRate: unionCount ? (addedCount + removedCount) / unionCount : 0,
    meanAbsoluteRankDelta: rankChanges.length
      ? totalRankDelta / rankChanges.length
      : 0,
    overlapRatio: unionCount ? retainedCount / unionCount : 1,
    sharedCount: retainedCount,
    unionCount,
  };
}
