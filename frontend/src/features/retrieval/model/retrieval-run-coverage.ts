import { humanize } from "../../../lib/utils";
import type { RetrievalCoverage, RetrievalPackage } from "../../../types";
import type { RetrievalCoverageSummary } from "./retrieval-run-summary-types";
import { stringRecordValue } from "./retrieval-run-summary-values";

export function coverageSummariesFromPackage(
  packageData: RetrievalPackage,
): RetrievalCoverageSummary[] {
  const coverage = packageData.coverage;
  const standardItems = coverage?.standard_system ?? [];
  const aspectItems = coverage?.query_aspects ?? [];
  return [
    ...standardItems.map((item) => coverageSummaryFromItem(item, "standard")),
    ...aspectItems.map((item) => coverageSummaryFromItem(item, "aspect")),
  ].sort((left, right) => coverageComparisonKey(left).localeCompare(coverageComparisonKey(right)));
}

function coverageSummaryFromItem(
  item: RetrievalCoverage["standard_system"][number],
  group: "aspect" | "standard",
): RetrievalCoverageSummary {
  return {
    field: item.field,
    label: group === "standard" ? item.value : humanize(item.value),
    selectedCount: item.selected_count,
    status: item.status,
    suggestedFilter: stringRecordValue(item.suggested_filter),
    value: item.value,
  };
}

function coverageComparisonKey(item: RetrievalCoverageSummary): string {
  return `${item.field}:${item.value}`;
}
