export type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export type RelevanceJudgmentMetricsView = {
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
