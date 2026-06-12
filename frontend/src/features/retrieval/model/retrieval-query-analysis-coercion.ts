export {
  booleanValue,
  numberValue,
  optionalStringValue,
  recordValue,
  stringArrayValue,
  stringValue,
} from "./retrieval-runtime-values";

import { recordValue } from "./retrieval-runtime-values";

export function stringRecordValue(value: unknown): Record<string, string> {
  const record = recordValue(value);
  return Object.fromEntries(
    Object.entries(record).filter(
      (entry): entry is [string, string] => typeof entry[1] === "string",
    ),
  );
}

export function uniqueValues(values: Array<string | null | undefined>): string[] {
  return Array.from(
    new Set(values.filter((value): value is string => typeof value === "string" && value.length > 0)),
  ).sort((left, right) => left.localeCompare(right));
}
