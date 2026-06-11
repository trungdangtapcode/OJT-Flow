import * as React from "react";

import type { RetrievalSearchPreset } from "../../../types";
import { useQueryBuilderDraftActions } from "./use-query-builder-draft-actions";
import { useRetrievalFilterControls } from "./use-retrieval-filter-controls";
import { useRetrievalFormPayloadActions } from "./use-retrieval-form-payload-actions";
import { useRetrievalFormState } from "./use-retrieval-form-state";

export function useRetrievalFormSession(presets: RetrievalSearchPreset[]) {
  const {
    activeFacetFilters,
    currentSearchSignature,
    formState,
    setters,
    values,
  } = useRetrievalFormState();
  const [formError, setFormError] = React.useState<string | null>(null);
  const [planControlNotice, setPlanControlNotice] = React.useState<string | null>(null);
  const [activePresetId, setActivePresetId] = React.useState<string | null>(null);
  const [didApplyInitialPreset, setDidApplyInitialPreset] = React.useState(false);

  const markCustomSearch = React.useCallback(() => {
    setActivePresetId(null);
    setPlanControlNotice(null);
  }, []);

  const {
    applyPreset,
    restoreSearchPayload,
  } = useRetrievalFormPayloadActions({
    markCustomSearch,
    setActivePresetId,
    setFormError,
    setPlanControlNotice,
    setters,
  });

  React.useEffect(() => {
    if (didApplyInitialPreset || !presets.length) return;
    applyPreset(presets[0]);
    setDidApplyInitialPreset(true);
  }, [applyPreset, didApplyInitialPreset, presets]);

  const {
    applyFilterControl,
    clearAllFilterControls,
    clearFilterControl,
  } = useRetrievalFilterControls(setters);

  const queryBuilderDraftActions = useQueryBuilderDraftActions({
    applyPreset,
    markCustomSearch,
    setFormError,
    setters,
  });

  return {
    activeFacetFilters,
    activePresetId,
    applyFilterControl,
    applyPreset,
    clearAllFilterControls,
    clearFilterControl,
    currentSearchSignature,
    formError,
    formState,
    markCustomSearch,
    planControlNotice,
    queryBuilderDraftActions,
    restoreSearchPayload,
    setClinicalDomain: setters.setClinicalDomain,
    setDetectedFormat: setters.setDetectedFormat,
    setFields: setters.setFields,
    setFormError,
    setPlanControlNotice,
    setQuery: setters.setQuery,
    setResourceType: setters.setResourceType,
    setSchemaId: setters.setSchemaId,
    setSourceId: setters.setSourceId,
    setSourceType: setters.setSourceType,
    setStandardSystem: setters.setStandardSystem,
    setTopK: setters.setTopK,
    setTrustLevel: setters.setTrustLevel,
    values,
  };
}
