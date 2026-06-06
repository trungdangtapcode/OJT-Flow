import { humanize } from "../../../lib/utils";
import type {
  RetrievalEvidenceBucket,
  RetrievalHit,
  RetrievalScoreComponent,
} from "../../../types";
import {
  evidenceSupportStatus,
  evidenceSupportSummary,
} from "./retrieval-evidence-support";
import type {
  EvidenceConceptMatchSignal,
  EvidenceHitMatchExplanation,
  EvidenceHitSignals,
  EvidenceProvenanceEntry,
  EvidenceQueryAspectMatchSignal,
  EvidenceRankingBoostSignal,
} from "./retrieval-evidence-types";
import {
  formatRankingSignal,
  formatSignedDelta,
  hitSupportStatusValue,
  nonEmptyStringArray,
  numberValue,
  optionalStringValue,
  rankingBoostDetailsValue,
  recordValue,
  stringArrayValue,
  stringRecordValue,
  stringValue,
  uniqueValues,
} from "./retrieval-evidence-utils";

export function evidenceSignalsFromHit(hit: RetrievalHit): EvidenceHitSignals {
  return {
    conceptMatches: conceptMatchesFromHit(hit),
    queryAspectMatches: queryAspectMatchesFromHit(hit),
    rankingBoostSignals: rankingBoostSignalsFromHit(hit),
    scoreComponents: scoreComponentsFromHit(hit),
  };
}

export function scoreComponentsFromHit(hit: RetrievalHit): RetrievalScoreComponent[] {
  return (hit.score_components ?? [])
    .map((component) => ({
      component: stringValue(component.component, ""),
      description: stringValue(
        component.description,
        "Score component contribution.",
      ),
      label: stringValue(component.label, humanize(component.component)),
      metadata: recordValue(component.metadata),
      rank: typeof component.rank === "number" ? component.rank : null,
      value: numberValue(component.value) ?? 0,
    }))
    .filter((component) => component.component);
}

export function hitMatchExplanation({
  buckets,
  hit,
  provenanceEntries,
  signals,
}: {
  buckets: RetrievalEvidenceBucket[];
  hit: RetrievalHit;
  provenanceEntries: EvidenceProvenanceEntry[];
  signals: EvidenceHitSignals;
}): EvidenceHitMatchExplanation {
  const evidenceId = hit.evidence.evidence_id;
  const bucketLabels = buckets
    .filter((bucket) => bucket.evidence_ids.includes(evidenceId))
    .map((bucket) => bucket.label);
  const matchedBuckets = buckets.filter((bucket) =>
    bucket.evidence_ids.includes(evidenceId),
  );
  const topComponent = [...signals.scoreComponents].sort(
    (left, right) => Math.abs(right.value) - Math.abs(left.value),
  )[0];
  const supportSummary = evidenceSupportSummary({
    hit,
    provenanceEntries,
    signals,
  });
  const backendExplanation = recordValue(hit.match_explanation);
  const backendTopComponent = recordValue(backendExplanation.top_score_component);
  return {
    aspectIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.aspect_ids).slice(0, 8),
      uniqueValues(signals.queryAspectMatches.map((match) => match.aspectId)).slice(0, 8),
    ),
    aspectLabels: nonEmptyStringArray(
      stringArrayValue(backendExplanation.aspect_labels).slice(0, 4),
      uniqueValues(signals.queryAspectMatches.map((match) => match.label)).slice(0, 4),
    ),
    bucketIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.bucket_ids).slice(0, 8),
      uniqueValues(matchedBuckets.map((bucket) => bucket.bucket_id)).slice(0, 8),
    ),
    bucketLabels: nonEmptyStringArray(
      stringArrayValue(backendExplanation.bucket_labels).slice(0, 4),
      uniqueValues(bucketLabels).slice(0, 4),
    ),
    conceptIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.concept_ids).slice(0, 8),
      uniqueValues(signals.conceptMatches.map((match) => match.conceptId)).slice(0, 8),
    ),
    conceptLabels: nonEmptyStringArray(
      stringArrayValue(backendExplanation.concept_labels).slice(0, 4),
      uniqueValues(
        signals.conceptMatches.map((match) =>
          match.code ? `${match.standardSystem} ${match.code}` : match.displayName,
        ),
      ).slice(0, 4),
    ),
    matchedTerms: nonEmptyStringArray(
      stringArrayValue(backendExplanation.matched_terms).slice(0, 6),
      uniqueValues(hit.matched_terms).slice(0, 6),
    ),
    provenanceCount:
      numberValue(backendExplanation.provenance_count) ?? provenanceEntries.length,
    provenanceFields: nonEmptyStringArray(
      stringArrayValue(backendExplanation.provenance_fields).slice(0, 12),
      uniqueValues(provenanceEntries.map((entry) => entry.label)).slice(0, 12),
    ),
    rankingSignalCount:
      numberValue(backendExplanation.ranking_signal_count) ??
      signals.rankingBoostSignals.length,
    rankingSignalRuleIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.ranking_signal_rule_ids).slice(0, 12),
      uniqueValues(signals.rankingBoostSignals.map((signal) => signal.ruleId)).slice(0, 12),
    ),
    supportStatus:
      hitSupportStatusValue(backendExplanation.support_status) ??
      evidenceSupportStatus(supportSummary),
    topScoreComponent: backendTopComponent.component
      ? {
          component: stringValue(backendTopComponent.component, ""),
          label: stringValue(backendTopComponent.label, "Score component"),
          rank: numberValue(backendTopComponent.rank),
          value: numberValue(backendTopComponent.value) ?? 0,
        }
      : topComponent
        ? {
            component: topComponent.component,
            label: topComponent.label,
            rank: topComponent.rank ?? null,
            value: topComponent.value,
          }
        : null,
    topScoreDriver:
      optionalStringValue(backendExplanation.top_score_driver) ??
      (topComponent
        ? `${topComponent.label} ${formatSignedDelta(topComponent.value)}`
        : null),
  };
}

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
