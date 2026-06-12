import { Activity, AlertTriangle, BarChart3, CheckCircle2, Inbox, RefreshCw } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Notice } from "../../../components/ui/notice";
import { cn } from "../../../lib/utils";
import type {
  RetrievalActiveLearningCandidate,
  RetrievalActiveLearningStatus,
  RetrievalActiveLearningSummary,
  RetrievalJudgmentEvaluationResult,
  RetrievalRelevanceJudgment,
  RetrievalRelevanceJudgmentSummary,
} from "../../../types";
import { isNonPositiveJudgment } from "../model/retrieval-judgment-labels";
import type { RetrievalSearchRun } from "../model/retrieval-run-summary";

type FormatCount = (count: number, singular: string, plural?: string) => string;
type FormatNullableNumber = (value: number | null) => string;
type FormatPercent = (value: number) => string;

type QueryRegressionRow = {
  query: string;
  total: number;
  relevant: number;
  partial: number;
  notRelevant: number;
  positiveRatio: number;
  sourceCount: number;
  latestUpdatedAt: string | null;
};

export function RetrievalRegressionDashboard({
  activeEvaluation,
  activeLearningCandidates,
  activeLearningSummary,
  activeRun,
  errorMessage,
  formatCount,
  formatNullableDecimal,
  formatNullablePercent,
  formatPercent,
  globalJudgments,
  globalSummary,
  isLoading,
  isRefreshing,
  onRefresh,
  onUpdateActiveLearningCandidate,
  searchRuns,
}: {
  activeEvaluation: RetrievalJudgmentEvaluationResult | null;
  activeLearningCandidates: RetrievalActiveLearningCandidate[];
  activeLearningSummary: RetrievalActiveLearningSummary | null;
  activeRun: RetrievalSearchRun | null;
  errorMessage: string | null;
  formatCount: FormatCount;
  formatNullableDecimal: FormatNullableNumber;
  formatNullablePercent: FormatNullableNumber;
  formatPercent: FormatPercent;
  globalJudgments: RetrievalRelevanceJudgment[];
  globalSummary: RetrievalRelevanceJudgmentSummary | null;
  isLoading: boolean;
  isRefreshing: boolean;
  onRefresh: () => void;
  onUpdateActiveLearningCandidate: (
    candidateId: string,
    status: RetrievalActiveLearningStatus,
  ) => void;
  searchRuns: RetrievalSearchRun[];
}) {
  const queryRows = regressionRows(globalJudgments).slice(0, 5);
  const status = regressionStatus(globalSummary, activeEvaluation);
  const latestRun = searchRuns[0] ?? null;

  return (
    <section className="grid gap-3 rounded-md border border-border bg-card p-4">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="inline-flex min-w-0 items-center gap-2">
            <BarChart3 className="h-4 w-4 shrink-0 text-primary" />
            <h2 className="break-words text-sm font-black">Regression dashboard</h2>
          </div>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Track relevance labels and active-run quality before tuning retrieval.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Badge variant={status.variant}>{status.label}</Badge>
          <Button
            aria-label="Refresh regression dashboard"
            disabled={isRefreshing}
            onClick={onRefresh}
            size="icon"
            type="button"
            variant="outline"
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
          </Button>
        </div>
      </div>

      {errorMessage ? (
        <Notice title="Regression metrics could not be loaded" tone="danger">
          {errorMessage}
        </Notice>
      ) : null}

      <div className="grid gap-2 sm:grid-cols-2">
        <RegressionMetric
          label="Judgments"
          value={
            isLoading && !globalSummary
              ? "loading"
              : formatCount(globalSummary?.total_count ?? 0, "label")
          }
        />
        <RegressionMetric
          label="Queries"
          value={formatCount(globalSummary?.query_count ?? 0, "query", "queries")}
        />
        <RegressionMetric
          label="Sources"
          value={formatCount(globalSummary?.source_count ?? 0, "source")}
        />
        <RegressionMetric
          label="Avg rating"
          value={formatNullableDecimal(globalSummary?.average_rating ?? null)}
        />
      </div>

      {activeEvaluation ? (
        <ActiveRunRegression
          activeEvaluation={activeEvaluation}
          activeRunQuery={activeRun?.payload.query ?? null}
          formatCount={formatCount}
          formatNullableDecimal={formatNullableDecimal}
          formatNullablePercent={formatNullablePercent}
          formatPercent={formatPercent}
        />
      ) : (
        <div className="rounded-md border border-border bg-muted/30 p-3 text-sm text-muted-foreground">
          Run a retrieval search and label evidence to see Precision@k, MRR, MAP, and nDCG.
        </div>
      )}

      <div className="grid gap-2">
        <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            <Activity className="h-3.5 w-3.5" />
            Recent labeled queries
          </div>
          {latestRun ? (
            <Badge variant="muted">
              latest run {new Date(latestRun.submittedAt).toLocaleString()}
            </Badge>
          ) : null}
        </div>
        {queryRows.length ? (
          <div className="grid gap-2">
            {queryRows.map((row) => (
              <QueryRegressionRowView
                formatCount={formatCount}
                formatPercent={formatPercent}
                key={row.query}
                row={row}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-md border border-dashed border-border p-3 text-sm text-muted-foreground">
            No persisted relevance labels yet.
          </div>
        )}
      </div>

      <ActiveLearningQueue
        candidates={activeLearningCandidates}
        onUpdateCandidate={onUpdateActiveLearningCandidate}
        summary={activeLearningSummary}
      />
    </section>
  );
}

function ActiveLearningQueue({
  candidates,
  onUpdateCandidate,
  summary,
}: {
  candidates: RetrievalActiveLearningCandidate[];
  onUpdateCandidate: (candidateId: string, status: RetrievalActiveLearningStatus) => void;
  summary: RetrievalActiveLearningSummary | null;
}) {
  return (
    <div className="grid gap-2 border-t border-border pt-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
          <Inbox className="h-3.5 w-3.5" />
          Active-learning queue
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="muted">{summary?.open_count ?? 0} open</Badge>
          <Badge variant={summary?.critical_count ? "destructive" : "muted"}>
            {summary?.critical_count ?? 0} critical
          </Badge>
          <Badge variant={summary?.high_count ? "warning" : "muted"}>
            {summary?.high_count ?? 0} high
          </Badge>
        </div>
      </div>

      {candidates.length ? (
        <div className="grid gap-2">
          {candidates.map((candidate) => (
            <ActiveLearningCandidateRow
              candidate={candidate}
              key={candidate.candidate_id}
              onUpdateCandidate={onUpdateCandidate}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-dashed border-border p-3 text-sm text-muted-foreground">
          No open active-learning candidates.
        </div>
      )}
    </div>
  );
}

function ActiveLearningCandidateRow({
  candidate,
  onUpdateCandidate,
}: {
  candidate: RetrievalActiveLearningCandidate;
  onUpdateCandidate: (candidateId: string, status: RetrievalActiveLearningStatus) => void;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-background p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex min-w-0 flex-wrap items-center gap-1.5">
            <Badge variant={priorityVariant(candidate.priority)}>{candidate.priority}</Badge>
            <Badge variant="muted">{humanizeLabel(candidate.source_kind)}</Badge>
            {candidate.support_status ? (
              <Badge variant="muted">{candidate.support_status}</Badge>
            ) : null}
          </div>
          <p className="mt-2 line-clamp-2 break-words text-sm font-semibold">
            {candidate.query}
          </p>
          <p className="mt-1 line-clamp-2 break-words text-xs leading-5 text-muted-foreground">
            {candidate.trigger_reason}
          </p>
        </div>
        <div className="flex shrink-0 gap-1.5">
          <Button
            onClick={() => onUpdateCandidate(candidate.candidate_id, "accepted")}
            size="sm"
            type="button"
            variant="outline"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            Accept
          </Button>
          <Button
            onClick={() => onUpdateCandidate(candidate.candidate_id, "archived")}
            size="sm"
            type="button"
            variant="ghost"
          >
            Archive
          </Button>
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5 text-xs text-muted-foreground">
        {candidate.evidence_id ? <span>evidence {candidate.evidence_id}</span> : null}
        {candidate.source_id ? <span>source {candidate.source_id}</span> : null}
        {candidate.updated_at ? (
          <span>updated {new Date(candidate.updated_at).toLocaleString()}</span>
        ) : null}
      </div>
    </div>
  );
}

function ActiveRunRegression({
  activeEvaluation,
  activeRunQuery,
  formatCount,
  formatNullableDecimal,
  formatNullablePercent,
  formatPercent,
}: {
  activeEvaluation: RetrievalJudgmentEvaluationResult;
  activeRunQuery: string | null;
  formatCount: FormatCount;
  formatNullableDecimal: FormatNullableNumber;
  formatNullablePercent: FormatNullableNumber;
  formatPercent: FormatPercent;
}) {
  const readiness = activeEvaluation.evaluation_readiness;
  const ready = readiness.status === "ready";
  return (
    <div className="grid gap-3 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-sm font-black">Active-run evaluation</div>
          <div className="mt-1 line-clamp-2 break-words text-xs text-muted-foreground">
            {activeRunQuery ?? activeEvaluation.query}
          </div>
        </div>
        <Badge variant={ready ? "success" : "warning"}>{readiness.label}</Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        <RegressionMetric label="Coverage@k" value={formatPercent(activeEvaluation.coverage_at_k)} />
        <RegressionMetric label="Precision@k" value={formatPercent(activeEvaluation.precision_at_k)} />
        <RegressionMetric label="MRR@k" value={formatNullableDecimal(activeEvaluation.mrr_at_k)} />
        <RegressionMetric label="MAP@k" value={formatNullableDecimal(activeEvaluation.average_precision_at_k)} />
        <RegressionMetric label="nDCG@k" value={formatNullableDecimal(activeEvaluation.ndcg_at_k ?? null)} />
        <RegressionMetric
          label="Unjudged"
          value={formatCount(activeEvaluation.unjudged_count, "hit")}
        />
      </div>
      <div className="flex items-start gap-2 rounded-md border border-border bg-card p-2 text-xs leading-5 text-muted-foreground">
        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-700" />
        <span>
          {readiness.message} Minimum coverage is{" "}
          {formatNullablePercent(readiness.min_coverage_at_k)} with{" "}
          {formatCount(readiness.min_judged_count, "judged hit")}.
        </span>
      </div>
    </div>
  );
}

function QueryRegressionRowView({
  formatCount,
  formatPercent,
  row,
}: {
  formatCount: FormatCount;
  formatPercent: FormatPercent;
  row: QueryRegressionRow;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="line-clamp-2 break-words text-sm font-bold">{row.query}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant="muted">{formatCount(row.total, "label")}</Badge>
        <Badge variant={row.positiveRatio >= 0.5 ? "success" : "warning"}>
          positive {formatPercent(row.positiveRatio)}
        </Badge>
        <Badge variant="muted">{formatCount(row.sourceCount, "source")}</Badge>
        {row.latestUpdatedAt ? (
          <Badge variant="muted">{new Date(row.latestUpdatedAt).toLocaleDateString()}</Badge>
        ) : null}
      </div>
    </div>
  );
}

function RegressionMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md border border-border bg-card/80 px-3 py-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 break-words text-sm font-black tabular-nums">{value}</div>
    </div>
  );
}

function regressionRows(judgments: RetrievalRelevanceJudgment[]): QueryRegressionRow[] {
  const rows = new Map<string, QueryRegressionRow>();
  for (const judgment of judgments) {
    const row =
      rows.get(judgment.query) ??
      {
        latestUpdatedAt: null,
        notRelevant: 0,
        partial: 0,
        positiveRatio: 0,
        query: judgment.query,
        relevant: 0,
        sourceCount: 0,
        total: 0,
      };
    row.total += 1;
    if (judgment.value === "relevant") row.relevant += 1;
    if (judgment.value === "partial") row.partial += 1;
    if (isNonPositiveJudgment(judgment.value)) row.notRelevant += 1;
    if (!row.latestUpdatedAt || judgment.updated_at > row.latestUpdatedAt) {
      row.latestUpdatedAt = judgment.updated_at;
    }
    rows.set(judgment.query, row);
  }

  const sourceCounts = new Map<string, Set<string>>();
  for (const judgment of judgments) {
    if (!judgment.source_id) continue;
    const sources = sourceCounts.get(judgment.query) ?? new Set<string>();
    sources.add(judgment.source_id);
    sourceCounts.set(judgment.query, sources);
  }

  return Array.from(rows.values())
    .map((row) => ({
      ...row,
      positiveRatio: row.total ? (row.relevant + row.partial) / row.total : 0,
      sourceCount: sourceCounts.get(row.query)?.size ?? 0,
    }))
    .sort((left, right) => (right.latestUpdatedAt ?? "").localeCompare(left.latestUpdatedAt ?? ""));
}

function humanizeLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function priorityVariant(
  priority: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (priority === "critical") return "destructive";
  if (priority === "high") return "warning";
  return "muted";
}

function regressionStatus(
  summary: RetrievalRelevanceJudgmentSummary | null,
  evaluation: RetrievalJudgmentEvaluationResult | null,
): { label: string; variant: "success" | "warning" | "destructive" | "muted" } {
  if (!summary || summary.total_count === 0) {
    return { label: "unlabeled", variant: "destructive" };
  }
  if (evaluation?.evaluation_readiness.status === "ready") {
    return { label: "ready", variant: "success" };
  }
  if ((summary.average_rating ?? 0) < 2) {
    return { label: "attention", variant: "warning" };
  }
  return { label: "labels available", variant: "muted" };
}
