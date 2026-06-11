export type SearchHintParameterExample = {
  example: string;
  matchedDatasetField: boolean;
  name: string;
  targetField: string;
};

export type SearchHintLineageFollowup = {
  parameter: string;
  purpose: string;
};

export function searchHintParameterExamples(
  value: unknown,
): SearchHintParameterExample[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      example: stringValue(item.example, ""),
      matchedDatasetField: Boolean(item.matched_dataset_field),
      name: stringValue(item.name, ""),
      targetField: stringValue(item.target_field, ""),
    }))
    .filter((item) => item.name && item.example);
}

export function searchHintLineageFollowup(
  value: unknown,
): SearchHintLineageFollowup[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      parameter: stringValue(item.parameter, ""),
      purpose: stringValue(item.purpose, ""),
    }))
    .filter((item) => item.parameter && item.purpose);
}

export function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

export function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

export function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

export function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (item): item is string => typeof item === "string" && item.trim().length > 0,
  );
}
