import type { EvidenceSupportMatrixRowView } from "./evidence-support-matrix";

export type EvidenceSupportStatus = EvidenceSupportMatrixRowView["supportStatus"];

export type EvidenceUseGuidanceView = {
  action: string;
  reasons: string[];
  status: EvidenceSupportStatus;
  title: string;
};

export type EvidenceUsabilitySummaryView = {
  checks: string[];
  headline: string;
  limitation: string;
  recommendation: string;
  status: EvidenceSupportStatus;
};

export type HitMatchExplanationView = {
  aspectLabels: string[];
  bucketLabels: string[];
  conceptLabels: string[];
  matchedTerms: string[];
  provenanceCount: number;
  rankingSignalCount: number;
  supportStatus: EvidenceSupportStatus;
  topScoreDriver: string | null;
};
