import type {
  RetrievalCoverage,
  RetrievalEvidenceBucket,
} from "../../../types";
import {
  isSupportedFilterField,
} from "./retrieval-filter-format";
import {
  type CoverageFilterAction,
  type QueryProfileFilterEntry,
  type SuggestedFilterSource,
} from "./retrieval-filter-types";
import {
  suggestedFilterEntries as filterEntrySuggestions,
} from "./retrieval-filter-entry-suggestions";
import {
  recordValue,
  stringValue,
} from "./retrieval-runtime-values";

export function suggestedFilterAction(value: unknown): CoverageFilterAction | null {
  const suggestedFilter = recordValue(value);
  for (const [field, rawValue] of Object.entries(suggestedFilter)) {
    const filterValue = stringValue(rawValue, "");
    if (filterValue && isSupportedFilterField(field)) {
      return { field, value: filterValue };
    }
  }
  return null;
}

export function bucketSuggestedFilter(
  bucket: RetrievalEvidenceBucket,
): CoverageFilterAction | null {
  return suggestedFilterAction(bucket.suggested_filter);
}

export function coverageSuggestedFilter(
  item: RetrievalCoverage["standard_system"][number],
): CoverageFilterAction | null {
  return suggestedFilterAction(item.suggested_filter);
}

export function coverageSuggestedAction(
  item: RetrievalCoverage["standard_system"][number],
): string {
  return stringValue(item.suggested_action, item.reason);
}

export function queryProfileFilterEntries(
  profile: SuggestedFilterSource,
  appliedFilters: Record<string, unknown>,
): QueryProfileFilterEntry[] {
  return suggestedFilterEntries(profile.suggestedFilters, appliedFilters);
}

export function queryAspectFilterEntries(
  aspect: SuggestedFilterSource,
  appliedFilters: Record<string, unknown>,
): QueryProfileFilterEntry[] {
  return suggestedFilterEntries(aspect.suggestedFilters, appliedFilters);
}

export function suggestedFilterEntries(
  suggestedFilters: Record<string, string>,
  appliedFilters: Record<string, unknown>,
): QueryProfileFilterEntry[] {
  return filterEntrySuggestions(suggestedFilters, appliedFilters);
}
