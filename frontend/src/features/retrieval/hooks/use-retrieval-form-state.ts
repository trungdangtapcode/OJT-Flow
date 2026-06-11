import * as React from "react";

import { retrievalFormDerivedState } from "../model/retrieval-form-derived-state";
import {
  retrievalFormSettersFromInputs,
  retrievalFormStateFromInputs,
} from "./retrieval-form-state-builders";
import { useRetrievalFormFieldState } from "./use-retrieval-form-field-state";

export function useRetrievalFormState() {
  const { setterInputs, values } = useRetrievalFormFieldState();

  const formState = React.useMemo(
    () => retrievalFormStateFromInputs(values),
    [values],
  );
  const {
    activeFacetFilters,
    currentSearchSignature,
    searchPayload,
  } = retrievalFormDerivedState(formState);

  const setters = React.useMemo(
    () => retrievalFormSettersFromInputs(setterInputs),
    [setterInputs],
  );

  return {
    activeFacetFilters,
    currentSearchSignature,
    formState,
    searchPayload,
    setters,
    values: formState,
  };
}
