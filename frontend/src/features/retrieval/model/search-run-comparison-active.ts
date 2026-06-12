import {
  facetFilterFields,
  filterFieldLabel,
} from "./retrieval-filter-model";
import {
  compareSearchRuns,
} from "./retrieval-run-comparison";
import type { RetrievalRunComparison } from "./retrieval-run-comparison-types";
import type { RetrievalSearchRun } from "./retrieval-run-summary";
import { comparisonRunForActive } from "./search-run-presentation";

export function activeSearchRunComparison({
  activeRunId,
  comparisonBaselineRunId,
  runs,
}: {
  activeRunId: string | null;
  comparisonBaselineRunId: string | null;
  runs: RetrievalSearchRun[];
}): RetrievalRunComparison | null {
  if (!activeRunId) return null;
  const activeRun = runs.find((run) => run.runId === activeRunId);
  if (!activeRun) return null;
  const baselineRun = comparisonRunForActive(
    runs,
    activeRun.runId,
    comparisonBaselineRunId,
  );
  return baselineRun
    ? compareSearchRuns(
        activeRun,
        baselineRun,
        facetFilterFields.map((field) => ({
          field,
          label: filterFieldLabel(field),
        })),
      )
    : null;
}
