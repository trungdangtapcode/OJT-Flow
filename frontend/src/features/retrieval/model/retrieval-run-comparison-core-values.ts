import type { RetrievalSearchRun } from "./retrieval-run-summary";

export type RetrievalRunComparisonCoreValues = {
  candidateDelta: number;
  hitDelta: number;
  qualityWarningDelta: number;
  rulePackChanged: boolean;
  topSourceAfter: string | null;
  topSourceBefore: string | null;
  topSourceChanged: boolean;
  warningDelta: number;
};

export function retrievalRunComparisonCoreValues({
  activeRun,
  baselineRun,
  rulePackChanged,
}: {
  activeRun: RetrievalSearchRun;
  baselineRun: RetrievalSearchRun;
  rulePackChanged: boolean;
}): RetrievalRunComparisonCoreValues {
  return {
    candidateDelta:
      activeRun.summary.candidateCount - baselineRun.summary.candidateCount,
    hitDelta: activeRun.summary.hitCount - baselineRun.summary.hitCount,
    qualityWarningDelta:
      activeRun.summary.qualityWarningCount - baselineRun.summary.qualityWarningCount,
    rulePackChanged,
    topSourceAfter: activeRun.summary.topSourceId,
    topSourceBefore: baselineRun.summary.topSourceId,
    topSourceChanged: activeRun.summary.topSourceId !== baselineRun.summary.topSourceId,
    warningDelta: activeRun.summary.warningCount - baselineRun.summary.warningCount,
  };
}
