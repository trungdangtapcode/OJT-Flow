import type { RetrievalScoreComponent } from "../../../types";

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

export type EvidenceHitSignals = {
  conceptMatches: EvidenceConceptMatchSignal[];
  queryAspectMatches: EvidenceQueryAspectMatchSignal[];
  rankingBoostSignals: EvidenceRankingBoostSignal[];
  scoreComponents: RetrievalScoreComponent[];
};
