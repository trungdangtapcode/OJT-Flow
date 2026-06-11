import type { RetrievalSearchTask } from "../../../types";
import {
  booleanValue,
  numberValue,
  optionalStringValue,
  recordValue,
  stringArrayValue,
  stringRecordValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";

export function retrievalTasksValue(value: unknown): RetrievalSearchTask[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => {
      const target = stringValue(item.target, "local_corpus");
      const metadata = recordValue(item.metadata);
      return {
        action_type: retrievalTaskActionTypeValue(item.action_type, target, metadata),
        aspect_id: optionalStringValue(item.aspect_id),
        label: stringValue(item.label, "Retrieval task"),
        metadata,
        priority: numberValue(item.priority) ?? 100,
        query: stringValue(item.query, ""),
        query_variants: stringArrayValue(item.query_variants),
        rationale: stringValue(item.rationale, "Generated from query analysis."),
        required: booleanValue(item.required),
        search_hint_target: optionalStringValue(item.search_hint_target),
        standards: stringArrayValue(item.standards),
        suggested_filters: stringRecordValue(item.suggested_filters),
        target: target === "external_medical_index" ? "external_medical_index" : "local_corpus",
        task_id: stringValue(item.task_id, ""),
        warnings: stringArrayValue(item.warnings),
      } satisfies RetrievalSearchTask;
    })
    .filter((item) => item.task_id && item.query)
    .sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
}

export function retrievalTaskActionTypeValue(
  value: unknown,
  target: string,
  metadata: Record<string, unknown>,
): RetrievalSearchTask["action_type"] {
  const action = stringValue(value, "");
  if (
    action === "run_local_search" ||
    action === "open_external_url" ||
    action === "copy_query"
  ) {
    return action;
  }
  if (target === "external_medical_index") {
    return optionalStringValue(metadata.url) ? "open_external_url" : "copy_query";
  }
  return "run_local_search";
}
