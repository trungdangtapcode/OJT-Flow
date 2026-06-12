import type {
  RetrievalPackage,
  RuntimeRetrievalRulePack,
} from "../../../types";
import {
  booleanValue,
  numberValue,
  optionalStringValue,
  recordValue,
  stringValue,
} from "./retrieval-run-summary-values";

export function retrievalRulePacksFromPackage(
  packageData: RetrievalPackage,
): RuntimeRetrievalRulePack[] {
  const rawPacks = packageData.handoff_context.retrieval_rule_packs;
  if (!Array.isArray(rawPacks)) return [];
  return rawPacks
    .map((rawPack) => recordValue(rawPack))
    .map((pack) => ({
      name: stringValue(pack.name, ""),
      status: rulePackStatusValue(pack.status),
      source: stringValue(pack.source, "unknown"),
      env_var: stringValue(pack.env_var, ""),
      configured: booleanValue(pack.configured),
      rule_count: numberValue(pack.rule_count) ?? 0,
      version: optionalStringValue(pack.version),
      content_hash: optionalStringValue(pack.content_hash),
      error: optionalStringValue(pack.error) ?? undefined,
    }))
    .filter((pack) => pack.name && pack.env_var);
}

export function rulePackFingerprint(pack?: RuntimeRetrievalRulePack): string {
  if (!pack) return "missing";
  if (pack.content_hash) return pack.content_hash;
  if (pack.version) return pack.version;
  return `${pack.status}:${pack.rule_count}`;
}

function rulePackStatusValue(value: unknown): RuntimeRetrievalRulePack["status"] {
  if (value === "ok" || value === "missing" || value === "error") return value;
  return "error";
}
