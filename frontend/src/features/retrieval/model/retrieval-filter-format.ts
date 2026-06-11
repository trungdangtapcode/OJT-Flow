import { humanize } from "../../../lib/utils";
import {
  supportedSuggestionFilterFields,
  type SupportedFilterField,
} from "./retrieval-filter-types";

export function filterFieldLabel(field: SupportedFilterField): string {
  if (field === "clinical_domain") return "Domain";
  if (field === "source_id") return "Source ID";
  if (field === "standard_system") return "Standard";
  if (field === "source_type") return "Source";
  return "Trust";
}

export function formatFilterValue(field: SupportedFilterField, value: string): string {
  return field === "standard_system" || field === "source_id" ? value : humanize(value);
}

export function formatMaybeSupportedFilterValue(field: string, value: string): string {
  return isSupportedFilterField(field) ? formatFilterValue(field, value) : value;
}

export function isSupportedFilterField(value: string): value is SupportedFilterField {
  return supportedSuggestionFilterFields.has(value as SupportedFilterField);
}
