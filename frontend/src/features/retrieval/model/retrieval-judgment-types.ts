import type { Evidence } from "../../../types";

export type RelevanceJudgmentValue = "relevant" | "partial" | "not_relevant";

export type RelevanceJudgment = {
  evidenceId: string;
  judgedAt: string;
  judgmentId?: string | null;
  query: string;
  rating: number;
  runId: string;
  searchSignature?: string | null;
  sourceId?: string | null;
  value: RelevanceJudgmentValue;
};

export type RelevanceJudgmentIndex = Record<string, RelevanceJudgment>;

export type SetHitJudgmentInput = {
  evidence: Evidence;
  queryText: string;
  runId: string;
  searchSignature: string | null;
  value: RelevanceJudgmentValue;
};

export type RelevanceJudgmentMetrics = {
  averageRating: number | null;
  judgedCount: number;
  judgedPrecision: number | null;
  judgmentCoverage: number;
  ndcgAtK: number | null;
  notRelevantCount: number;
  partialCount: number;
  precisionAtK: number;
  relevantCount: number;
  totalHits: number;
};
