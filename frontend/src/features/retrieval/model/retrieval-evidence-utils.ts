import { humanize } from "../../../lib/utils";
import type {
  EvidenceRankingBoostSignal,
  EvidenceSupportStatus,
} from "./retrieval-evidence-types";

export function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

export function hitSupportStatusValue(value: unknown): EvidenceSupportStatus | null {
  return value === "strong" || value === "partial" || value === "weak"
    ? value
    : null;
}

export function nonEmptyStringArray(values: string[], fallback: string[]): string[] {
  return values.length ? values : fallback;
}

export function rankingBoostDetailsValue(value: unknown): EvidenceRankingBoostSignal[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      label: stringValue(item.label, "Ranking boost"),
      reason: stringValue(item.reason, "Ranking boost rule applied."),
      ruleId: stringValue(item.rule_id, ""),
      weight: numberValue(item.weight),
    }))
    .filter((item) => item.ruleId);
}

export function formatRankingSignal(ruleId: string): string {
  return humanize(ruleId.replace(/^boost_/, ""));
}

export function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

export function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

export function numberValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (item): item is string => typeof item === "string" && item.trim().length > 0,
  );
}

export function stringRecordValue(value: unknown): Record<string, string> {
  const source = recordValue(value);
  return Object.fromEntries(
    Object.entries(source)
      .filter((entry): entry is [string, string] => typeof entry[1] === "string")
      .filter(([, item]) => item.trim().length > 0),
  );
}

export function uniqueValues(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
}

export function formatSignedDelta(delta: number): string {
  return delta > 0 ? `+${delta}` : String(delta);
}
