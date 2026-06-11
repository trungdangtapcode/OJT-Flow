import * as React from "react";

import type { RetrievalSearchPayload, RetrievalSearchPreset } from "../../../types";
import type { RetrievalFormSetters } from "./retrieval-form-session-types";

type UseRetrievalFormPayloadActionsArgs = {
  markCustomSearch: () => void;
  setActivePresetId: (presetId: string | null) => void;
  setFormError: (message: string | null) => void;
  setPlanControlNotice: (message: string | null) => void;
  setters: RetrievalFormSetters;
};

export function useRetrievalFormPayloadActions({
  markCustomSearch,
  setActivePresetId,
  setFormError,
  setPlanControlNotice,
  setters,
}: UseRetrievalFormPayloadActionsArgs) {
  const applyPreset = React.useCallback(
    (preset: RetrievalSearchPreset) => {
      applyPresetToForm(preset, setters);
      setFormError(null);
      setPlanControlNotice(null);
      setActivePresetId(preset.preset_id);
    },
    [setActivePresetId, setFormError, setPlanControlNotice, setters],
  );

  const restoreSearchPayload = React.useCallback(
    (payload: RetrievalSearchPayload) => {
      markCustomSearch();
      applySearchPayloadToForm(payload, setters);
      setFormError(null);
    },
    [markCustomSearch, setFormError, setters],
  );

  return {
    applyPreset,
    restoreSearchPayload,
  };
}

function applyPresetToForm(
  preset: RetrievalSearchPreset,
  setters: RetrievalFormSetters,
) {
  setters.setQuery(preset.query);
  setters.setFields(preset.fields.join(", "));
  setters.setSchemaId(preset.schema_id ?? "");
  setters.setDetectedFormat(preset.detected_format ?? "");
  setters.setResourceType(preset.resource_type ?? "");
  setters.setClinicalDomain(preset.clinical_domain ?? "");
  setters.setStandardSystem(preset.standard_system ?? "");
  setters.setSourceType(preset.source_type ?? "");
  setters.setTrustLevel(preset.trust_level ?? "");
  setters.setSourceId("");
  setters.setTopK(preset.top_k);
}

function applySearchPayloadToForm(
  payload: RetrievalSearchPayload,
  setters: RetrievalFormSetters,
) {
  setters.setQuery(payload.query);
  setters.setFields(payload.fields.join(", "));
  setters.setSchemaId(payload.schema_id ?? "");
  setters.setDetectedFormat(payload.detected_format ?? "");
  setters.setResourceType(payload.resource_type ?? "");
  setters.setClinicalDomain(payload.clinical_domain ?? "");
  setters.setStandardSystem(payload.standard_system ?? "");
  setters.setSourceType(payload.source_type ?? "");
  setters.setTrustLevel(payload.trust_level ?? "");
  setters.setSourceId(payload.filters?.source_id ?? "");
  setters.setTopK(payload.top_k);
}
