import { humanize } from "../../../lib/utils";
import {
  filterFieldLabel,
  formatFilterValue,
  isSupportedFilterField,
} from "./retrieval-filter-format";
import type {
  QueryProfileFilterEntry,
  SupportedFilterField,
} from "./retrieval-filter-types";

export function suggestedFilterEntries(
  suggestedFilters: Record<string, string>,
  appliedFilters: Record<string, unknown>,
): QueryProfileFilterEntry[] {
  return Object.entries(suggestedFilters).map(([field, value]) => {
    const supported = isSupportedFilterField(field);
    return {
      applied: supported && appliedFilterMatches(appliedFilters, field, value),
      displayValue: supported ? formatFilterValue(field, value) : value,
      field,
      label: supported ? filterFieldLabel(field) : humanize(field),
      supported,
      value,
    };
  });
}

export function appliedFilterMatches(
  appliedFilters: Record<string, unknown>,
  field: SupportedFilterField,
  value: string,
): boolean {
  const appliedValue = appliedFilters[field];
  if (typeof appliedValue !== "string") return false;
  return appliedValue.toLowerCase() === value.toLowerCase();
}
