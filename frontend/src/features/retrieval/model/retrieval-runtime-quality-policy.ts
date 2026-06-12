import type { RetrievalPackage } from "../../../types";
import {
  numberValue,
  numericRecordValue,
  optionalBooleanValue,
  recordValue,
  stringArrayValue,
  stringValue,
} from "./retrieval-runtime-values";

export type RetrievalQualityPolicyStack = {
  blockingSeverities: string[];
  conceptGroundingRequirements: {
    minConfidence: number | null;
    requireDetectedConcepts: boolean | null;
  };
  provenanceRequirements: {
    locatorAnyKeys: string[];
    requireSourceVersion: boolean | null;
    sourceTypes: string[];
  };
  rankingThresholds: Record<string, number>;
  reviewScoreBelow: number | null;
  reviewSeverities: string[];
  severityPenalties: Record<string, number>;
  version: string;
};

export function qualityPolicyFromPackage(
  packageData: RetrievalPackage,
): RetrievalQualityPolicyStack {
  const policy = recordValue(packageData.handoff_context.quality_policy);
  const conceptGroundingRequirements = recordValue(
    policy.concept_grounding_requirements,
  );
  const provenanceRequirements = recordValue(policy.provenance_requirements);
  return {
    blockingSeverities: stringArrayValue(policy.blocking_severities),
    conceptGroundingRequirements: {
      minConfidence: numberValue(conceptGroundingRequirements.min_confidence),
      requireDetectedConcepts: optionalBooleanValue(
        conceptGroundingRequirements.require_detected_concepts,
      ),
    },
    provenanceRequirements: {
      locatorAnyKeys: stringArrayValue(provenanceRequirements.locator_any_keys),
      requireSourceVersion: optionalBooleanValue(
        provenanceRequirements.require_source_version,
      ),
      sourceTypes: stringArrayValue(provenanceRequirements.source_types),
    },
    rankingThresholds: numericRecordValue(policy.ranking_thresholds),
    reviewScoreBelow: numberValue(policy.review_score_below),
    reviewSeverities: stringArrayValue(policy.review_severities),
    severityPenalties: numericRecordValue(policy.severity_penalties),
    version: stringValue(policy.version, "unknown"),
  };
}

export function formatQualityPolicyTrace(policy: RetrievalQualityPolicyStack): string {
  const warningPenalty = policy.severityPenalties.warning;
  const destructivePenalty = policy.severityPenalties.destructive;
  const minTopMatchedTerms = policy.rankingThresholds.min_top_matched_terms;
  const thresholdText =
    policy.reviewScoreBelow === null ? "review threshold unknown" : `review < ${policy.reviewScoreBelow}`;
  const matchText =
    minTopMatchedTerms === undefined
      ? null
      : `top match >= ${minTopMatchedTerms}`;
  const conceptText =
    policy.conceptGroundingRequirements.requireDetectedConcepts === true
      ? `concepts >= ${(policy.conceptGroundingRequirements.minConfidence ?? 0).toFixed(2)}`
      : null;
  const provenanceText = policy.provenanceRequirements.sourceTypes.length
    ? `provenance ${policy.provenanceRequirements.sourceTypes.length} source types`
    : null;
  const penaltyText = [
    warningPenalty === undefined ? null : `warning -${warningPenalty}`,
    destructivePenalty === undefined ? null : `blocker -${destructivePenalty}`,
  ].filter(Boolean);
  return [policy.version, thresholdText, matchText, conceptText, provenanceText, ...penaltyText]
    .filter(Boolean)
    .join(" / ");
}
