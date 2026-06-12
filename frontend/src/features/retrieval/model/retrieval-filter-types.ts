export type SupportedFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type FacetFilterField = Exclude<SupportedFilterField, "source_id">;

export type ActiveFacetFilters = Partial<Record<SupportedFilterField, string>>;

export type ActiveFilterEntry = {
  displayValue: string;
  field: SupportedFilterField;
  label: string;
};

export type CoverageFilterAction = {
  field: SupportedFilterField;
  value: string;
};

export type QueryProfileFilterEntry = {
  applied: boolean;
  displayValue: string;
  field: string;
  label: string;
  supported: boolean;
  value: string;
};

export type SuggestedFilterSource = {
  suggestedFilters: Record<string, string>;
};

export const supportedSuggestionFilterFields = new Set<SupportedFilterField>([
  "clinical_domain",
  "source_id",
  "standard_system",
  "source_type",
  "trust_level",
]);

export const facetFilterFields: FacetFilterField[] = [
  "clinical_domain",
  "standard_system",
  "source_type",
  "trust_level",
];
