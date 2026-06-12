import type { RetrievalPackage } from "../../../types";
import { retrievalRulePacksFromPackage } from "./retrieval-run-summary";

export function retrievalCockpitRulePackReport(packageData: RetrievalPackage) {
  return retrievalRulePacksFromPackage(packageData).map((pack) => ({
    name: pack.name,
    status: pack.status,
    source: pack.source,
    env_var: pack.env_var,
    configured: pack.configured,
    rule_count: pack.rule_count,
    version: pack.version ?? null,
    content_hash: pack.content_hash ?? null,
  }));
}
