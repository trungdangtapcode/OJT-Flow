import {
  retrievalRulePacksFromPackage,
  rulePackFingerprint,
  type RetrievalSearchRun,
} from "./retrieval-run-summary";
import type { RetrievalRulePackChange } from "./retrieval-run-comparison-types";
import { uniqueComparisonValues } from "./retrieval-run-comparison-value-utils";

export function rulePackChangesBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalRulePackChange[] {
  const activePacks = retrievalRulePacksFromPackage(activeRun.packageData);
  const baselinePacks = retrievalRulePacksFromPackage(baselineRun.packageData);
  const activeByName = new Map(activePacks.map((pack) => [pack.name, pack]));
  const baselineByName = new Map(baselinePacks.map((pack) => [pack.name, pack]));
  const packNames = uniqueComparisonValues([...activeByName.keys(), ...baselineByName.keys()]);
  return packNames.map((name) => {
    const active = activeByName.get(name);
    const baseline = baselineByName.get(name);
    let status: RetrievalRulePackChange["status"] = "stable";
    if (active && !baseline) status = "added";
    else if (!active && baseline) status = "removed";
    else if (rulePackFingerprint(active) !== rulePackFingerprint(baseline)) {
      status = "changed";
    }
    return { active, baseline, name, status };
  });
}

export function comparisonRulePackChangeViews(
  rulePackChanges: RetrievalRulePackChange[],
) {
  return rulePackChanges.map((change) => ({
    activeFingerprint: rulePackFingerprint(change.active),
    baselineFingerprint: rulePackFingerprint(change.baseline),
    name: change.name,
    status: change.status,
  }));
}
