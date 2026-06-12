import type { RetrievalSearchRun } from "./retrieval-run-summary";
import type { RetrievalRankChange } from "./retrieval-run-comparison-types";

export function rankChangesBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalRankChange[] {
  const baselineRanks = new Map(
    baselineRun.packageData.hits.map((hit, index) => [
      hit.evidence.evidence_id,
      index + 1,
    ]),
  );
  return activeRun.packageData.hits
    .map((hit, index) => {
      const evidenceId = hit.evidence.evidence_id;
      const fromRank = baselineRanks.get(evidenceId);
      const toRank = index + 1;
      if (!fromRank || fromRank === toRank) return null;
      return {
        evidenceId,
        fromRank,
        rankDelta: toRank - fromRank,
        toRank,
      };
    })
    .filter((change): change is RetrievalRankChange => Boolean(change))
    .sort((left, right) => Math.abs(right.rankDelta) - Math.abs(left.rankDelta));
}
