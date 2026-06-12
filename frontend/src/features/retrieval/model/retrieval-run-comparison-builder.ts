import {
  comparisonDiagnosisFromComparison,
} from "./retrieval-comparison-diagnosis";
import {
  comparisonMetrics,
} from "./retrieval-run-comparison-metrics";
import { retrievalRunComparisonDimensionValues } from "./retrieval-run-comparison-dimension-values";
import { retrievalRunComparisonCoreValues } from "./retrieval-run-comparison-core-values";
import { retrievalRunComparisonMetricInput } from "./retrieval-run-comparison-metric-input";
import { retrievalRunComparisonRunValues } from "./retrieval-run-comparison-run-values";
import type {
  RetrievalFacetConfig,
  RetrievalRunComparison,
} from "./retrieval-run-comparison-types";
import type { RetrievalSearchRun } from "./retrieval-run-summary";

export function compareSearchRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
  facetConfigs: RetrievalFacetConfig[],
): RetrievalRunComparison {
  const dimensions = retrievalRunComparisonDimensionValues({
    activeRun,
    baselineRun,
    facetConfigs,
  });
  const rulePackChanged = dimensions.rulePackChanges.some(
    (change) => change.status !== "stable",
  );
  const coreValues = retrievalRunComparisonCoreValues({
    activeRun,
    baselineRun,
    rulePackChanged,
  });
  const runValues = retrievalRunComparisonRunValues({ activeRun, baselineRun });

  const comparison: Omit<RetrievalRunComparison, "diagnosis"> = {
    addedEvidenceIds: dimensions.evidenceComparison.addedEvidenceIds,
    ...runValues,
    candidateDelta: coreValues.candidateDelta,
    conceptGroundingComparison: dimensions.conceptGroundingComparison,
    coverageComparison: dimensions.coverageComparison,
    facetComparisons: dimensions.facetComparisons,
    hitDelta: coreValues.hitDelta,
    metrics: comparisonMetrics(
      retrievalRunComparisonMetricInput({
        evidenceComparison: dimensions.evidenceComparison,
        rankChanges: dimensions.rankChanges,
      }),
    ),
    queryAspectComparison: dimensions.queryAspectComparison,
    qualityScoreDelta: dimensions.qualitySummaryComparison.qualityScoreDelta,
    qualitySummaryChanged: dimensions.qualitySummaryComparison.qualitySummaryChanged,
    qualityWarningDelta: coreValues.qualityWarningDelta,
    qualitySignalComparison: dimensions.qualitySignalComparison,
    queryProfileChanged: dimensions.queryProfileChanged,
    rankChanges: dimensions.rankChanges,
    removedEvidenceIds: dimensions.evidenceComparison.removedEvidenceIds,
    retainedEvidenceIds: dimensions.evidenceComparison.retainedEvidenceIds,
    rulePackChanges: dimensions.rulePackChanges,
    rulePackChanged: coreValues.rulePackChanged,
    sourceDiversityComparison: dimensions.sourceDiversityComparison,
    topSourceAfter: coreValues.topSourceAfter,
    topSourceBefore: coreValues.topSourceBefore,
    topSourceChanged: coreValues.topSourceChanged,
    warningDelta: coreValues.warningDelta,
  };
  return {
    ...comparison,
    diagnosis: comparisonDiagnosisFromComparison(comparison),
  };
}
