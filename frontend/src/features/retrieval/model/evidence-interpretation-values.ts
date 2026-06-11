import type { RetrievalPackage, RetrievalRecommendedAction } from "../../../types";
import type { EvidenceSupportStatus } from "./evidence-interpretation-types";

export function primaryEvidenceAction(
  packageData: RetrievalPackage,
): RetrievalRecommendedAction | null {
  return [...(packageData.recommended_actions ?? [])].sort(
    (left, right) => left.priority - right.priority,
  )[0] ?? null;
}

export function packageWarnings(packageData: RetrievalPackage): string[] {
  return [
    ...(packageData.trace.warnings ?? []),
    ...((packageData.coverage?.warnings ?? []) as string[]),
  ].filter((warning) => warning.trim());
}

export function supportStatusValue(value: unknown): EvidenceSupportStatus | null {
  return value === "strong" || value === "partial" || value === "weak" ? value : null;
}

export function stringFromRecord(record: unknown, key: string): string | null {
  if (!record || typeof record !== "object" || Array.isArray(record)) return null;
  const value = (record as Record<string, unknown>)[key];
  return typeof value === "string" && value.trim() ? value : null;
}

export function stringArrayFromRecord(record: unknown, key: string): string[] {
  if (!record || typeof record !== "object" || Array.isArray(record)) return [];
  const value = (record as Record<string, unknown>)[key];
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0)
    : [];
}

export function formatEvidenceInterpretationCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
