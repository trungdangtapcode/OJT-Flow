import {
  evidenceSupportStatus,
} from "./retrieval-evidence-support-summary";
import type { BackendMatchExplanationValues } from "./retrieval-evidence-match-explanation-backend";
import type { FallbackMatchExplanationValues } from "./retrieval-evidence-match-explanation-fallback";
import type {
  EvidenceHitMatchExplanation,
} from "./retrieval-evidence-types";
import type { EvidenceSupportSummary } from "./retrieval-evidence-support-types";
import { nonEmptyStringArray } from "./retrieval-evidence-utils";

export function matchExplanationArrayValue(
  backendValues: string[],
  fallbackValues: string[],
): string[] {
  return nonEmptyStringArray(backendValues, fallbackValues);
}

export function matchExplanationTopScoreComponentValue(
  backendValue: EvidenceHitMatchExplanation["topScoreComponent"],
  fallbackValue: EvidenceHitMatchExplanation["topScoreComponent"],
) {
  return backendValue ? backendValue : fallbackValue;
}

export function mergeMatchExplanationValues({
  backendValues,
  fallbackValues,
  supportSummary,
}: {
  backendValues: BackendMatchExplanationValues;
  fallbackValues: FallbackMatchExplanationValues;
  supportSummary: EvidenceSupportSummary;
}): EvidenceHitMatchExplanation {
  return {
    aspectIds: matchExplanationArrayValue(
      backendValues.aspectIds,
      fallbackValues.aspectIds,
    ),
    aspectLabels: matchExplanationArrayValue(
      backendValues.aspectLabels,
      fallbackValues.aspectLabels,
    ),
    bucketIds: matchExplanationArrayValue(
      backendValues.bucketIds,
      fallbackValues.bucketIds,
    ),
    bucketLabels: matchExplanationArrayValue(
      backendValues.bucketLabels,
      fallbackValues.bucketLabels,
    ),
    conceptIds: matchExplanationArrayValue(
      backendValues.conceptIds,
      fallbackValues.conceptIds,
    ),
    conceptLabels: matchExplanationArrayValue(
      backendValues.conceptLabels,
      fallbackValues.conceptLabels,
    ),
    matchedTerms: matchExplanationArrayValue(
      backendValues.matchedTerms,
      fallbackValues.matchedTerms,
    ),
    provenanceCount: backendValues.provenanceCount ?? fallbackValues.provenanceCount,
    provenanceFields: matchExplanationArrayValue(
      backendValues.provenanceFields,
      fallbackValues.provenanceFields,
    ),
    rankingSignalCount: backendValues.rankingSignalCount ?? fallbackValues.rankingSignalCount,
    rankingSignalRuleIds: matchExplanationArrayValue(
      backendValues.rankingSignalRuleIds,
      fallbackValues.rankingSignalRuleIds,
    ),
    supportStatus:
      backendValues.supportStatus ?? evidenceSupportStatus(supportSummary),
    topScoreComponent: matchExplanationTopScoreComponentValue(
      backendValues.topScoreComponent,
      fallbackValues.topScoreComponent,
    ),
    topScoreDriver:
      backendValues.topScoreDriver ??
      fallbackValues.topScoreDriver,
  };
}
