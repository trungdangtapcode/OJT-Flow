import type {
  RetrievalPackage,
  RetrievalPlan,
} from "../../../types";
import {
  queryAnalysisFromPackage,
  queryAnalysisFromPlan,
  queryVariantsFromAnalysis,
  queryVariantsFromTrace,
  searchPlanCoverageSummary,
  searchPlanRiskSignals,
  searchPlanTaskSummary,
} from "../model/retrieval-query-analysis";
import type { SearchPlanPreviewView } from "../model/search-plan-preview-types";

export function searchPlanPreviewView({
  currentPlanData,
  packageData,
}: {
  currentPlanData: RetrievalPlan | undefined;
  packageData: RetrievalPackage | undefined;
}): SearchPlanPreviewView | null {
  if (!packageData && !currentPlanData) return null;
  const analysis = packageData
    ? queryAnalysisFromPackage(packageData)
    : queryAnalysisFromPlan(currentPlanData!);
  return {
    analysis,
    coverageSummary: searchPlanCoverageSummary(analysis),
    planSummary: currentPlanData?.summary ?? null,
    profile: analysis.queryProfile,
    qualitySummary: packageData?.quality_summary ?? null,
    riskSignals: searchPlanRiskSignals(analysis),
    taskSummary: searchPlanTaskSummary(analysis),
    variants: packageData
      ? queryVariantsFromTrace(packageData.trace)
      : queryVariantsFromAnalysis(analysis),
  };
}
