import type {
  RetrievalPlanRiskSignal,
  RetrievalPlanTaskSummary,
} from "../../../types";
import {
  stringArrayValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";
import {
  conceptCandidatesValue,
  filterSuggestionsValue,
  queryAspectsValue,
  queryDiagnosticsValue,
  queryProfileValue,
  searchHintsValue,
} from "./retrieval-query-analysis-profile-values";
import { retrievalTasksValue } from "./retrieval-query-analysis-task-values";
import type {
  QueryAnalysisStack,
  SearchPlanCoverageStack,
} from "./retrieval-query-analysis-types";
import { queryVariantDetailsValue } from "./retrieval-query-analysis-variants";

export function queryAnalysisStackFromRecord(
  queryAnalysis: Record<string, unknown>,
  planCoverageSummary: SearchPlanCoverageStack | null = null,
  planTaskSummary: RetrievalPlanTaskSummary | null = null,
  planRiskSignals: RetrievalPlanRiskSignal[] = [],
): QueryAnalysisStack {
  const queryVariantTexts = stringArrayValue(queryAnalysis.query_variants);
  return {
    conceptCandidates: conceptCandidatesValue(queryAnalysis.concept_candidates),
    detectedConcepts: stringArrayValue(queryAnalysis.detected_concepts),
    diagnostics: queryDiagnosticsValue(queryAnalysis.diagnostics),
    expandedTerms: stringArrayValue(queryAnalysis.expanded_terms),
    filterSuggestions: filterSuggestionsValue(queryAnalysis.filter_suggestions),
    queryAspects: queryAspectsValue(queryAnalysis.query_aspects),
    queryProfile: queryProfileValue(queryAnalysis.query_profile),
    queryVariantTexts,
    queryVariants: queryVariantDetailsValue(queryAnalysis.query_variant_details),
    planCoverageSummary,
    planRiskSignals,
    planTaskSummary,
    retrievalTasks: retrievalTasksValue(queryAnalysis.retrieval_tasks),
    ruleIds: stringArrayValue(queryAnalysis.rule_ids),
    searchHints: searchHintsValue(queryAnalysis.search_hints),
    standards: stringArrayValue(queryAnalysis.standards),
    strategy: stringValue(queryAnalysis.strategy, "unknown"),
    variantCount: queryVariantTexts.length,
  };
}
