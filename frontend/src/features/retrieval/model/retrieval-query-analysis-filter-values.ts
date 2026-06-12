import type { FilterSuggestionStack } from "../components/search-plan-detail-panels";
import {
  booleanValue,
  numberValue,
  recordValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";

export function filterSuggestionsValue(value: unknown): FilterSuggestionStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      applied: booleanValue(item.applied),
      confidence: numberValue(item.confidence) ?? 0,
      field: stringValue(item.field, "filter"),
      reason: stringValue(item.reason, "Suggested by query analysis."),
      value: stringValue(item.value, "unknown"),
    }))
    .filter((item) => item.field !== "filter" && item.value !== "unknown");
}
