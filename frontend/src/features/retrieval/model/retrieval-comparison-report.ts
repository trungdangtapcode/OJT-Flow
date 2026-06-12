import {
  comparisonOperatorSummary,
  comparisonRecommendedActionSummary,
  comparisonReportRecommendedActions,
} from "./retrieval-comparison-actions";
import {
  comparisonDeltaReport,
  comparisonDimensionReports,
  comparisonEvidenceReport,
  comparisonJudgmentReport,
  comparisonRemediationReport,
  comparisonRulePackReport,
  comparisonRunReportSections,
  comparisonSourceDiversityReport,
} from "./retrieval-comparison-report-sections";
import { comparisonReportSummary } from "./retrieval-comparison-report-summary";
import type {
  RetrievalComparisonJudgmentInput,
  RetrievalComparisonRecommendedAction,
  RetrievalComparisonReportInput,
} from "./retrieval-comparison-types";

export function comparisonReportFromComparison(
  comparison: RetrievalComparisonReportInput,
  judgments: RetrievalComparisonJudgmentInput[],
  recommendedActions: RetrievalComparisonRecommendedAction[] = comparisonReportRecommendedActions(
    comparison,
    judgments,
  ),
) {
  const runReports = comparisonRunReportSections(comparison);
  const dimensionReports = comparisonDimensionReports(comparison);
  return {
    report_type: "retrieval_run_comparison",
    version: 1,
    generated_at: new Date().toISOString(),
    summary: comparisonReportSummary(comparison, judgments),
    operator_summary: comparisonOperatorSummary(comparison, recommendedActions),
    remediation: comparisonRemediationReport(comparison),
    recommended_action_summary: comparisonRecommendedActionSummary(recommendedActions),
    recommended_actions: recommendedActions,
    active: runReports.active,
    baseline: runReports.baseline,
    deltas: comparisonDeltaReport(comparison),
    diagnosis: comparison.diagnosis,
    metrics: comparison.metrics,
    coverage: dimensionReports.coverage,
    query_aspects: dimensionReports.query_aspects,
    concept_grounding: dimensionReports.concept_grounding,
    quality_signals: dimensionReports.quality_signals,
    facets: dimensionReports.facets,
    judgments: comparisonJudgmentReport(judgments),
    evidence: comparisonEvidenceReport(comparison),
    top_source: {
      before: comparison.topSourceBefore,
      after: comparison.topSourceAfter,
      changed: comparison.topSourceChanged,
    },
    source_diversity: comparisonSourceDiversityReport(comparison),
    query_profiles: {
      before: comparison.baselineSummary.queryProfile,
      after: comparison.activeSummary.queryProfile,
      changed: comparison.queryProfileChanged,
    },
    rule_packs: comparisonRulePackReport(comparison),
  };
}
