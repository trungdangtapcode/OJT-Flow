import { humanize } from "../../../lib/utils";
import type {
  RetrievalPackage,
  RetrievalQualitySummary,
  RetrievalRecommendedAction,
  RetrievalSearchPayload,
  RetrievalStandardSearchPlan,
  RetrievalStrategyRecommendation,
} from "../../../types";
import {
  conceptGroundingCountFromPackage,
  coverageGapCountFromPackage,
  diversityFromPackage,
  fusionDiagnosticsFromPackage,
  hybridStackValue,
  queryAnalysisFromPackage,
  rankingStackFromPackage,
  type RetrievalCockpitDiversityStack,
  type RetrievalCockpitQueryAnalysisStack,
} from "./retrieval-cockpit-runtime";
import {
  activeFiltersFromPayload,
  queryHealthItems,
  recommendedActionFilter,
  searchReadinessChecklist,
  type RetrievalCockpitFilterAction,
  type RetrievalCockpitQueryHealthItem,
  type RetrievalCockpitReadinessChecklistItem,
  type RetrievalSearchCockpitActiveFilter,
} from "./retrieval-cockpit-signals";

export type { RetrievalSearchCockpitActiveFilter };

export type RetrievalSearchCockpitView = {
  activeFilters: RetrievalSearchCockpitActiveFilter[];
  bm25Enabled: boolean | null;
  candidateCount: number;
  conceptGroundingCount: number;
  correctiveActionCount: number | null;
  coveredRequiredBucketCount: number;
  coverageGapCount: number;
  detectedConcepts: string[];
  diversity: RetrievalCockpitDiversityStack;
  expandedTerms: string[];
  fusionDiagnostics: {
    interpretation: string;
    label: string;
    tone: "success" | "warning" | "info";
  };
  hitCount: number;
  hybridStackValue: string;
  qualitySummary: {
    score: number;
    status: string;
    topAction: string;
    variant: "success" | "warning" | "destructive" | "muted";
  } | null;
  queryAspectCount: number;
  queryAspects: RetrievalCockpitQueryAnalysisStack["queryAspects"];
  queryHealth: RetrievalCockpitQueryHealthItem[];
  queryProfile: RetrievalCockpitQueryAnalysisStack["queryProfile"];
  rankingSupporting: string;
  readinessChecklist: RetrievalCockpitReadinessChecklistItem[];
  rerankerEnabled: boolean;
  requiredBucketCount: number;
  routeLabel: string;
  standardSearchPlan: RetrievalStandardSearchPlan | null;
  standards: string[];
  strategy: string;
  strategyRecommendations: RetrievalStrategyRecommendation[];
  topAction: RetrievalRecommendedAction | null;
  topBroadeningAction: boolean;
  topFilterAction: RetrievalCockpitFilterAction | null;
  variantCount: number;
};

export function retrievalSearchCockpitView(
  packageData: RetrievalPackage,
  submittedSearchPayload: RetrievalSearchPayload | null,
): RetrievalSearchCockpitView {
  const analysis = queryAnalysisFromPackage(packageData);
  const ranking = rankingStackFromPackage(packageData);
  const diversity = diversityFromPackage(packageData);
  const qualitySummary = packageData.quality_summary ?? null;
  const topAction = (packageData.recommended_actions ?? [])[0] ?? null;
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const queryHealth = queryHealthItems(submittedSearchPayload, packageData);
  const queryProfile = analysis.queryProfile;
  const strategy = packageData.trace.strategy;
  const routeLabel = queryProfile
    ? `${queryProfile.label} / ${humanize(queryProfile.retrievalMode)}`
    : humanize(strategy);

  return {
    activeFilters: activeFiltersFromPayload(submittedSearchPayload),
    bm25Enabled: ranking.framework.bm25Enabled,
    candidateCount: packageData.trace.candidates_seen,
    conceptGroundingCount: conceptGroundingCountFromPackage(packageData),
    correctiveActionCount: packageData.recommended_action_summary?.count ?? null,
    coveredRequiredBucketCount: requiredBuckets.filter((bucket) => bucket.hit_count > 0).length,
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
    requiredBucketCount: requiredBuckets.length,
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

function qualitySummaryView(summary: RetrievalQualitySummary): NonNullable<
  RetrievalSearchCockpitView["qualitySummary"]
> {
  return {
    score: summary.score,
    status: summary.status,
    topAction: summary.top_action,
    variant: qualitySummaryBadgeVariant(summary),
  };
}

function qualitySummaryBadgeVariant(
  summary: RetrievalQualitySummary,
): "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
}
