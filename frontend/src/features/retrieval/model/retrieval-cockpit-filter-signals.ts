import { humanize } from "../../../lib/utils";
import type { RetrievalSearchPayload } from "../../../types";

export {
  firstSupportedRecommendedAction,
  recommendedActionFilter,
} from "./retrieval-cockpit-recommended-action-filter";

export type RetrievalCockpitFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type RetrievalCockpitFilterAction = {
  field: RetrievalCockpitFilterField;
  value: string;
};

export type RetrievalSearchCockpitActiveFilter = {
  displayValue: string;
  field: RetrievalCockpitFilterField;
  label: string;
};

export function activeFiltersFromPayload(
  payload: RetrievalSearchPayload | null,
): RetrievalSearchCockpitActiveFilter[] {
  if (!payload) return [];
  return activeFilterEntries(activeFacetFiltersFromPayload(payload));
}

function activeFacetFiltersFromPayload(
  payload: RetrievalSearchPayload,
): Partial<Record<RetrievalCockpitFilterField, string>> {
  return {
    clinical_domain: payload.filters?.clinical_domain ?? payload.clinical_domain ?? undefined,
    source_id: payload.filters?.source_id ?? undefined,
    source_type: payload.filters?.source_type ?? payload.source_type ?? undefined,
    standard_system: payload.filters?.standard_system ?? payload.standard_system ?? undefined,
    trust_level: payload.filters?.trust_level ?? payload.trust_level ?? undefined,
  };
}

function activeFilterEntries(
  filters: Partial<Record<RetrievalCockpitFilterField, string>>,
): RetrievalSearchCockpitActiveFilter[] {
  return Object.entries(filters)
    .filter((entry): entry is [RetrievalCockpitFilterField, string] => Boolean(entry[1]))
    .map(([field, value]) => ({
      displayValue: humanize(value),
      field,
      label: filterFieldLabel(field),
    }));
}

function filterFieldLabel(field: RetrievalCockpitFilterField): string {
  const labels: Record<RetrievalCockpitFilterField, string> = {
    clinical_domain: "Domain",
    source_id: "Source",
    source_type: "Source type",
    standard_system: "Standard",
    trust_level: "Trust",
  };
  return labels[field];
}
