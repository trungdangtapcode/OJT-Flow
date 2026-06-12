import type { RetrievalFacetBucket } from "../../../types";

export type ResultFacetFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level";

export type ResultFacetFilters = Partial<Record<ResultFacetFilterField | "source_id", string>>;

export type ResultFacetSection = {
  field: ResultFacetFilterField;
  label: string;
  values: RetrievalFacetBucket[];
  formatter: (value: string) => string;
};
