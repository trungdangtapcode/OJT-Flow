import type {
  RetrievalRunComparison,
} from "./retrieval-run-comparison-types";
import type { RetrievalSearchRun } from "./retrieval-run-summary";

export type RetrievalRunComparisonRunValues = Pick<
  RetrievalRunComparison,
  | "activePayload"
  | "activeQuery"
  | "activeRunId"
  | "activeSubmittedAt"
  | "activeSummary"
  | "baselinePayload"
  | "baselineQuery"
  | "baselineRunId"
  | "baselineSubmittedAt"
  | "baselineSummary"
>;

export function retrievalRunComparisonRunValues({
  activeRun,
  baselineRun,
}: {
  activeRun: RetrievalSearchRun;
  baselineRun: RetrievalSearchRun;
}): RetrievalRunComparisonRunValues {
  return {
    activePayload: activeRun.payload,
    activeQuery: activeRun.payload.query,
    activeRunId: activeRun.runId,
    activeSubmittedAt: activeRun.submittedAt,
    activeSummary: activeRun.summary,
    baselinePayload: baselineRun.payload,
    baselineQuery: baselineRun.payload.query,
    baselineRunId: baselineRun.runId,
    baselineSubmittedAt: baselineRun.submittedAt,
    baselineSummary: baselineRun.summary,
  };
}
