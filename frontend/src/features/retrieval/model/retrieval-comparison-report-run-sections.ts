import { searchRunRemediationSummary } from "./search-run-presentation";
import type { RetrievalComparisonReportInput } from "./retrieval-comparison-types";

export function comparisonRunReportSections(
  comparison: RetrievalComparisonReportInput,
) {
  return {
    active: comparisonRunReportSection({
      payload: comparison.activePayload,
      query: comparison.activeQuery,
      runId: comparison.activeRunId,
      submittedAt: comparison.activeSubmittedAt,
      summary: comparison.activeSummary,
    }),
    baseline: comparisonRunReportSection({
      payload: comparison.baselinePayload,
      query: comparison.baselineQuery,
      runId: comparison.baselineRunId,
      submittedAt: comparison.baselineSubmittedAt,
      summary: comparison.baselineSummary,
    }),
  };
}

export function comparisonRemediationReport(
  comparison: RetrievalComparisonReportInput,
) {
  return {
    active:
      comparison.activeSummary.remediationSummary ??
      searchRunRemediationSummary(comparison.activeSummary),
    baseline:
      comparison.baselineSummary.remediationSummary ??
      searchRunRemediationSummary(comparison.baselineSummary),
  };
}

function comparisonRunReportSection({
  payload,
  query,
  runId,
  submittedAt,
  summary,
}: {
  payload: RetrievalComparisonReportInput["activePayload"];
  query: string;
  runId: string;
  submittedAt: string;
  summary: RetrievalComparisonReportInput["activeSummary"];
}) {
  return {
    query,
    run_id: runId,
    search_signature: summary.serverSignature,
    submitted_at: submittedAt,
    payload,
    remediation_summary:
      summary.remediationSummary ?? searchRunRemediationSummary(summary),
    summary,
  };
}
