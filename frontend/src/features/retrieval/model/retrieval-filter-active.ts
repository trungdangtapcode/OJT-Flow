import type { RetrievalSearchPayload } from "../../../types";
import {
  filterFieldLabel,
  formatFilterValue,
} from "./retrieval-filter-format";
import {
  supportedSuggestionFilterFields,
  type ActiveFacetFilters,
  type ActiveFilterEntry,
} from "./retrieval-filter-types";

export function activeFacetFiltersFromPayload(
  payload: RetrievalSearchPayload,
): ActiveFacetFilters {
  return {
    clinical_domain: payload.clinical_domain || undefined,
    standard_system: payload.standard_system || undefined,
    source_type: payload.source_type || undefined,
    trust_level: payload.trust_level || undefined,
    source_id: payload.filters?.source_id || undefined,
  };
}

export function activeFilterEntries(filters: ActiveFacetFilters): ActiveFilterEntry[] {
  return Array.from(supportedSuggestionFilterFields)
    .map((field) => {
      const value = filters[field];
      if (!value) return null;
      return {
        displayValue: formatFilterValue(field, value),
        field,
        label: filterFieldLabel(field),
      };
    })
    .filter((entry): entry is ActiveFilterEntry => entry !== null);
}

export function activeFilterEntriesForSearch(
  currentFilters: ActiveFacetFilters,
  submittedPayload: RetrievalSearchPayload | null,
): ActiveFilterEntry[] {
  return activeFilterEntries(
    submittedPayload
      ? activeFacetFiltersFromPayload(submittedPayload)
      : currentFilters,
  );
}
