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
