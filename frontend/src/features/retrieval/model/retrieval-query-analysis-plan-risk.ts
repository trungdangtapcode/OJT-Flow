import type {
  RetrievalPlanRiskSignal,
} from "../../../types";
import type { QueryAnalysisStack } from "./retrieval-query-analysis-types";
import { searchPlanCoverageSummary } from "./retrieval-query-analysis-plan-summary";

export function searchPlanRiskSignals(
  analysis: QueryAnalysisStack,
): RetrievalPlanRiskSignal[] {
  if (analysis.planRiskSignals.length) return analysis.planRiskSignals;
  const coverage = searchPlanCoverageSummary(analysis);
  const signals: RetrievalPlanRiskSignal[] = [];
  if (!coverage.ready) {
    signals.push({
      code: "coverage_not_ready",
      message: "The plan needs more detail before review-grade search.",
      metadata: {
        local_task_count: coverage.localTaskCount,
        standard_count: coverage.standards.length,
      },
      severity: "warning",
      source: "frontend_compatibility_fallback",
      suggested_action:
        "Add a standard, field list, resource type, schema, or clinical domain before relying on the search.",
    });
  }
  signals.push(
    ...analysis.diagnostics
      .filter((diagnostic) => diagnostic.severity !== "info")
      .map((diagnostic) => ({
        code: `diagnostic_${diagnostic.code}`,
        message: diagnostic.message,
        metadata: diagnostic.metadata,
        severity: diagnostic.severity,
        source: "query_diagnostic",
        suggested_action: diagnostic.suggestedAction,
      })),
  );
  return signals.slice(0, 6);
}
