import type * as React from "react";

import type { RetrievalFormState } from "../model/retrieval-search-payload";
import type {
  RetrievalFormSetters,
  RetrievalFormValues,
} from "./retrieval-form-session-types";

export type RetrievalFormStateInputs = RetrievalFormValues;

export type RetrievalFormSetterInputs = {
  setClinicalDomain: React.Dispatch<React.SetStateAction<string>>;
  setDetectedFormat: React.Dispatch<React.SetStateAction<string>>;
  setFields: React.Dispatch<React.SetStateAction<string>>;
  setQuery: React.Dispatch<React.SetStateAction<string>>;
  setResourceType: React.Dispatch<React.SetStateAction<string>>;
  setSchemaId: React.Dispatch<React.SetStateAction<string>>;
  setSourceId: React.Dispatch<React.SetStateAction<string>>;
  setSourceType: React.Dispatch<React.SetStateAction<string>>;
  setStandardSystem: React.Dispatch<React.SetStateAction<string>>;
  setTopK: React.Dispatch<React.SetStateAction<number>>;
  setTrustLevel: React.Dispatch<React.SetStateAction<string>>;
};

export function retrievalFormStateFromInputs(
  inputs: RetrievalFormStateInputs,
): RetrievalFormState {
  return inputs;
}

export function retrievalFormSettersFromInputs(
  inputs: RetrievalFormSetterInputs,
): RetrievalFormSetters {
  return inputs;
}
