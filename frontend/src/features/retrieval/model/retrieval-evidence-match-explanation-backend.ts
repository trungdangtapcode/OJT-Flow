import type { RetrievalHit } from "../../../types";
import type { EvidenceSupportStatus } from "./retrieval-evidence-types";
import {
  hitSupportStatusValue,
  numberValue,
  optionalStringValue,
  recordValue,
  stringArrayValue,
  stringValue,
} from "./retrieval-evidence-utils";

type BackendTopScoreComponent = {
  component: string;
  label: string;
  rank: number | null;
  value: number;
} | null;

export type BackendMatchExplanationValues = {
  aspectIds: string[];
  aspectLabels: string[];
  bucketIds: string[];
  bucketLabels: string[];
  conceptIds: string[];
  conceptLabels: string[];
  matchedTerms: string[];
  provenanceCount: number | null;
  provenanceFields: string[];
  rankingSignalCount: number | null;
  rankingSignalRuleIds: string[];
  supportStatus: EvidenceSupportStatus | null;
  topScoreComponent: BackendTopScoreComponent;
  topScoreDriver: string | null;
};

export function backendMatchExplanationValues(
  hit: RetrievalHit,
): BackendMatchExplanationValues {
  const backendExplanation = recordValue(hit.match_explanation);
  const backendTopComponent = recordValue(backendExplanation.top_score_component);

  return {
    aspectIds: stringArrayValue(backendExplanation.aspect_ids).slice(0, 8),
    aspectLabels: stringArrayValue(backendExplanation.aspect_labels).slice(0, 4),
    bucketIds: stringArrayValue(backendExplanation.bucket_ids).slice(0, 8),
    bucketLabels: stringArrayValue(backendExplanation.bucket_labels).slice(0, 4),
    conceptIds: stringArrayValue(backendExplanation.concept_ids).slice(0, 8),
    conceptLabels: stringArrayValue(backendExplanation.concept_labels).slice(0, 4),
    matchedTerms: stringArrayValue(backendExplanation.matched_terms).slice(0, 6),
    provenanceCount: numberValue(backendExplanation.provenance_count),
    provenanceFields: stringArrayValue(backendExplanation.provenance_fields).slice(0, 12),
    rankingSignalCount: numberValue(backendExplanation.ranking_signal_count),
    rankingSignalRuleIds: stringArrayValue(
      backendExplanation.ranking_signal_rule_ids,
    ).slice(0, 12),
    supportStatus: hitSupportStatusValue(backendExplanation.support_status),
    topScoreComponent: backendTopComponent.component
      ? {
          component: stringValue(backendTopComponent.component, ""),
          label: stringValue(backendTopComponent.label, "Score component"),
          rank: numberValue(backendTopComponent.rank),
          value: numberValue(backendTopComponent.value) ?? 0,
        }
      : null,
    topScoreDriver: optionalStringValue(backendExplanation.top_score_driver),
  };
}
