import type { RetrievalPackage } from "../../../types";

export function searchAnswerWarnings(packageData: RetrievalPackage): string[] {
  return [
    ...(packageData.trace.warnings ?? []),
    ...((packageData.coverage?.warnings ?? []) as string[]),
  ].filter((warning) => warning.trim());
}

export function stringFromRecord(record: Record<string, unknown>, key: string): string | null {
  const value = record[key];
  return typeof value === "string" && value.trim() ? value : null;
}

export function formatSearchAnswerCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
