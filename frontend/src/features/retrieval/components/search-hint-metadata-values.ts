import type {
  SearchHintLineageFollowup,
  SearchHintParameterExample,
} from "./search-hint-metadata";

export function searchHintParameterExamples(
  value: unknown,
): SearchHintParameterExample[] {
  return Array.isArray(value)
    ? value.flatMap((item) => {
        if (!item || typeof item !== "object" || Array.isArray(item)) return [];
        const record = item as Record<string, unknown>;
        const name = optionalStringValue(record.name);
        const targetField = optionalStringValue(record.target_field);
        const example = optionalStringValue(record.example);
        if (!name || !targetField || !example) return [];
        return [
          {
            example,
            matchedDatasetField: Boolean(record.matched_dataset_field),
            name,
            targetField,
          },
        ];
      })
    : [];
}

export function searchHintLineageFollowup(
  value: unknown,
): SearchHintLineageFollowup[] {
  return Array.isArray(value)
    ? value.flatMap((item) => {
        if (!item || typeof item !== "object" || Array.isArray(item)) return [];
        const record = item as Record<string, unknown>;
        const parameter = optionalStringValue(record.parameter);
        const purpose = optionalStringValue(record.purpose);
        return parameter && purpose ? [{ parameter, purpose }] : [];
      })
    : [];
}

export function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

export function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}
