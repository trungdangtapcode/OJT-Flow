import { evidenceIdsFromRun, type RetrievalSearchRun } from "./retrieval-run-summary";

export type RetrievalRunEvidenceComparison = {
  activeEvidenceIds: string[];
  addedEvidenceIds: string[];
  baselineEvidenceIds: string[];
  removedEvidenceIds: string[];
  retainedEvidenceIds: string[];
};

export function evidenceComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalRunEvidenceComparison {
  const activeEvidenceIds = evidenceIdsFromRun(activeRun);
  const baselineEvidenceIds = evidenceIdsFromRun(baselineRun);
  const activeEvidenceIdSet = new Set(activeEvidenceIds);
  const baselineEvidenceIdSet = new Set(baselineEvidenceIds);

  return {
    activeEvidenceIds,
    addedEvidenceIds: activeEvidenceIds.filter(
      (evidenceId) => !baselineEvidenceIdSet.has(evidenceId),
    ),
    baselineEvidenceIds,
    removedEvidenceIds: baselineEvidenceIds.filter(
      (evidenceId) => !activeEvidenceIdSet.has(evidenceId),
    ),
    retainedEvidenceIds: activeEvidenceIds.filter((evidenceId) =>
      baselineEvidenceIdSet.has(evidenceId),
    ),
  };
}
