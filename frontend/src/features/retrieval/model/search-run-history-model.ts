import type {
  RetrievalPackage,
  RetrievalSearchPayload,
} from "../../../types";
import type { RetrievalRunSummary, RetrievalSearchRun } from "./retrieval-run-summary";

export function createSearchRun({
  createRunId,
  now,
  packageData,
  payload,
  signature,
  summary,
}: {
  createRunId: () => string;
  now: () => string;
  packageData: RetrievalPackage;
  payload: RetrievalSearchPayload;
  signature: string;
  summary: RetrievalRunSummary;
}): RetrievalSearchRun {
  return {
    packageData,
    payload,
    runId: createRunId(),
    signature,
    submittedAt: now(),
    summary,
  };
}

export function comparisonRunForActive<T extends { runId: string }>(
  runs: T[],
  activeRunId: string,
  baselineRunId: string | null,
): T | null {
  const activeIndex = runs.findIndex((run) => run.runId === activeRunId);
  if (activeIndex < 0) return null;
  const explicitBaseline = baselineRunId
    ? runs.find((run) => run.runId === baselineRunId && run.runId !== activeRunId)
    : null;
  if (explicitBaseline) return explicitBaseline;
  return (
    runs.slice(activeIndex + 1).find((run) => run.runId !== activeRunId) ??
    runs.find((run) => run.runId !== activeRunId) ??
    null
  );
}
