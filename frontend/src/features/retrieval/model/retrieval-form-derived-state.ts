import { activeFacetFiltersFromPayload } from "./retrieval-filter-model";
import {
  retrievalPayloadFromForm,
  retrievalSearchSignature,
  type RetrievalFormState,
} from "./retrieval-search-payload";

export function retrievalFormDerivedState(formState: RetrievalFormState) {
  const searchPayload = retrievalPayloadFromForm(formState);
  return {
    activeFacetFilters: activeFacetFiltersFromPayload(searchPayload),
    currentSearchSignature: retrievalSearchSignature(searchPayload),
    searchPayload,
  };
}
