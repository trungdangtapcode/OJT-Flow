export function recordValue(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return value as Record<string, unknown>;
}

export function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

export function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

export function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function booleanValue(value: unknown): boolean {
  return value === true;
}

export function optionalBooleanValue(value: unknown): boolean | null {
  if (value === true) return true;
  if (value === false) return false;
  return null;
}

export function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

export function numericRecordValue(value: unknown): Record<string, number> {
  const record = recordValue(value);
  return Object.fromEntries(
    Object.entries(record)
      .map(([key, item]) => [key, numberValue(item)] as const)
      .filter((entry): entry is readonly [string, number] => entry[1] !== null),
  );
}
