import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { cn, humanize } from "../../../lib/utils";
import type {
  RetrievalJudgmentEvaluationResult,
  RetrievalRelevanceJudgmentSummary,
} from "../../../types";
import { SectionHelpText } from "./section-help-text";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

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

export function RelevanceJudgmentSummary({
  copyTextToClipboard,
  evaluationReportJson,
  formatCount,
  formatDecimal,
  formatNullableDecimal,
  formatNullablePercent,
  formatPercent,
  isSyncing,
  metrics,
  persistedEvaluation,
  persistedSummary,
  qualitySignalBadgeVariant,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  evaluationReportJson: string | null;
  formatCount: (count: number, singular: string, plural?: string) => string;
  formatDecimal: (value: number) => string;
  formatNullableDecimal: (value: number | null) => string;
  formatNullablePercent: (value: number | null) => string;
  formatPercent: (value: number) => string;
  isSyncing: boolean;
  metrics: RelevanceJudgmentMetricsView;
  persistedEvaluation: RetrievalJudgmentEvaluationResult | null;
  persistedSummary: RetrievalRelevanceJudgmentSummary | null;
  qualitySignalBadgeVariant: (severity: string) => BadgeVariant;
}) {
  const [evaluationCopied, setEvaluationCopied] = useState(false);

  useEffect(() => {
    if (!evaluationCopied) return undefined;
    const timeoutId = window.setTimeout(() => setEvaluationCopied(false), 1800);
    return () => window.clearTimeout(timeoutId);
  }, [evaluationCopied]);

  const copyEvaluationReport = async () => {
    if (!evaluationReportJson) return;
    await copyTextToClipboard(evaluationReportJson);
    setEvaluationCopied(true);
  };

  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
          Judgment metrics
          <HelpTooltip label="Judgment metrics help">
            Metrics summarize how many ranked hits have human relevance labels and how useful the current ranking looks for this query.
          </HelpTooltip>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={metrics.judgedCount ? "success" : "muted"}>
            {formatCount(metrics.judgedCount, "judged hit")}
          </Badge>
          {persistedSummary ? (
            <Badge variant={persistedSummary.total_count ? "success" : "muted"}>
              {formatCount(persistedSummary.total_count, "stored label")}
            </Badge>
          ) : null}
          {persistedEvaluation ? (
            <Badge variant={persistedEvaluation.judged_count ? "success" : "warning"}>
              server eval {formatCount(persistedEvaluation.judged_count, "judged")}
            </Badge>
          ) : null}
          {isSyncing ? <Badge variant="warning">syncing</Badge> : null}
          {evaluationReportJson ? (
            <>
              <Button
                aria-label="Copy retrieval judgment evaluation report"
                onClick={() => void copyEvaluationReport()}
                size="sm"
                type="button"
                variant="outline"
              >
                {evaluationCopied ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  <Clipboard className="h-4 w-4" />
                )}
                {evaluationCopied ? "Copied" : "Copy evaluation JSON"}
              </Button>
              <HelpTooltip label="Judgment evaluation JSON report help">
                Copies server relevance metrics, local judgment coverage, stored-label summary, recommendations, and query-profile context for retrieval tuning notes.
              </HelpTooltip>
            </>
          ) : null}
        </div>
      </div>
      <SectionHelpText>
        Label top hits as relevant, partial, or not relevant. Coverage shows how much of the result set has labels; Precision@k and nDCG@k become meaningful only after enough judgments exist.
      </SectionHelpText>
      {persistedEvaluation ? (
        <EvaluationReadinessPanel
          evaluation={persistedEvaluation}
          formatCount={formatCount}
          formatPercent={formatPercent}
        />
      ) : null}
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
      {persistedEvaluation ? (
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          <JudgmentMetricCard
            label="Server coverage"
            tone={persistedEvaluation.coverage_at_k >= 0.5 ? "success" : "warning"}
            value={formatPercent(persistedEvaluation.coverage_at_k)}
          />
          <JudgmentMetricCard
            label="Server HitRate@k"
            tone={persistedEvaluation.hit_rate_at_k >= 1 ? "success" : "warning"}
            value={formatPercent(persistedEvaluation.hit_rate_at_k)}
          />
          <JudgmentMetricCard
            label="Server MAP@k"
            tone={persistedEvaluation.average_precision_at_k >= 0.5 ? "success" : "warning"}
            value={formatDecimal(persistedEvaluation.average_precision_at_k)}
          />
          <JudgmentMetricCard
            label="Server MRR@k"
            tone={persistedEvaluation.mrr_at_k >= 0.5 ? "success" : "warning"}
            value={formatDecimal(persistedEvaluation.mrr_at_k)}
          />
          <JudgmentMetricCard
            label="Server nDCG@k"
            tone={(persistedEvaluation.ndcg_at_k ?? 0) >= 0.5 ? "success" : "warning"}
            value={formatNullableDecimal(persistedEvaluation.ndcg_at_k ?? null)}
          />
          <JudgmentMetricCard
            label="Server unjudged"
            tone={persistedEvaluation.unjudged_count ? "warning" : "success"}
            value={formatCount(persistedEvaluation.unjudged_count, "hit")}
          />
        </div>
      ) : null}
      {persistedEvaluation?.recommendations.length ? (
        <div className="grid gap-2">
          <div className="text-xs font-bold uppercase text-muted-foreground">
            Evaluation recommendations
          </div>
          {persistedEvaluation.recommendations.map((recommendation) => {
            const warning =
              recommendation.severity === "warning" ||
              recommendation.severity === "destructive" ||
              recommendation.severity === "error";
            return (
              <div
                className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
                key={recommendation.rule_id}
              >
                <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                  <span className="flex min-w-0 items-center gap-1.5">
                    {warning ? (
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600" />
                    ) : (
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                    )}
                    <span className="break-words font-bold">
                      {humanize(recommendation.rule_id)}
                    </span>
                  </span>
                  <Badge variant={qualitySignalBadgeVariant(recommendation.severity)}>
                    {recommendation.metric}
                  </Badge>
                </div>
                <div className="break-words text-muted-foreground">
                  {recommendation.message}
                </div>
                <div className="break-words font-semibold text-foreground">
                  {recommendation.suggested_action}
                </div>
                {recommendation.evidence_ids.length ? (
                  <div className="flex min-w-0 flex-wrap gap-1">
                    {recommendation.evidence_ids.slice(0, 4).map((evidenceId) => (
                      <code
                        className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px]"
                        key={`${recommendation.rule_id}-${evidenceId}`}
                      >
                        {evidenceId}
                      </code>
                    ))}
                    {recommendation.evidence_ids.length > 4 ? (
                      <span className="text-xs font-semibold text-muted-foreground">
                        +{recommendation.evidence_ids.length - 4} more
                      </span>
                    ) : null}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}
      {metrics.judgedCount ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          <Badge variant="success">{formatCount(metrics.relevantCount, "relevant")}</Badge>
          <Badge variant="warning">{formatCount(metrics.partialCount, "partial")}</Badge>
          <Badge variant="destructive">
            {formatCount(metrics.notRelevantCount, "not relevant")}
          </Badge>
          <Badge variant="muted">
            average rating {formatNullableDecimal(metrics.averageRating)}
          </Badge>
          {persistedSummary?.latest_updated_at ? (
            <Badge variant="muted">
              stored avg {formatNullableDecimal(persistedSummary.average_rating ?? null)}
            </Badge>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function EvaluationReadinessPanel({
  evaluation,
  formatCount,
  formatPercent,
}: {
  evaluation: RetrievalJudgmentEvaluationResult;
  formatCount: (count: number, singular: string, plural?: string) => string;
  formatPercent: (value: number) => string;
}) {
  const readiness = evaluation.evaluation_readiness;
  return (
    <div
      aria-label="Judgment evaluation readiness"
      className={cn(
        "grid gap-2 rounded-md border p-3 text-sm",
        evaluationReadinessClass(readiness.status),
      )}
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 font-black">
          {readiness.status === "ready" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0" />
          ) : (
            <AlertTriangle className="h-4 w-4 shrink-0" />
          )}
          {readiness.label}
          <HelpTooltip label="Judgment readiness help">
            Readiness tells whether enough ranked hits have human labels for Precision@k, MAP@k, MRR@k, and nDCG@k to be useful for tuning.
          </HelpTooltip>
        </div>
        <Badge variant={evaluationReadinessVariant(readiness.status)}>
          {humanize(readiness.status)}
        </Badge>
      </div>
      <p className="break-words leading-6">{readiness.message}</p>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant="muted">
          min {formatCount(readiness.min_judged_count, "judged hit")}
        </Badge>
        <Badge variant="muted">
          min coverage {formatPercent(readiness.min_coverage_at_k)}
        </Badge>
      </div>
    </div>
  );
}

export function JudgmentMetricCard({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "success" | "warning";
  value: string;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2">
      <span className="text-xs font-bold text-muted-foreground">{label}</span>
      <Badge variant={tone}>{value}</Badge>
    </div>
  );
}

function evaluationReadinessVariant(
  status: string,
): "success" | "warning" | "destructive" | "muted" {
  if (status === "ready") return "success";
  if (status === "unlabeled") return "destructive";
  if (status === "low_confidence" || status === "usable_with_gaps") return "warning";
  return "muted";
}

function evaluationReadinessClass(status: string): string {
  if (status === "ready") return "border-emerald-200 bg-emerald-50 text-emerald-950";
  if (status === "unlabeled") return "border-red-200 bg-red-50 text-red-950";
  if (status === "low_confidence" || status === "usable_with_gaps") {
    return "border-amber-200 bg-amber-50 text-amber-950";
  }
  return "border-border bg-card text-card-foreground";
}
