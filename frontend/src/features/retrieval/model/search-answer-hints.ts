import type { RetrievalPackage } from "../../../types";

export function searchHintsFromPackage(packageData: RetrievalPackage): unknown[] {
  const queryAnalysis = packageData.handoff_context.query_analysis;
  if (!queryAnalysis || typeof queryAnalysis !== "object" || Array.isArray(queryAnalysis)) {
    return [];
  }
  const hints = (queryAnalysis as Record<string, unknown>).search_hints;
  return Array.isArray(hints) ? hints.slice(0, 8) : [];
}
