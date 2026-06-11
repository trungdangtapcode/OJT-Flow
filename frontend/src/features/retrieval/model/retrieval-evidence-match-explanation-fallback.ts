import type { RetrievalEvidenceBucket, RetrievalHit } from "../../../types";
import {
  matchedBucketIds,
  matchedBucketLabels,
  topScoreComponentValue,
  topScoreDriverValue,
} from "./retrieval-evidence-match-explanation-values";
import type {
  EvidenceHitMatchExplanation,
  EvidenceHitSignals,
  EvidenceProvenanceEntry,
} from "./retrieval-evidence-types";
import { uniqueValues } from "./retrieval-evidence-utils";

export type FallbackMatchExplanationValues = Omit<
  EvidenceHitMatchExplanation,
  "supportStatus"
>;

export function fallbackMatchExplanationValues({
  buckets,
  hit,
  provenanceEntries,
  signals,
}: {
  buckets: RetrievalEvidenceBucket[];
  hit: RetrievalHit;
  provenanceEntries: EvidenceProvenanceEntry[];
  signals: EvidenceHitSignals;
}): FallbackMatchExplanationValues {
  const evidenceId = hit.evidence.evidence_id;
  const bucketLabels = matchedBucketLabels(buckets, evidenceId);
  const topScoreComponent = topScoreComponentValue(signals.scoreComponents);
  return {
    aspectIds: uniqueValues(signals.queryAspectMatches.map((match) => match.aspectId)).slice(0, 8),
    aspectLabels: uniqueValues(signals.queryAspectMatches.map((match) => match.label)).slice(0, 4),
    bucketIds: matchedBucketIds(buckets, evidenceId),
    bucketLabels: uniqueValues(bucketLabels).slice(0, 4),
    conceptIds: uniqueValues(signals.conceptMatches.map((match) => match.conceptId)).slice(0, 8),
    conceptLabels: uniqueValues(
      signals.conceptMatches.map((match) =>
        match.code ? `${match.standardSystem} ${match.code}` : match.displayName,
      ),
    ).slice(0, 4),
    matchedTerms: uniqueValues(hit.matched_terms).slice(0, 6),
    provenanceCount: provenanceEntries.length,
    provenanceFields: uniqueValues(provenanceEntries.map((entry) => entry.label)).slice(0, 12),
    rankingSignalCount: signals.rankingBoostSignals.length,
    rankingSignalRuleIds: uniqueValues(signals.rankingBoostSignals.map((signal) => signal.ruleId)).slice(0, 12),
    topScoreComponent,
    topScoreDriver: topScoreDriverValue(topScoreComponent),
  };
}
