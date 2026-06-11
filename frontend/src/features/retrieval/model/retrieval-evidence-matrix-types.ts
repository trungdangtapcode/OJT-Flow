import type { EvidenceSupportStatus } from "./retrieval-evidence-support-types";

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
