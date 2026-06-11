import type {
  RetrievalPackage,
  RetrievalSearchPayload,
} from "../../../types";
import { retrievalCockpitQueryAnalysisReport } from "./retrieval-report-cockpit-query-analysis";
import { retrievalCockpitRankingStackReport } from "./retrieval-report-cockpit-ranking";
import { retrievalCockpitReadinessReport } from "./retrieval-report-cockpit-readiness";
import { retrievalCockpitRetrievalReport } from "./retrieval-report-cockpit-retrieval";
import { retrievalCockpitRulePackReport } from "./retrieval-report-cockpit-rule-packs";
import { retrievalCockpitStrategyRecommendationReport } from "./retrieval-report-cockpit-strategy";
import { retrievalCockpitEvidenceHitReports } from "./retrieval-report-evidence-hits";
import { retrievalInterpretationReport } from "./retrieval-report-interpretation";
import { retrievalStandardSearchPlanReport } from "./retrieval-report-standard-plan";
import {
  retrievalRunSummary,
  serverSearchSignatureFromPackage,
} from "./retrieval-run-summary";
import { searchRunRemediationSummary } from "./search-run-presentation";

export function retrievalCockpitReportFromPackage(
  packageData: RetrievalPackage,
  submittedSearchPayload: RetrievalSearchPayload | null,
) {
  const runSummary = retrievalRunSummary(packageData);
  return {
    report_type: "retrieval_cockpit",
    version: 1,
    generated_at: new Date().toISOString(),
    query: submittedSearchPayload?.query ?? null,
    submitted_payload: submittedSearchPayload,
    search_signature: serverSearchSignatureFromPackage(packageData),
    retrieval: retrievalCockpitRetrievalReport(packageData),
    evidence_hits: retrievalCockpitEvidenceHitReports(packageData),
    query_analysis: retrievalCockpitQueryAnalysisReport(
      packageData,
      submittedSearchPayload,
    ),
    ranking_stack: retrievalCockpitRankingStackReport(packageData),
    strategy_recommendations:
      retrievalCockpitStrategyRecommendationReport(packageData),
    standard_search_plan: retrievalStandardSearchPlanReport(packageData),
    evidence_readiness: retrievalCockpitReadinessReport(
      packageData,
      submittedSearchPayload,
    ),
    recommended_action_summary: packageData.recommended_action_summary ?? null,
    remediation_summary:
      runSummary.remediationSummary ?? searchRunRemediationSummary(runSummary),
    interpretation: retrievalInterpretationReport(packageData),
    recommended_actions: packageData.recommended_actions ?? [],
    facets: packageData.facets ?? null,
    graph_context: packageData.handoff_context.graph_context ?? null,
    retrieval_rule_packs: retrievalCockpitRulePackReport(packageData),
  };
}
