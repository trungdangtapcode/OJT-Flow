import { humanize } from "../../../lib/utils";
import type { QueryProfileStack } from "./retrieval-query-analysis-types";
import {
  recordValue,
  stringArrayValue,
  stringRecordValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";

export function queryProfileValue(value: unknown): QueryProfileStack | null {
  const profile = recordValue(value);
  const profileId = stringValue(profile.profile_id, "");
  if (!profileId) return null;
  return {
    complexity: stringValue(profile.complexity, "unknown"),
    description: stringValue(profile.description, "No query profile description provided."),
    label: stringValue(profile.label, humanize(profileId)),
    profileId,
    retrievalMode: stringValue(profile.retrieval_mode, "unknown"),
    route: stringValue(profile.route, "retrieval"),
    ruleIds: stringArrayValue(profile.rule_ids),
    suggestedFilters: stringRecordValue(profile.suggested_filters),
  };
}
