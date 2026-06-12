import * as React from "react";

import type { RetrievalSource } from "../../../types";
import {
  emptySourceInventoryFilters,
  filteredSourcesForInventory,
  hasSourceInventoryFilters,
  sourceInventoryFilterOptions,
  sourceInventoryReadiness,
} from "../model/retrieval-source-inventory-model";

export function useSourceInventoryPanelState(sources: RetrievalSource[]) {
  const [filters, setFilters] = React.useState(emptySourceInventoryFilters);
  const filteredSources = filteredSourcesForInventory(sources, filters);
  const filterOptions = sourceInventoryFilterOptions(sources);
  const hasSourceFilters = hasSourceInventoryFilters(filters);
  const readiness = sourceInventoryReadiness(sources, filteredSources);

  return {
    filteredSources,
    filterOptions,
    filters,
    hasSourceFilters,
    readiness,
    resetFilters: () => setFilters(emptySourceInventoryFilters),
    setFilters,
  };
}
