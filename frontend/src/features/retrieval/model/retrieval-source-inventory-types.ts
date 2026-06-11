export type SourceInventoryFilters = {
  domain: string | null;
  search: string;
  standard: string | null;
  type: string | null;
};

export type SourceInventoryReadiness = {
  chunkCount: number;
  domainCount: number;
  emptySourceCount: number;
  filteredCount: number;
  readiness: "ready" | "review" | "blocked";
  standardCount: number;
  sourceCount: number;
  sourceTypeCount: number;
};

export type SourceInventoryFilterOptions = {
  domains: string[];
  standards: string[];
  types: string[];
};
