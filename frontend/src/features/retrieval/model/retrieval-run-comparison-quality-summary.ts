import {
  qualitySummaryFingerprint,
  type RetrievalSearchRun,
} from "./retrieval-run-summary";

export type RetrievalRunQualitySummaryComparison = {
  qualityScoreDelta: number | null;
  qualitySummaryChanged: boolean;
};

export function qualitySummaryComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalRunQualitySummaryComparison {
  return {
    qualityScoreDelta:
      activeRun.summary.qualitySummary && baselineRun.summary.qualitySummary
        ? activeRun.summary.qualitySummary.score -
          baselineRun.summary.qualitySummary.score
        : null,
    qualitySummaryChanged:
      qualitySummaryFingerprint(activeRun.summary.qualitySummary) !==
      qualitySummaryFingerprint(baselineRun.summary.qualitySummary),
  };
}
