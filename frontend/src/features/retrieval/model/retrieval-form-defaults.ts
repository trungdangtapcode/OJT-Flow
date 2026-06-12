import type { RetrievalFormState } from "./retrieval-search-payload";

export const defaultRetrievalFormState: RetrievalFormState = {
  clinicalDomain: "",
  detectedFormat: "",
  fields: "",
  query: "",
  resourceType: "",
  schemaId: "",
  sourceId: "",
  sourceType: "",
  standardSystem: "",
  topK: 5,
  trustLevel: "approved",
};
