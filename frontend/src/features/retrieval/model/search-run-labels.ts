import { humanize } from "../../../lib/utils";
import type {
  RetrievalRecommendedAction,
  RetrievalSearchPayload,
} from "../../../types";
import { formatCount } from "./retrieval-format";

export function searchRunScopeLabels(payload: RetrievalSearchPayload): string[] {
  return [
    payload.schema_id ? `schema ${payload.schema_id}` : null,
    payload.detected_format ? `format ${humanize(payload.detected_format)}` : null,
    payload.resource_type ? `resource ${payload.resource_type}` : null,
    payload.clinical_domain ? `domain ${humanize(payload.clinical_domain)}` : null,
    payload.standard_system ? `standard ${payload.standard_system}` : null,
    payload.source_type ? `source ${humanize(payload.source_type)}` : null,
    payload.filters?.source_id ? `source ID ${payload.filters.source_id}` : null,
    payload.trust_level ? `trust ${humanize(payload.trust_level)}` : null,
    payload.fields.length ? formatCount(payload.fields.length, "field") : null,
  ].filter((label): label is string => Boolean(label));
}

export function recommendedActionSourceLabel(
  action: RetrievalRecommendedAction,
): string | null {
  const source = stringValue(action.metadata.corrective_rule_source, "");
  if (!source) return null;
  if (source === "query_diagnostic") return "query diagnostic";
  if (source === "quality_signal") return "quality signal";
  return humanize(source);
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}
