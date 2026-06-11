import type { RetrievalSearchRun } from "./retrieval-run-summary";
import type {
  RetrievalQualitySignalComparison,
  RetrievalQualitySignalSummary,
} from "./retrieval-run-comparison-types";

export function qualitySignalComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalQualitySignalComparison {
  const activeSignals = qualitySignalSummariesFromRun(activeRun);
  const baselineSignals = qualitySignalSummariesFromRun(baselineRun);
  const activeByCode = new Map(activeSignals.map((signal) => [signal.code, signal]));
  const baselineByCode = new Map(baselineSignals.map((signal) => [signal.code, signal]));
  return {
    added: activeSignals.filter((signal) => !baselineByCode.has(signal.code)),
    removed: baselineSignals.filter((signal) => !activeByCode.has(signal.code)),
    retained: activeSignals.filter((signal) => baselineByCode.has(signal.code)),
  };
}

export function qualitySignalSummariesFromRun(
  run: RetrievalSearchRun,
): RetrievalQualitySignalSummary[] {
  return (run.packageData.quality_signals ?? [])
    .map((signal) => ({
      code: signal.code,
      message: signal.message,
      severity: signal.severity,
      suggestedAction: signal.suggested_action,
    }))
    .filter((signal) => signal.code)
    .sort((left, right) => left.code.localeCompare(right.code));
}
