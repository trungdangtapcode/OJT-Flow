import type {
  RetrievalJudgmentEvaluationResult,
  RetrievalPackage,
  RetrievalRelevanceJudgmentSummary,
} from "../../../types";
import {
  queryProfileSummaryFromPackage,
  retrievalRulePacksFromPackage,
} from "./retrieval-run-summary";
import type { RelevanceJudgmentMetrics } from "./retrieval-judgment-types";

export function evaluationReportFromJudgmentSummary(
  evaluation: RetrievalJudgmentEvaluationResult,
  metrics: RelevanceJudgmentMetrics,
  summary: RetrievalRelevanceJudgmentSummary | null,
  packageData: RetrievalPackage,
) {
  return {
    report_type: "retrieval_judgment_evaluation",
    version: 1,
    generated_at: new Date().toISOString(),
    query: evaluation.query,
    cutoff: evaluation.cutoff,
    ranked_evidence_ids: evaluation.ranked_evidence_ids,
    evaluation_readiness: evaluation.evaluation_readiness,
    server_metrics: {
      coverage_at_k: evaluation.coverage_at_k,
      hit_rate_at_k: evaluation.hit_rate_at_k,
      precision_at_k: evaluation.precision_at_k,
      judged_precision: evaluation.judged_precision ?? null,
      average_precision_at_k: evaluation.average_precision_at_k,
      mrr_at_k: evaluation.mrr_at_k,
      ndcg_at_k: evaluation.ndcg_at_k ?? null,
      average_rating: evaluation.average_rating ?? null,
      judged_count: evaluation.judged_count,
      unjudged_count: evaluation.unjudged_count,
      relevant_count: evaluation.relevant_count,
      partial_count: evaluation.partial_count,
      not_relevant_count: evaluation.not_relevant_count,
    },
    local_metrics: {
      average_rating: metrics.averageRating,
      coverage_at_k: metrics.judgmentCoverage,
      precision_at_k: metrics.precisionAtK,
      judged_precision: metrics.judgedPrecision,
      ndcg_at_k: metrics.ndcgAtK,
      judged_count: metrics.judgedCount,
      relevant_count: metrics.relevantCount,
      partial_count: metrics.partialCount,
      not_relevant_count: metrics.notRelevantCount,
      total_hits: metrics.totalHits,
    },
    recommendations: evaluation.recommendations,
    query_profile: queryProfileSummaryFromPackage(packageData),
    retrieval_rule_packs: retrievalRulePacksFromPackage(packageData),
    stored_label_summary: summary,
    unjudged_evidence_ids: evaluation.unjudged_evidence_ids,
    judgment_ids: evaluation.judgment_ids,
  };
}
