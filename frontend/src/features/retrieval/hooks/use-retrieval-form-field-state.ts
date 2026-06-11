import * as React from "react";

import { defaultRetrievalFormState } from "../model/retrieval-form-defaults";

export function useRetrievalFormFieldState() {
  const [query, setQuery] = React.useState(defaultRetrievalFormState.query);
  const [fields, setFields] = React.useState(defaultRetrievalFormState.fields);
  const [schemaId, setSchemaId] = React.useState(defaultRetrievalFormState.schemaId);
  const [detectedFormat, setDetectedFormat] = React.useState(
    defaultRetrievalFormState.detectedFormat,
  );
  const [resourceType, setResourceType] = React.useState(
    defaultRetrievalFormState.resourceType,
  );
  const [clinicalDomain, setClinicalDomain] = React.useState(
    defaultRetrievalFormState.clinicalDomain,
  );
  const [standardSystem, setStandardSystem] = React.useState(
    defaultRetrievalFormState.standardSystem,
  );
  const [trustLevel, setTrustLevel] = React.useState(
    defaultRetrievalFormState.trustLevel,
  );
  const [sourceType, setSourceType] = React.useState(defaultRetrievalFormState.sourceType);
  const [sourceId, setSourceId] = React.useState(defaultRetrievalFormState.sourceId);
  const [topK, setTopK] = React.useState(defaultRetrievalFormState.topK);

  const setterInputs = React.useMemo(
    () => ({
      setClinicalDomain,
      setDetectedFormat,
      setFields,
      setQuery,
      setResourceType,
      setSchemaId,
      setSourceId,
      setSourceType,
      setStandardSystem,
      setTopK,
      setTrustLevel,
    }),
    [],
  );
  const values = React.useMemo(
    () => ({
      clinicalDomain,
      detectedFormat,
      fields,
      query,
      resourceType,
      schemaId,
      sourceId,
      sourceType,
      standardSystem,
      topK,
      trustLevel,
    }),
    [
      clinicalDomain,
      detectedFormat,
      fields,
      query,
      resourceType,
      schemaId,
      sourceId,
      sourceType,
      standardSystem,
      topK,
      trustLevel,
    ],
  );

  return { setterInputs, values };
}
