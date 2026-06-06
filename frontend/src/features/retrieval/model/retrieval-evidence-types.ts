import type { RetrievalScoreComponent } from "../../../types";

export type EvidenceProvenanceEntry = {
  href: string | null;
  label: string;
  value: string;
};

export type EvidenceSupportStatus = "strong" | "partial" | "weak";

export type EvidenceSupportSummary = {
  aspect_count: number;
  concept_count: number;
  matched_term_count: number;
  provenance_field_count: number;
  ranking_signal_count: number;
};

export type EvidenceUseGuidance = {
  action: string;
  reasons: string[];
  status: EvidenceSupportStatus;
  title: string;
};

export type EvidenceUsabilitySummary = {
  checks: string[];
  headline: string;
  limitation: string;
  recommendation: string;
  status: EvidenceSupportStatus;
};

export type RetrievalEvidenceJudgment = {
  value: "relevant" | "partial" | "not_relevant";
};

export type EvidenceSupportMatrixRow = {
  aspectCount: number;
  bucketLabels: string[];
  conceptCount: number;
  confidenceLabel: string;
  evidenceId: string;
  judgment: RetrievalEvidenceJudgment | null;
  matchedTermCount: number;
  provenanceCount: number;
  rank: number;
  score: number;
  sourceId: string;
  sourceType: string;
  standardSystem: string | null;
  supportStatus: EvidenceSupportStatus;
};

export type EvidenceRankingBoostSignal = {
  label: string;
  reason: string;
  ruleId: string;
  weight: number | null;
};

export type EvidenceConceptMatchSignal = {
  clinicalDomain: string | null;
  code: string | null;
  conceptId: string;
  confidence: number;
  displayName: string;
  matchedAliases: string[];
  matchedFields: string[];
  matchedTerms: string[];
  reason: string;
  standardSystem: string;
};

export type EvidenceQueryAspectMatchSignal = {
  aspectId: string;
  label: string;
  matchedFilters: Record<string, string>;
  matchedTerms: string[];
  priority: number;
  reason: string;
  ruleId: string;
};

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

export type EvidenceHitSignals = {
  conceptMatches: EvidenceConceptMatchSignal[];
  queryAspectMatches: EvidenceQueryAspectMatchSignal[];
  rankingBoostSignals: EvidenceRankingBoostSignal[];
  scoreComponents: RetrievalScoreComponent[];
};
