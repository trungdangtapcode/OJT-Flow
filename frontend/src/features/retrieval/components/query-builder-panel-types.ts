import type { FormEvent } from "react";

import type { RetrievalSearchPreset, RetrievalSource, SchemaEntry } from "../../../types";
import type { ActiveFacetFilters, SupportedFilterField } from "../model/retrieval-filter-model";

export type RetrievalQueryBuilderValue = {
  activeFilters: ActiveFacetFilters;
  activePresetId: string | null;
  clinicalDomain: string;
  detectedFormat: string;
  fields: string;
  formError: string | null;
  isSearchPending: boolean;
  isSearchResultStale: boolean;
  planControlNotice: string | null;
  query: string;
  resourceType: string;
  schemaId: string;
  sourceId: string;
  sourceType: string;
  standardSystem: string;
  topK: number;
  trustLevel: string;
};

export type RetrievalQueryBuilderOptions = {
  domainOptions: string[];
  formatOptions: Array<{ value: string; label: string }>;
  presets: RetrievalSearchPreset[];
  schemas: SchemaEntry[];
  selectedSource: RetrievalSource | null;
  sources: RetrievalSource[];
  sourceTypeOptions: string[];
  standardOptions: string[];
  topKOptions: number[];
  trustOptions: string[];
};

export type RetrievalQueryBuilderStatus = {
  presetsError: string | null;
  presetsLoading: boolean;
  searchError: string | null;
  searchOptionsError: string | null;
};

export type RetrievalQueryBuilderActions = {
  onApplyPreset: (preset: RetrievalSearchPreset) => void;
  onClearAllFilters: () => void;
  onClearFieldError: () => void;
  onClearSourceScope: () => void;
  onRemoveFilter: (field: SupportedFilterField) => void;
  onSearch: (event: FormEvent<HTMLFormElement>) => void;
  onSelectSourceScope: (sourceId: string) => void;
  onSetClinicalDomain: (value: string) => void;
  onSetDetectedFormat: (value: string) => void;
  onSetFields: (value: string) => void;
  onSetQuery: (value: string) => void;
  onSetResourceType: (value: string) => void;
  onSetSchemaId: (value: string) => void;
  onSetSourceType: (value: string) => void;
  onSetStandardSystem: (value: string) => void;
  onSetTopK: (value: number) => void;
  onSetTrustLevel: (value: string) => void;
};
