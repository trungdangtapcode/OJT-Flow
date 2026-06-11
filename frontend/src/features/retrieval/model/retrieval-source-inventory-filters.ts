import type { RetrievalSource } from "../../../types";
import type {
  SourceInventoryFilterOptions,
  SourceInventoryFilters,
} from "./retrieval-source-inventory-types";
import { uniqueSourceInventoryValues } from "./retrieval-source-inventory-values";

export const emptySourceInventoryFilters: SourceInventoryFilters = {
  domain: null,
  search: "",
  standard: null,
  type: null,
};

export function hasSourceInventoryFilters(filters: SourceInventoryFilters): boolean {
  return Boolean(
    filters.search.trim() || filters.type || filters.domain || filters.standard,
  );
}

export function sourceInventoryFilterOptions(
  sources: RetrievalSource[],
): SourceInventoryFilterOptions {
  return {
    domains: uniqueSourceInventoryValues(sources.map((source) => source.clinical_domain)),
    standards: uniqueSourceInventoryValues(sources.map((source) => source.standard_system)),
    types: uniqueSourceInventoryValues(sources.map((source) => source.source_type)),
  };
}

export function filteredSourcesForInventory(
  sources: RetrievalSource[],
  filters: SourceInventoryFilters,
): RetrievalSource[] {
  return sources.filter((source) => sourceMatchesInventoryFilters(source, filters));
}

export function sourceMatchesInventoryFilters(
  source: RetrievalSource,
  filters: SourceInventoryFilters,
): boolean {
  if (filters.type && source.source_type !== filters.type) return false;
  if (filters.domain && source.clinical_domain !== filters.domain) return false;
  if (filters.standard && source.standard_system !== filters.standard) return false;

  const normalizedSearch = filters.search.trim().toLowerCase();
  if (!normalizedSearch) return true;
  return [
    source.source_id,
    source.title,
    source.source_type,
    source.clinical_domain,
    source.standard_system,
    source.source_version,
    source.trust_level,
  ].some((value) => value?.toLowerCase().includes(normalizedSearch));
}
