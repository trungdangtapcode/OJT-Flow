import type { DiversityStack } from "./retrieval-source-diversity-types";
import type { RetrievalSearchRun } from "./retrieval-run-summary";
import type { RetrievalSourceDiversityComparison } from "./retrieval-run-comparison-types";
import { uniqueComparisonValues } from "./retrieval-run-comparison-value-utils";

export function sourceDiversityComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalSourceDiversityComparison {
  const active = activeRun.summary.diversity;
  const baseline = baselineRun.summary.diversity;
  const activeSelectedSourceIds = diversitySelectedSourceIds(active);
  const baselineSelectedSourceIds = diversitySelectedSourceIds(baseline);
  const activeSourceSet = new Set(activeSelectedSourceIds);
  const baselineSourceSet = new Set(baselineSelectedSourceIds);
  const addedSourceIds = activeSelectedSourceIds.filter(
    (sourceId) => !baselineSourceSet.has(sourceId),
  );
  const removedSourceIds = baselineSelectedSourceIds.filter(
    (sourceId) => !activeSourceSet.has(sourceId),
  );
  const retainedSourceIds = activeSelectedSourceIds.filter((sourceId) =>
    baselineSourceSet.has(sourceId),
  );
  const unionCount = Math.max(
    0,
    activeSelectedSourceIds.length + baselineSelectedSourceIds.length - retainedSourceIds.length,
  );

  return {
    active,
    activeSelectedSourceIds,
    addedSourceIds,
    baseline,
    baselineSelectedSourceIds,
    candidateSourceDelta: active.candidateSourceCount - baseline.candidateSourceCount,
    duplicateSelectedSourceDelta:
      active.duplicateSelectedSourceCount - baseline.duplicateSelectedSourceCount,
    lambdaChanged: active.lambda !== baseline.lambda,
    removedSourceIds,
    retainedSourceIds,
    selectedSourceDelta: active.selectedSourceCount - baseline.selectedSourceCount,
    selectionModeChanged: active.selectionMode !== baseline.selectionMode,
    sourceOverlapRatio: unionCount ? retainedSourceIds.length / unionCount : 1,
  };
}

function diversitySelectedSourceIds(diversity: DiversityStack): string[] {
  return uniqueComparisonValues(diversity.selectedHits.map((selection) => selection.sourceId));
}
