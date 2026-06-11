export type RecommendedActionFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type RecommendedActionFilter = {
  field: RecommendedActionFilterField;
  value: string;
};

export type RecommendedActionActiveFilter = {
  field: RecommendedActionFilterField;
};
