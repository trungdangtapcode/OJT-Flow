import type { RetrievalPackage } from "../../../types";
import type { RetrievalSearchRun } from "../model/retrieval-run-summary";

export const defaultSearchRunHistoryLimit = 6;

export function upsertSearchRunHistory(
  current: RetrievalSearchRun[],
  run: RetrievalSearchRun,
  historyLimit: number,
): RetrievalSearchRun[] {
  return [run, ...current.filter((item) => item.signature !== run.signature)].slice(
    0,
    historyLimit,
  );
}

export function shouldClearComparisonBaseline(
  comparisonBaselineRunId: string | null,
  searchRuns: RetrievalSearchRun[],
): boolean {
  if (!comparisonBaselineRunId) return false;
  return !searchRuns.some((run) => run.runId === comparisonBaselineRunId);
}

export function activeRetrievalRunState({
  activeRunId,
  latestPackageData,
  searchRuns,
}: {
  activeRunId: string | null;
  latestPackageData?: RetrievalPackage;
  searchRuns: RetrievalSearchRun[];
}): {
  activeRun: RetrievalSearchRun | null;
  packageData: RetrievalPackage | undefined;
} {
  const activeRun = searchRuns.find((run) => run.runId === activeRunId) ?? null;
  return {
    activeRun,
    packageData: activeRun?.packageData ?? latestPackageData,
  };
}
