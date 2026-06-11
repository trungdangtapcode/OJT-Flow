import type { RetrievalSearchPayload, RetrievalSearchTask } from "../../../types";

type RetrievalPayloadFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

const payloadFilterFields = new Set<RetrievalPayloadFilterField>([
  "clinical_domain",
  "standard_system",
  "source_type",
  "trust_level",
  "source_id",
]);

export function plannedTaskSearchOverrides(
  task: RetrievalSearchTask,
): Partial<RetrievalSearchPayload> {
  const overrides: Partial<RetrievalSearchPayload> = {
    query: task.query,
  };
  for (const [field, value] of Object.entries(task.suggested_filters)) {
    if (!isRetrievalPayloadFilterField(field)) continue;
    if (field === "source_id") {
      overrides.filters = { ...(overrides.filters ?? {}), source_id: value };
    } else {
      overrides[field] = value;
    }
  }
  return overrides;
}

export function isRetrievalPayloadFilterField(
  value: string,
): value is RetrievalPayloadFilterField {
  return payloadFilterFields.has(value as RetrievalPayloadFilterField);
}
