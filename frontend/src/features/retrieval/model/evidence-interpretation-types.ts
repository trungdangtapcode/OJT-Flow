export type EvidenceSupportStatus = "strong" | "partial" | "weak";

export type EvidenceInterpretationCard = {
  detail: string;
  items: string[];
  label: string;
  title: string;
};

export type EvidenceInterpretationViewModel = {
  cards: EvidenceInterpretationCard[];
  status: string;
  summary: string;
  supportStatus: EvidenceSupportStatus | null;
};
