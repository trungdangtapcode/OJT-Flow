import type { RetrievalPackage } from "../../../types";
import { queryAnalysisFromPackage } from "./retrieval-query-analysis";
import type { QueryProfileSummary } from "./retrieval-run-summary-types";

export function queryProfileSummaryFromPackage(
  packageData: RetrievalPackage,
): QueryProfileSummary | null {
  const queryProfile = queryAnalysisFromPackage(packageData).queryProfile;
  if (!queryProfile) return null;
  return {
    complexity: queryProfile.complexity,
    label: queryProfile.label,
    profileId: queryProfile.profileId,
    retrievalMode: queryProfile.retrievalMode,
    route: queryProfile.route,
  };
}
