import type {
  RetrievalPackage,
  RetrievalPlan,
  RetrievalSearchPayload,
} from "../../../types";
import {
  queryAnalysisFromPackage,
  queryAnalysisFromPlan,
  queryVariantsFromAnalysis,
  queryVariantsFromTrace,
  searchPlanCoverageSummary,
  searchPlanRiskSignals,
  searchPlanTaskSummary,
} from "./retrieval-query-analysis";
import { retrievalStandardSearchPlanReport } from "./retrieval-report-standard-plan";
import { serverSearchSignatureFromPackage } from "./retrieval-run-summary";

export function retrievalSearchPlanPreviewReport(
  packageData: RetrievalPackage | undefined,
  submittedSearchPayload: RetrievalSearchPayload | null,
  planData: RetrievalPlan | undefined,
) {
  const analysis = packageData
    ? queryAnalysisFromPackage(packageData)
    : queryAnalysisFromPlan(planData!);
  return {
    report_type: "retrieval_search_plan_preview",
    version: 1,
    generated_at: new Date().toISOString(),
    submitted_payload: submittedSearchPayload,
    plan_query: planData?.query ?? null,
    search_signature: packageData
      ? serverSearchSignatureFromPackage(packageData)
      : planData?.search_signature ?? null,
    route: {
      strategy: packageData?.trace.strategy ?? analysis.strategy,
      profile: analysis.queryProfile,
      quality_summary: packageData?.quality_summary ?? null,
    },
    query_planning: {
      detected_concepts: analysis.detectedConcepts,
      standards: analysis.standards,
      rule_ids: analysis.ruleIds,
      aspects: analysis.queryAspects,
      retrieval_tasks: analysis.retrievalTasks,
      coverage_summary: searchPlanCoverageSummary(analysis),
      task_summary: searchPlanTaskSummary(analysis),
      risk_signals: searchPlanRiskSignals(analysis),
      diagnostics: analysis.diagnostics,
      filter_suggestions: analysis.filterSuggestions,
      rewrites: packageData
        ? queryVariantsFromTrace(packageData.trace)
        : queryVariantsFromAnalysis(analysis),
    },
    medical_search_hints: analysis.searchHints,
    standard_search_plan: packageData
      ? retrievalStandardSearchPlanReport(packageData)
      : null,
    trace: {
      candidates_seen: packageData?.trace.candidates_seen ?? null,
      filters_applied:
        packageData?.trace.filters_applied ?? planData?.query.filters ?? {},
      warnings: packageData?.trace.warnings ?? [],
      safety_flags: packageData?.trace.safety_flags ?? [],
    },
  };
}
