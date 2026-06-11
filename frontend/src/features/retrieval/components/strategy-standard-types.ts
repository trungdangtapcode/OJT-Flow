export type SearchPlanFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type SearchPlanFilterAction = {
  field: SearchPlanFilterField;
  value: string;
};
