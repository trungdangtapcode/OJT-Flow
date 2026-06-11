import * as React from "react";

import type { SupportedFilterField } from "../model/retrieval-filter-model";
import type { RetrievalSearchPayload } from "../../../types";
import type { RetrievalFormSetters } from "./retrieval-form-session-types";

export function useRetrievalFilterControls(setters: RetrievalFormSetters) {
  const applyFilterControl = React.useCallback(
    (
      field: SupportedFilterField,
      value: string,
    ): Partial<RetrievalSearchPayload> => {
      const overrides: Partial<RetrievalSearchPayload> = {};
      if (field === "clinical_domain") {
        setters.setClinicalDomain(value);
        overrides.clinical_domain = value;
      } else if (field === "standard_system") {
        setters.setStandardSystem(value);
        overrides.standard_system = value;
      } else if (field === "source_type") {
        setters.setSourceType(value);
        overrides.source_type = value;
      } else if (field === "trust_level") {
        setters.setTrustLevel(value);
        overrides.trust_level = value;
      } else if (field === "source_id") {
        setters.setSourceId(value);
        overrides.filters = { source_id: value };
      }
      return overrides;
    },
    [setters],
  );

  const clearFilterControl = React.useCallback(
    (field: SupportedFilterField): Partial<RetrievalSearchPayload> => {
      const overrides: Partial<RetrievalSearchPayload> = {};
      if (field === "clinical_domain") {
        setters.setClinicalDomain("");
        overrides.clinical_domain = null;
      } else if (field === "standard_system") {
        setters.setStandardSystem("");
        overrides.standard_system = null;
      } else if (field === "source_type") {
        setters.setSourceType("");
        overrides.source_type = null;
      } else if (field === "trust_level") {
        setters.setTrustLevel("");
        overrides.trust_level = null;
      } else if (field === "source_id") {
        setters.setSourceId("");
        overrides.filters = { source_id: null };
      }
      return overrides;
    },
    [setters],
  );

  const clearAllFilterControls = React.useCallback((): Partial<RetrievalSearchPayload> => {
    setters.setClinicalDomain("");
    setters.setStandardSystem("");
    setters.setSourceType("");
    setters.setSourceId("");
    setters.setTrustLevel("");
    return {
      clinical_domain: null,
      filters: { source_id: null },
      source_type: null,
      standard_system: null,
      trust_level: null,
    };
  }, [setters]);

  return {
    applyFilterControl,
    clearAllFilterControls,
    clearFilterControl,
  };
}
