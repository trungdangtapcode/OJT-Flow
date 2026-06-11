import {
  conceptGroundingKey,
  type RetrievalSearchRun,
} from "./retrieval-run-summary";
import type {
  RetrievalConceptGroundingComparison,
  RetrievalQueryAspectComparison,
} from "./retrieval-run-comparison-types";

export function queryAspectComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalQueryAspectComparison {
  const activeAspects = activeRun.summary.queryAspects;
  const baselineAspects = baselineRun.summary.queryAspects;
  const activeById = new Map(activeAspects.map((aspect) => [aspect.aspectId, aspect]));
  const baselineById = new Map(baselineAspects.map((aspect) => [aspect.aspectId, aspect]));
  return {
    added: activeAspects.filter((aspect) => !baselineById.has(aspect.aspectId)),
    removed: baselineAspects.filter((aspect) => !activeById.has(aspect.aspectId)),
    retained: activeAspects.filter((aspect) => baselineById.has(aspect.aspectId)),
  };
}

export function conceptGroundingComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalConceptGroundingComparison {
  const activeConcepts = activeRun.summary.conceptGrounding;
  const baselineConcepts = baselineRun.summary.conceptGrounding;
  const activeByKey = new Map(
    activeConcepts.map((concept) => [conceptGroundingKey(concept), concept]),
  );
  const baselineByKey = new Map(
    baselineConcepts.map((concept) => [conceptGroundingKey(concept), concept]),
  );
  return {
    added: activeConcepts.filter(
      (concept) => !baselineByKey.has(conceptGroundingKey(concept)),
    ),
    removed: baselineConcepts.filter(
      (concept) => !activeByKey.has(conceptGroundingKey(concept)),
    ),
    retained: activeConcepts.filter((concept) =>
      baselineByKey.has(conceptGroundingKey(concept)),
    ),
  };
}
