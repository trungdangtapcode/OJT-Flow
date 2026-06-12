import type { RetrievalJudgmentEvaluationResult } from "../../../types";
import { JudgmentMetricCard } from "./judgment-metric-card";
import type { RelevanceJudgmentMetricsView } from "./judgment-evaluation-types";

export function LocalJudgmentMetricGrid({
  formatNullableDecimal,
  formatNullablePercent,
  formatPercent,
  metrics,
}: {
  formatNullableDecimal: (value: number | null) => string;
  formatNullablePercent: (value: number | null) => string;
  formatPercent: (value: number) => string;
  metrics: RelevanceJudgmentMetricsView;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
      <JudgmentMetricCard
        label="Coverage"
        tone={metrics.judgmentCoverage >= 0.5 ? "success" : "warning"}
        value={formatPercent(metrics.judgmentCoverage)}
      />
      <JudgmentMetricCard
        label="Precision@k"
        tone={metrics.precisionAtK >= 0.5 ? "success" : "warning"}
        value={formatPercent(metrics.precisionAtK)}
      />
      <JudgmentMetricCard
        label="Judged precision"
        tone={(metrics.judgedPrecision ?? 0) >= 0.5 ? "success" : "warning"}
        value={formatNullablePercent(metrics.judgedPrecision)}
      />
      <JudgmentMetricCard
        label="nDCG@k"
        tone={(metrics.ndcgAtK ?? 0) >= 0.5 ? "success" : "warning"}
        value={formatNullableDecimal(metrics.ndcgAtK)}
      />
    </div>
  );
}

export function ServerJudgmentMetricGrid({
  evaluation,
  formatCount,
  formatDecimal,
  formatNullableDecimal,
  formatPercent,
}: {
  evaluation: RetrievalJudgmentEvaluationResult;
  formatCount: (count: number, singular: string, plural?: string) => string;
  formatDecimal: (value: number) => string;
  formatNullableDecimal: (value: number | null) => string;
  formatPercent: (value: number) => string;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
      <JudgmentMetricCard
        label="Server coverage"
        tone={evaluation.coverage_at_k >= 0.5 ? "success" : "warning"}
        value={formatPercent(evaluation.coverage_at_k)}
      />
      <JudgmentMetricCard
        label="Server HitRate@k"
        tone={evaluation.hit_rate_at_k >= 1 ? "success" : "warning"}
        value={formatPercent(evaluation.hit_rate_at_k)}
      />
      <JudgmentMetricCard
        label="Server MAP@k"
        tone={evaluation.average_precision_at_k >= 0.5 ? "success" : "warning"}
        value={formatDecimal(evaluation.average_precision_at_k)}
      />
      <JudgmentMetricCard
        label="Server MRR@k"
        tone={evaluation.mrr_at_k >= 0.5 ? "success" : "warning"}
        value={formatDecimal(evaluation.mrr_at_k)}
      />
      <JudgmentMetricCard
        label="Server nDCG@k"
        tone={(evaluation.ndcg_at_k ?? 0) >= 0.5 ? "success" : "warning"}
        value={formatNullableDecimal(evaluation.ndcg_at_k ?? null)}
      />
      <JudgmentMetricCard
        label="Server unjudged"
        tone={evaluation.unjudged_count ? "warning" : "success"}
        value={formatCount(evaluation.unjudged_count, "hit")}
      />
    </div>
  );
}
