import type { Evidence, RetrievalJudgmentValue } from "../../../types";

export type RelevanceJudgmentValue = RetrievalJudgmentValue;

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
  sourcePolicyBlockedCount: number;
  staleCount: number;
  totalHits: number;
  unsafeCount: number;
};
