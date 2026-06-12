export type NoResultFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type NoResultActiveFilter = {
  displayValue: string;
  field: NoResultFilterField;
  label: string;
};

export type NoResultSuggestedAction = {
  field: NoResultFilterField;
  value: string;
};
