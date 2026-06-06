import type {
  RetrievalFacets,
  RetrievalSearchPayload,
  RuntimeRetrievalRulePack,
} from "../../../types";
import type {
  DiversityStack,
  RetrievalSourceDiversityComparisonView,
} from "../components/source-diversity-panel";
import {
  comparisonDiagnosisFromComparison,
  type RetrievalComparisonDiagnosis,
} from "./retrieval-comparison-diagnosis";
import {
  conceptGroundingKey,
  evidenceIdsFromRun,
  qualitySummaryFingerprint,
  retrievalRulePacksFromPackage,
  rulePackFingerprint,
  type ConceptGroundingSummary,
  type QueryAspectSummary,
  type QueryProfileSummary,
  type RetrievalCoverageSummary,
  type RetrievalSearchRun,
  type RetrievalRunSummary,
} from "./retrieval-run-summary";

export type RetrievalRulePackChange = {
  active?: RuntimeRetrievalRulePack;
  baseline?: RuntimeRetrievalRulePack;
  name: string;
  status: "added" | "removed" | "changed" | "stable";
};

export type RetrievalRunComparison = {
  addedEvidenceIds: string[];
  activePayload: RetrievalSearchPayload;
  activeQuery: string;
  activeRunId: string;
  activeSubmittedAt: string;
  activeSummary: RetrievalRunSummary;
  baselinePayload: RetrievalSearchPayload;
  baselineQuery: string;
  baselineRunId: string;
  baselineSubmittedAt: string;
  baselineSummary: RetrievalRunSummary;
  candidateDelta: number;
  conceptGroundingComparison: RetrievalConceptGroundingComparison;
  coverageComparison: RetrievalCoverageComparison;
  diagnosis: RetrievalComparisonDiagnosis[];
  facetComparisons: RetrievalFacetComparison[];
  hitDelta: number;
  metrics: RetrievalRunComparisonMetrics;
  queryAspectComparison: RetrievalQueryAspectComparison;
  qualityScoreDelta: number | null;
  qualitySummaryChanged: boolean;
  qualityWarningDelta: number;
  qualitySignalComparison: RetrievalQualitySignalComparison;
  queryProfileChanged: boolean;
  rankChanges: RetrievalRankChange[];
  removedEvidenceIds: string[];
  retainedEvidenceIds: string[];
  rulePackChanges: RetrievalRulePackChange[];
  rulePackChanged: boolean;
  sourceDiversityComparison: RetrievalSourceDiversityComparison;
  topSourceAfter: string | null;
  topSourceBefore: string | null;
  topSourceChanged: boolean;
  warningDelta: number;
};

export type RetrievalQueryAspectComparison = {
  added: QueryAspectSummary[];
  removed: QueryAspectSummary[];
  retained: QueryAspectSummary[];
};

export type RetrievalConceptGroundingComparison = {
  added: ConceptGroundingSummary[];
  removed: ConceptGroundingSummary[];
  retained: ConceptGroundingSummary[];
};

export type RetrievalCoverageComparison = {
  added: RetrievalCoverageSummary[];
  improved: RetrievalCoverageStatusChange[];
  regressed: RetrievalCoverageStatusChange[];
  removed: RetrievalCoverageSummary[];
  retained: RetrievalCoverageSummary[];
};

export type RetrievalCoverageStatusChange = {
  active: RetrievalCoverageSummary;
  baseline: RetrievalCoverageSummary;
};

export type RetrievalQualitySignalComparison = {
  added: RetrievalQualitySignalSummary[];
  removed: RetrievalQualitySignalSummary[];
  retained: RetrievalQualitySignalSummary[];
};

export type RetrievalQualitySignalSummary = {
  code: string;
  message: string;
  severity: string;
  suggestedAction: string;
};

export type RetrievalFacetComparison = {
  activeCount: number;
  addedValues: string[];
  baselineCount: number;
  field: RetrievalFacetField;
  label: string;
  removedValues: string[];
  retainedValues: string[];
};

export type RetrievalRunComparisonMetrics = {
  changedRankCount: number;
  churnRate: number;
  meanAbsoluteRankDelta: number;
  overlapRatio: number;
  sharedCount: number;
  unionCount: number;
};

export type RetrievalSourceDiversityComparison = RetrievalSourceDiversityComparisonView;

export type RetrievalRankChange = {
  evidenceId: string;
  fromRank: number;
  rankDelta: number;
  toRank: number;
};

export type RetrievalFacetConfig = {
  field: RetrievalFacetField;
  label: string;
};

type RetrievalFacetField = keyof RetrievalFacets;

export function compareSearchRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
  facetConfigs: RetrievalFacetConfig[],
): RetrievalRunComparison {
  const activeEvidenceIds = evidenceIdsFromRun(activeRun);
  const baselineEvidenceIds = evidenceIdsFromRun(baselineRun);
  const activeEvidenceIdSet = new Set(activeEvidenceIds);
  const baselineEvidenceIdSet = new Set(baselineEvidenceIds);
  const addedEvidenceIds = activeEvidenceIds.filter(
    (evidenceId) => !baselineEvidenceIdSet.has(evidenceId),
  );
  const removedEvidenceIds = baselineEvidenceIds.filter(
    (evidenceId) => !activeEvidenceIdSet.has(evidenceId),
  );
  const retainedEvidenceIds = activeEvidenceIds.filter((evidenceId) =>
    baselineEvidenceIdSet.has(evidenceId),
  );
  const rankChanges = rankChangesBetweenRuns(activeRun, baselineRun);
  const rulePackChanges = rulePackChangesBetweenRuns(activeRun, baselineRun);
  const queryProfileChanged = queryProfilesChanged(
    activeRun.summary.queryProfile,
    baselineRun.summary.queryProfile,
  );
  const coverageComparison = coverageComparisonBetweenRuns(activeRun, baselineRun);
  const facetComparisons = facetComparisonsBetweenRuns(
    activeRun,
    baselineRun,
    facetConfigs,
  );
  const qualitySignalComparison = qualitySignalComparisonBetweenRuns(
    activeRun,
    baselineRun,
  );
  const conceptGroundingComparison = conceptGroundingComparisonBetweenRuns(
    activeRun,
    baselineRun,
  );
  const queryAspectComparison = queryAspectComparisonBetweenRuns(activeRun, baselineRun);
  const sourceDiversityComparison = sourceDiversityComparisonBetweenRuns(
    activeRun,
    baselineRun,
  );
  const rulePackChanged = rulePackChanges.some((change) => change.status !== "stable");
  const topSourceChanged = activeRun.summary.topSourceId !== baselineRun.summary.topSourceId;
  const qualitySummaryChanged =
    qualitySummaryFingerprint(activeRun.summary.qualitySummary) !==
    qualitySummaryFingerprint(baselineRun.summary.qualitySummary);
  const qualityScoreDelta =
    activeRun.summary.qualitySummary && baselineRun.summary.qualitySummary
      ? activeRun.summary.qualitySummary.score - baselineRun.summary.qualitySummary.score
      : null;

  const comparison: Omit<RetrievalRunComparison, "diagnosis"> = {
    addedEvidenceIds,
    activePayload: activeRun.payload,
    activeQuery: activeRun.payload.query,
    activeRunId: activeRun.runId,
    activeSubmittedAt: activeRun.submittedAt,
    activeSummary: activeRun.summary,
    baselinePayload: baselineRun.payload,
    baselineQuery: baselineRun.payload.query,
    baselineRunId: baselineRun.runId,
    baselineSubmittedAt: baselineRun.submittedAt,
    baselineSummary: baselineRun.summary,
    candidateDelta:
      activeRun.summary.candidateCount - baselineRun.summary.candidateCount,
    conceptGroundingComparison,
    coverageComparison,
    facetComparisons,
    hitDelta: activeRun.summary.hitCount - baselineRun.summary.hitCount,
    metrics: comparisonMetrics({
      addedCount: addedEvidenceIds.length,
      baselineCount: baselineEvidenceIds.length,
      rankChanges,
      retainedCount: retainedEvidenceIds.length,
      removedCount: removedEvidenceIds.length,
      activeCount: activeEvidenceIds.length,
    }),
    queryAspectComparison,
    qualityScoreDelta,
    qualitySummaryChanged,
    qualityWarningDelta:
      activeRun.summary.qualityWarningCount - baselineRun.summary.qualityWarningCount,
    qualitySignalComparison,
    queryProfileChanged,
    rankChanges,
    removedEvidenceIds,
    retainedEvidenceIds,
    rulePackChanges,
    rulePackChanged,
    sourceDiversityComparison,
    topSourceAfter: activeRun.summary.topSourceId,
    topSourceBefore: baselineRun.summary.topSourceId,
    topSourceChanged,
    warningDelta: activeRun.summary.warningCount - baselineRun.summary.warningCount,
  };
  return {
    ...comparison,
    diagnosis: comparisonDiagnosisFromComparison(comparison),
  };
}

export function comparisonRulePackChangeViews(
  rulePackChanges: RetrievalRulePackChange[],
) {
  return rulePackChanges.map((change) => ({
    activeFingerprint: rulePackFingerprint(change.active),
    baselineFingerprint: rulePackFingerprint(change.baseline),
    name: change.name,
    status: change.status,
  }));
}

function comparisonMetrics({
  activeCount,
  addedCount,
  baselineCount,
  rankChanges,
  retainedCount,
  removedCount,
}: {
  activeCount: number;
  addedCount: number;
  baselineCount: number;
  rankChanges: RetrievalRankChange[];
  retainedCount: number;
  removedCount: number;
}): RetrievalRunComparisonMetrics {
  const unionCount = Math.max(0, activeCount + baselineCount - retainedCount);
  const totalRankDelta = rankChanges.reduce(
    (total, change) => total + Math.abs(change.rankDelta),
    0,
  );
  return {
    changedRankCount: rankChanges.length,
    churnRate: unionCount ? (addedCount + removedCount) / unionCount : 0,
    meanAbsoluteRankDelta: rankChanges.length
      ? totalRankDelta / rankChanges.length
      : 0,
    overlapRatio: unionCount ? retainedCount / unionCount : 1,
    sharedCount: retainedCount,
    unionCount,
  };
}

function sourceDiversityComparisonBetweenRuns(
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
  return uniqueValues(diversity.selectedHits.map((selection) => selection.sourceId));
}

function rankChangesBetweenRuns(
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

function rulePackChangesBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalRulePackChange[] {
  const activePacks = retrievalRulePacksFromPackage(activeRun.packageData);
  const baselinePacks = retrievalRulePacksFromPackage(baselineRun.packageData);
  const activeByName = new Map(activePacks.map((pack) => [pack.name, pack]));
  const baselineByName = new Map(baselinePacks.map((pack) => [pack.name, pack]));
  const packNames = uniqueValues([...activeByName.keys(), ...baselineByName.keys()]);
  return packNames.map((name) => {
    const active = activeByName.get(name);
    const baseline = baselineByName.get(name);
    let status: RetrievalRulePackChange["status"] = "stable";
    if (active && !baseline) status = "added";
    else if (!active && baseline) status = "removed";
    else if (rulePackFingerprint(active) !== rulePackFingerprint(baseline)) {
      status = "changed";
    }
    return { active, baseline, name, status };
  });
}

function queryProfilesChanged(
  active: QueryProfileSummary | null,
  baseline: QueryProfileSummary | null,
): boolean {
  return (
    active?.profileId !== baseline?.profileId ||
    active?.retrievalMode !== baseline?.retrievalMode ||
    active?.route !== baseline?.route
  );
}

function coverageComparisonBetweenRuns(
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

function facetComparisonsBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
  facetConfigs: RetrievalFacetConfig[],
): RetrievalFacetComparison[] {
  return facetConfigs.map((config) => {
    const activeValues = facetValuesFromRun(activeRun, config.field);
    const baselineValues = facetValuesFromRun(baselineRun, config.field);
    const activeSet = new Set(activeValues);
    const baselineSet = new Set(baselineValues);
    return {
      activeCount: activeValues.length,
      addedValues: activeValues.filter((value) => !baselineSet.has(value)),
      baselineCount: baselineValues.length,
      field: config.field,
      label: config.label,
      removedValues: baselineValues.filter((value) => !activeSet.has(value)),
      retainedValues: activeValues.filter((value) => baselineSet.has(value)),
    };
  });
}

function facetValuesFromRun(run: RetrievalSearchRun, field: RetrievalFacetField): string[] {
  const facets = run.packageData.facets;
  if (!facets) return [];
  const buckets = facetBuckets(facets, field);
  return buckets
    .map((bucket) => bucket.value)
    .filter(Boolean)
    .sort((left, right) => left.localeCompare(right));
}

function facetBuckets(facets: RetrievalFacets, field: RetrievalFacetField) {
  if (field === "clinical_domain") return facets.clinical_domain;
  if (field === "standard_system") return facets.standard_system;
  if (field === "source_type") return facets.source_type;
  if (field === "trust_level") return facets.trust_level;
  return [];
}

function qualitySignalComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalQualitySignalComparison {
  const activeSignals = qualitySignalSummariesFromRun(activeRun);
  const baselineSignals = qualitySignalSummariesFromRun(baselineRun);
  const activeByCode = new Map(activeSignals.map((signal) => [signal.code, signal]));
  const baselineByCode = new Map(baselineSignals.map((signal) => [signal.code, signal]));
  return {
    added: activeSignals.filter((signal) => !baselineByCode.has(signal.code)),
    removed: baselineSignals.filter((signal) => !activeByCode.has(signal.code)),
    retained: activeSignals.filter((signal) => baselineByCode.has(signal.code)),
  };
}

function queryAspectComparisonBetweenRuns(
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

function conceptGroundingComparisonBetweenRuns(
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

function qualitySignalSummariesFromRun(
  run: RetrievalSearchRun,
): RetrievalQualitySignalSummary[] {
  return (run.packageData.quality_signals ?? [])
    .map((signal) => ({
      code: signal.code,
      message: signal.message,
      severity: signal.severity,
      suggestedAction: signal.suggested_action,
    }))
    .filter((signal) => signal.code)
    .sort((left, right) => left.code.localeCompare(right.code));
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
}
