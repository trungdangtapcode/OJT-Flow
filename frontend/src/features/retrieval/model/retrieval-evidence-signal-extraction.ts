import type { RetrievalHit } from "../../../types";
import type {
  EvidenceConceptMatchSignal,
  EvidenceQueryAspectMatchSignal,
  EvidenceRankingBoostSignal,
} from "./retrieval-evidence-types";
import {
  formatRankingSignal,
  numberValue,
  optionalStringValue,
  rankingBoostDetailsValue,
  recordValue,
  stringArrayValue,
  stringRecordValue,
  stringValue,
} from "./retrieval-evidence-utils";

export function rankingBoostSignalsFromHit(
  hit: RetrievalHit,
): EvidenceRankingBoostSignal[] {
  const detailedSignals = rankingBoostDetailsValue(hit.source_locator.ranking_boosts);
  if (detailedSignals.length) return detailedSignals;
  return stringArrayValue(hit.source_locator.ranking_boost_rules).map((ruleId) => ({
    label: formatRankingSignal(ruleId),
    reason: "Ranking boost rule applied.",
    ruleId,
    weight: null,
  }));
}

export function queryAspectMatchesFromHit(
  hit: RetrievalHit,
): EvidenceQueryAspectMatchSignal[] {
  const matches = hit.source_locator.query_aspect_matches;
  if (!Array.isArray(matches)) return [];
  return matches
    .map((item) => recordValue(item))
    .map((item) => ({
      aspectId: stringValue(item.aspect_id, ""),
      label: stringValue(item.label, "Search aspect"),
      matchedFilters: stringRecordValue(item.matched_filters),
      matchedTerms: stringArrayValue(item.matched_terms),
      priority: numberValue(item.priority) ?? 100,
      reason: stringValue(item.reason, "Evidence matched this search aspect."),
      ruleId: stringValue(item.rule_id, ""),
    }))
    .filter((item) => item.aspectId && item.ruleId);
}

export function conceptMatchesFromHit(hit: RetrievalHit): EvidenceConceptMatchSignal[] {
  const matches = hit.source_locator.concept_matches;
  if (!Array.isArray(matches)) return [];
  return matches
    .map((item) => recordValue(item))
    .map((item) => ({
      clinicalDomain: optionalStringValue(item.clinical_domain),
      code: optionalStringValue(item.code),
      conceptId: stringValue(item.concept_id, ""),
      confidence: numberValue(item.confidence) ?? 0,
      displayName: stringValue(item.display_name, "Medical concept"),
      matchedAliases: stringArrayValue(item.matched_aliases),
      matchedFields: stringArrayValue(item.matched_fields),
      matchedTerms: stringArrayValue(item.matched_terms),
      reason: stringValue(item.reason, "Evidence supports this detected concept."),
      standardSystem: stringValue(item.standard_system, "unknown"),
    }))
    .filter((item) => item.conceptId && item.standardSystem !== "unknown");
}
