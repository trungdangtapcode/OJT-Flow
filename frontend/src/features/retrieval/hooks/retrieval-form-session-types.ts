import type * as React from "react";
import type { RetrievalFormState } from "../model/retrieval-search-payload";

export type RetrievalFormValues = RetrievalFormState;

export type RetrievalFormSetters = {
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
