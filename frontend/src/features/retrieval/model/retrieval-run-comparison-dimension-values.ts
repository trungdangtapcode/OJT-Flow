import {
  conceptGroundingComparisonBetweenRuns,
  coverageComparisonBetweenRuns,
  facetComparisonsBetweenRuns,
  qualitySignalComparisonBetweenRuns,
  queryAspectComparisonBetweenRuns,
  queryProfilesChanged,
} from "./retrieval-run-comparison-dimensions";
import { evidenceComparisonBetweenRuns } from "./retrieval-run-comparison-evidence";
import {
  rankChangesBetweenRuns,
  rulePackChangesBetweenRuns,
  sourceDiversityComparisonBetweenRuns,
} from "./retrieval-run-comparison-metrics";
import { qualitySummaryComparisonBetweenRuns } from "./retrieval-run-comparison-quality-summary";
import type {
  RetrievalFacetConfig,
} from "./retrieval-run-comparison-types";
import type { RetrievalSearchRun } from "./retrieval-run-summary";

export function retrievalRunComparisonDimensionValues({
  activeRun,
  baselineRun,
  facetConfigs,
}: {
  activeRun: RetrievalSearchRun;
  baselineRun: RetrievalSearchRun;
  facetConfigs: RetrievalFacetConfig[];
}) {
  return {
    conceptGroundingComparison: conceptGroundingComparisonBetweenRuns(
      activeRun,
      baselineRun,
    ),
    coverageComparison: coverageComparisonBetweenRuns(activeRun, baselineRun),
    evidenceComparison: evidenceComparisonBetweenRuns(activeRun, baselineRun),
    facetComparisons: facetComparisonsBetweenRuns(activeRun, baselineRun, facetConfigs),
    qualitySignalComparison: qualitySignalComparisonBetweenRuns(activeRun, baselineRun),
    qualitySummaryComparison: qualitySummaryComparisonBetweenRuns(activeRun, baselineRun),
    queryAspectComparison: queryAspectComparisonBetweenRuns(activeRun, baselineRun),
    queryProfileChanged: queryProfilesChanged(
      activeRun.summary.queryProfile,
      baselineRun.summary.queryProfile,
    ),
    rankChanges: rankChangesBetweenRuns(activeRun, baselineRun),
    rulePackChanges: rulePackChangesBetweenRuns(activeRun, baselineRun),
    sourceDiversityComparison: sourceDiversityComparisonBetweenRuns(
      activeRun,
      baselineRun,
    ),
  };
}
