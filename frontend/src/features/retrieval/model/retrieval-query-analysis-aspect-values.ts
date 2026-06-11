import type { QueryAspectStack } from "../components/search-plan-detail-panels";
import {
  numberValue,
  recordValue,
  stringArrayValue,
  stringRecordValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";

export function queryAspectsValue(value: unknown): QueryAspectStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      aspectId: stringValue(item.aspect_id, ""),
      label: stringValue(item.label, "Search aspect"),
      priority: numberValue(item.priority) ?? 100,
      question: stringValue(item.question, "Review this search aspect."),
      rationale: stringValue(item.rationale, "Aspect generated from query analysis."),
      ruleId: stringValue(item.rule_id, ""),
      suggestedFilters: stringRecordValue(item.suggested_filters),
      suggestedTerms: stringArrayValue(item.suggested_terms),
    }))
    .filter((item) => item.aspectId)
    .sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
}
