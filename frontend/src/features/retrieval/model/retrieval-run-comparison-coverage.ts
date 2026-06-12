import type {
  RetrievalCoverageSummary,
  RetrievalSearchRun,
} from "./retrieval-run-summary";
import type {
  RetrievalCoverageComparison,
  RetrievalCoverageStatusChange,
} from "./retrieval-run-comparison-types";

export function coverageComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalCoverageComparison {
  const activeCoverage = activeRun.summary.coverage;
  const baselineCoverage = baselineRun.summary.coverage;
  const activeByKey = new Map(activeCoverage.map((item) => [coverageComparisonKey(item), item]));
  const baselineByKey = new Map(
    baselineCoverage.map((item) => [coverageComparisonKey(item), item]),
  );
  const retained: RetrievalCoverageSummary[] = [];
  const improved: RetrievalCoverageStatusChange[] = [];
  const regressed: RetrievalCoverageStatusChange[] = [];
  for (const item of activeCoverage) {
    const baseline = baselineByKey.get(coverageComparisonKey(item));
    if (!baseline) continue;
    const change = { active: item, baseline };
    const activeRank = coverageStatusRank(item);
    const baselineRank = coverageStatusRank(baseline);
    if (activeRank > baselineRank) improved.push(change);
    else if (activeRank < baselineRank) regressed.push(change);
    else retained.push(item);
  }
  return {
    added: activeCoverage.filter((item) => !baselineByKey.has(coverageComparisonKey(item))),
    improved,
    regressed,
    removed: baselineCoverage.filter((item) => !activeByKey.has(coverageComparisonKey(item))),
    retained,
  };
}

function coverageStatusRank(item: RetrievalCoverageSummary): number {
  if (item.status === "covered") return 2;
  if (item.status === "partial") return 1;
  return 0;
}

function coverageComparisonKey(item: RetrievalCoverageSummary): string {
  return `${item.field}:${item.value}`;
}
