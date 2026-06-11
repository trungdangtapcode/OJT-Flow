import type { EvidenceSupportStatus } from "./retrieval-evidence-support-types";

export type EvidenceHitMatchExplanation = {
  aspectIds: string[];
  aspectLabels: string[];
  bucketIds: string[];
  bucketLabels: string[];
  conceptIds: string[];
  conceptLabels: string[];
  matchedTerms: string[];
  provenanceCount: number;
  provenanceFields: string[];
  rankingSignalCount: number;
  rankingSignalRuleIds: string[];
  supportStatus: EvidenceSupportStatus;
  topScoreComponent: {
    component: string;
    label: string;
    rank: number | null;
    value: number;
  } | null;
  topScoreDriver: string | null;
};
