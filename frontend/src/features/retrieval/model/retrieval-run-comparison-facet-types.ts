import type { RetrievalFacets } from "../../../types";

export type RetrievalFacetComparison = {
  activeCount: number;
  addedValues: string[];
  baselineCount: number;
  field: RetrievalFacetField;
  label: string;
  removedValues: string[];
  retainedValues: string[];
};

export type RetrievalFacetConfig = {
  field: RetrievalFacetField;
  label: string;
};

export type RetrievalFacetField = keyof RetrievalFacets;
