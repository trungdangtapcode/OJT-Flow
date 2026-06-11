import * as React from "react";

import type { RetrievalSearchPreset } from "../../../types";
import type { RetrievalFormSetters } from "./retrieval-form-session-types";

export function useQueryBuilderDraftActions({
  applyPreset,
  markCustomSearch,
  setFormError,
  setters,
}: {
  applyPreset: (preset: RetrievalSearchPreset) => void;
  markCustomSearch: () => void;
  setFormError: React.Dispatch<React.SetStateAction<string | null>>;
  setters: RetrievalFormSetters;
}) {
  return React.useMemo(
    () => ({
      onApplyPreset: applyPreset,
      onClearFieldError: () => setFormError(null),
      onSelectSourceScope: (nextSourceId: string) => {
        markCustomSearch();
        setters.setSourceId(nextSourceId);
      },
      onSetClinicalDomain: (nextValue: string) => {
        markCustomSearch();
        setters.setClinicalDomain(nextValue);
      },
      onSetDetectedFormat: (nextValue: string) => {
        markCustomSearch();
        setters.setDetectedFormat(nextValue);
      },
      onSetFields: (nextValue: string) => {
        markCustomSearch();
        setters.setFields(nextValue);
      },
      onSetQuery: (nextValue: string) => {
        markCustomSearch();
        setters.setQuery(nextValue);
      },
      onSetResourceType: (nextValue: string) => {
        markCustomSearch();
        setters.setResourceType(nextValue);
      },
      onSetSchemaId: (nextValue: string) => {
        markCustomSearch();
        setters.setSchemaId(nextValue);
      },
      onSetSourceType: (nextValue: string) => {
        markCustomSearch();
        setters.setSourceType(nextValue);
      },
      onSetStandardSystem: (nextValue: string) => {
        markCustomSearch();
        setters.setStandardSystem(nextValue);
      },
      onSetTopK: (nextValue: number) => {
        markCustomSearch();
        setters.setTopK(nextValue);
      },
      onSetTrustLevel: (nextValue: string) => {
        markCustomSearch();
        setters.setTrustLevel(nextValue);
      },
    }),
    [applyPreset, markCustomSearch, setFormError, setters],
  );
}
