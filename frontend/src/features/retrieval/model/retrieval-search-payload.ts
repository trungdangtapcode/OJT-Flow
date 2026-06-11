import type { RetrievalSearchPayload } from "../../../types";

export type RetrievalFormState = {
  query: string;
  fields: string;
  schemaId: string;
  detectedFormat: string;
  resourceType: string;
  clinicalDomain: string;
  standardSystem: string;
  trustLevel: string;
  sourceType: string;
  sourceId: string;
  topK: number;
};

export function parseFields(value: string) {
  return value
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function retrievalPayloadFromForm(
  form: RetrievalFormState,
  overrides: Partial<RetrievalSearchPayload> = {},
): RetrievalSearchPayload {
  return {
    query: form.query.trim(),
    top_k: form.topK,
    schema_id: form.schemaId || null,
    fields: parseFields(form.fields),
    detected_format: form.detectedFormat || null,
    resource_type: form.resourceType || null,
    clinical_domain: form.clinicalDomain || null,
    standard_system: form.standardSystem || null,
    trust_level: form.trustLevel || null,
    source_type: form.sourceType || null,
    filters: {
      source_id: form.sourceId || null,
    },
    ...overrides,
  };
}

export function retrievalSearchSignature(payload: RetrievalSearchPayload): string {
  return JSON.stringify({
    query: payload.query,
    top_k: payload.top_k,
    schema_id: payload.schema_id ?? null,
    fields: payload.fields,
    detected_format: payload.detected_format ?? null,
    resource_type: payload.resource_type ?? null,
    clinical_domain: payload.clinical_domain ?? null,
    standard_system: payload.standard_system ?? null,
    trust_level: payload.trust_level ?? null,
    source_type: payload.source_type ?? null,
    source_id: payload.filters?.source_id ?? null,
    filters: payload.filters ?? {},
  });
}
