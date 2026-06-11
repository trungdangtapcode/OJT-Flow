import type { QueryDiagnosticStack } from "./retrieval-query-analysis-types";
import {
  recordValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";

export function queryDiagnosticsValue(value: unknown): QueryDiagnosticStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      code: stringValue(item.code, "query_diagnostic"),
      metadata: recordValue(item.metadata),
      message: stringValue(item.message, "Query diagnostic unavailable."),
      severity: stringValue(item.severity, "info"),
      suggestedAction: stringValue(item.suggested_action, "Review the retrieval query."),
    }))
    .filter((item) => item.code !== "query_diagnostic");
}
