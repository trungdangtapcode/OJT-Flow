import type { SearchHintStack } from "../components/search-plan-detail-panels";
import {
  optionalStringValue,
  recordValue,
  stringArrayValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";

export function searchHintsValue(value: unknown): SearchHintStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      metadata: recordValue(item.metadata),
      query: stringValue(item.query, ""),
      rationale: stringValue(item.rationale, "Generated from rule-based query analysis."),
      target: stringValue(item.target, "medical_search"),
      url: optionalStringValue(item.url),
      warnings: stringArrayValue(item.warnings),
    }))
    .filter((item) => item.query.length > 0 && item.target !== "medical_search");
}
