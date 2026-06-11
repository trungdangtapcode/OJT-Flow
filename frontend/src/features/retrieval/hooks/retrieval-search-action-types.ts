import type { RetrievalSearchPayload } from "../../../types";
import type { SupportedFilterField } from "../model/retrieval-filter-model";

export type SearchFilterSuggestion = {
  field: string;
  value: string;
};

export type RetrievalSearchTaskControlSetters = {
  setClinicalDomain: (value: string) => void;
  setQuery: (value: string) => void;
  setSourceId: (value: string) => void;
  setSourceType: (value: string) => void;
  setStandardSystem: (value: string) => void;
  setTrustLevel: (value: string) => void;
};

export type UseRetrievalSearchActionsArgs = RetrievalSearchTaskControlSetters & {
  applyFilterControl: (
    field: SupportedFilterField,
    value: string,
  ) => Partial<RetrievalSearchPayload>;
  clearAllFilterControls: () => Partial<RetrievalSearchPayload>;
  clearFilterControl: (field: SupportedFilterField) => Partial<RetrievalSearchPayload>;
  executeSearch: (overrides?: Partial<RetrievalSearchPayload>) => Promise<void>;
  hasCurrentPackage: boolean;
  hasPlanPreviewPackage: boolean;
  isSupportedFilterField: (field: string) => field is SupportedFilterField;
  markCustomSearch: () => void;
  setPlanControlNotice: (value: string | null) => void;
};
