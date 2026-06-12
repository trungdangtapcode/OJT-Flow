import type { RetrievalCoverageSummaryView } from "./run-comparison-detail-types";

export function coverageComparisonKey(item: RetrievalCoverageSummaryView) {
  return `${item.field}:${item.value}:${item.status}`;
}
