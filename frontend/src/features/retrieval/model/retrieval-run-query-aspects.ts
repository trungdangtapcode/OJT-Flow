import type { RetrievalPackage } from "../../../types";
import { queryAnalysisFromPackage } from "./retrieval-query-analysis";
import type { QueryAspectSummary } from "./retrieval-run-summary-types";

export function queryAspectSummariesFromPackage(
  packageData: RetrievalPackage,
): QueryAspectSummary[] {
  return queryAnalysisFromPackage(packageData)
    .queryAspects.map((aspect) => ({
      aspectId: aspect.aspectId,
      label: aspect.label,
      priority: aspect.priority,
      question: aspect.question,
      ruleId: aspect.ruleId,
    }))
    .sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
}
