import type {
  RetrievalPackage,
  RetrievalSearchPayload,
} from "../../../types";
import {
  conceptGroundingCountFromPackage,
  coverageGapCountFromPackage,
  diversityFromPackage,
  fusionDiagnosticsFromPackage,
  hybridStackValue,
  queryAnalysisFromPackage,
  rankingStackFromPackage,
} from "./retrieval-cockpit-runtime";
import { qualitySummaryView } from "./retrieval-cockpit-quality-summary";
import {
  activeFiltersFromPayload,
  queryHealthItems,
  recommendedActionFilter,
  searchReadinessChecklist,
} from "./retrieval-cockpit-signals";
import {
  cockpitRouteLabel,
  requiredEvidenceBucketSummary,
} from "./retrieval-cockpit-view-derivations";
import type { RetrievalSearchCockpitView } from "./retrieval-cockpit-view-types";

export type {
  RetrievalSearchCockpitActiveFilter,
  RetrievalSearchCockpitView,
} from "./retrieval-cockpit-view-types";

export function retrievalSearchCockpitView(
  packageData: RetrievalPackage,
  submittedSearchPayload: RetrievalSearchPayload | null,
): RetrievalSearchCockpitView {
  const analysis = queryAnalysisFromPackage(packageData);
  const ranking = rankingStackFromPackage(packageData);
  const diversity = diversityFromPackage(packageData);
  const qualitySummary = packageData.quality_summary ?? null;
  const topAction = (packageData.recommended_actions ?? [])[0] ?? null;
  const {
    coveredRequiredBucketCount,
    requiredBucketCount,
    requiredBuckets,
  } = requiredEvidenceBucketSummary(packageData.evidence_buckets);
  const queryHealth = queryHealthItems(submittedSearchPayload, packageData);
  const queryProfile = analysis.queryProfile;
  const strategy = packageData.trace.strategy;
  const routeLabel = cockpitRouteLabel({ queryProfile, strategy });

  return {
    activeFilters: activeFiltersFromPayload(submittedSearchPayload),
    bm25Enabled: ranking.framework.bm25Enabled,
    candidateCount: packageData.trace.candidates_seen,
    conceptGroundingCount: conceptGroundingCountFromPackage(packageData),
    correctiveActionCount: packageData.recommended_action_summary?.count ?? null,
    coveredRequiredBucketCount,
    coverageGapCount: coverageGapCountFromPackage(packageData),
    detectedConcepts: analysis.detectedConcepts,
    diversity,
    expandedTerms: analysis.expandedTerms,
    fusionDiagnostics: fusionDiagnosticsFromPackage(packageData),
    hitCount: packageData.hits.length,
    hybridStackValue: hybridStackValue(ranking),
    qualitySummary: qualitySummary ? qualitySummaryView(qualitySummary) : null,
    queryAspectCount: analysis.queryAspects.length,
    queryAspects: analysis.queryAspects,
    queryHealth,
    queryProfile,
    rankingSupporting: `${ranking.embedding.provider} / ${ranking.embedding.model}`,
    readinessChecklist: searchReadinessChecklist({
      diversity,
      packageData,
      queryHealth,
      requiredBuckets,
      topAction,
    }),
    rerankerEnabled: ranking.reranker.enabled,
    requiredBucketCount,
    routeLabel,
    standardSearchPlan: packageData.standard_search_plan ?? null,
    standards: analysis.standards,
    strategy,
    strategyRecommendations: packageData.strategy_recommendations ?? [],
    topAction,
    topBroadeningAction: topAction?.action_type === "broaden_query",
    topFilterAction: topAction ? recommendedActionFilter(topAction) : null,
    variantCount: analysis.variantCount,
  };
}
