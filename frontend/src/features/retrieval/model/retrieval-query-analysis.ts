import type {
  RetrievalPackage,
  RetrievalPlan,
} from "../../../types";
import {
  planCoverageSummaryValue,
  planRiskSignalsValue,
  planTaskSummaryValue,
  searchPlanCoverageSummary,
  searchPlanRiskSignals,
  searchPlanTaskSummary,
} from "./retrieval-query-analysis-plan";
import type {
  QueryAnalysisStack,
} from "./retrieval-query-analysis-types";
import { recordValue } from "./retrieval-query-analysis-coercion";
import { queryAnalysisStackFromRecord } from "./retrieval-query-analysis-stack";
import {
  queryVariantsFromAnalysis,
  queryVariantsFromTrace,
} from "./retrieval-query-analysis-variants";

export function queryAnalysisFromPackage(packageData: RetrievalPackage): QueryAnalysisStack {
  const queryAnalysis = recordValue(packageData.handoff_context.query_analysis);
  return queryAnalysisStackFromRecord(queryAnalysis);
}

export function queryAnalysisFromPlan(planData: RetrievalPlan): QueryAnalysisStack {
  return queryAnalysisStackFromRecord(
    recordValue(planData.query_analysis),
    planCoverageSummaryValue(planData.coverage_summary),
    planTaskSummaryValue(planData.task_summary),
    planRiskSignalsValue(planData.risk_signals),
  );
}

export {
  queryAnalysisStackFromRecord,
  queryVariantsFromAnalysis,
  queryVariantsFromTrace,
  searchPlanCoverageSummary,
  searchPlanRiskSignals,
  searchPlanTaskSummary,
};
export type {
  ConceptCandidateStack,
  QueryAnalysisStack,
  QueryDiagnosticStack,
  QueryProfileStack,
  SearchPlanCoverageStack,
} from "./retrieval-query-analysis-types";
