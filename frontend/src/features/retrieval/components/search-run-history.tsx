import type { ReactNode } from "react";
import { GitCompareArrows, History } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { cn, humanize } from "../../../lib/utils";
import type { RetrievalSearchPayload } from "../../../types";
import { CorrectiveActionTypeCountChips } from "./corrective-action-type-count-chips";
import { SearchRunEvidenceSummary } from "./search-run-evidence-summary";
import type { SearchRunSummaryView } from "../model/search-run-presentation";

type SearchRunHistorySummary = SearchRunSummaryView & {
  candidateCount: number;
  conceptGrounding: unknown[];
  coverage: unknown[];
  queryAspects: unknown[];
  queryProfile: {
    label: string;
    retrievalMode: string;
    route: string;
  } | null;
  rulePackCount: number;
  serverSignature: string | null;
  topSourceId: string | null;
};

type SearchRunHistoryRun = {
  payload: RetrievalSearchPayload;
  runId: string;
  submittedAt: string;
  summary: SearchRunHistorySummary;
};

type SearchRunHistoryProps<TRun extends SearchRunHistoryRun> = {
  activeRunId: string | null;
  comparisonBaselineRunId: string | null;
  comparisonNode?: ReactNode;
  isSearchPending: boolean;
  onClear: () => void;
  onRestore: (run: TRun) => void;
  onSetComparisonBaseline: (runId: string | null) => void;
  runs: TRun[];
};

export function SearchRunHistory<TRun extends SearchRunHistoryRun>({
  activeRunId,
  comparisonBaselineRunId,
  comparisonNode,
  isSearchPending,
  onClear,
  onRestore,
  onSetComparisonBaseline,
  runs,
}: SearchRunHistoryProps<TRun>) {
  if (!runs.length) return null;
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3 border-b border-border bg-card/70">
        <div>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            Search runs
          </CardTitle>
          <CardDescription>{formatCount(runs.length, "recent run")}</CardDescription>
        </div>
        <Button
          aria-label="Clear recent search runs"
          disabled={isSearchPending}
          onClick={onClear}
          size="sm"
          type="button"
          variant="ghost"
        >
          Clear
        </Button>
      </CardHeader>
      <CardContent className="grid gap-2 pt-4">
        {runs.map((run) => {
          const active = run.runId === activeRunId;
          const baseline = run.runId === comparisonBaselineRunId;
          const canSetBaseline = !active && !isSearchPending;
          return (
            <div
              className={cn(
                "grid min-w-0 gap-2 rounded-md border px-3 py-2 text-sm transition-colors",
                active
                  ? "border-primary bg-primary/10 text-foreground"
                  : "border-border bg-card hover:bg-muted",
              )}
              key={run.runId}
              title={run.payload.query}
            >
              <button
                aria-label={`Restore search run ${run.payload.query}`}
                aria-pressed={active}
                className="grid w-full min-w-0 gap-2 text-left focus-ring disabled:cursor-not-allowed disabled:opacity-70"
                disabled={isSearchPending}
                onClick={() => onRestore(run)}
                type="button"
              >
                <span className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                  <span className="min-w-0 break-words font-black">
                    {run.payload.query}
                  </span>
                  <span className="flex min-w-0 flex-wrap justify-end gap-1.5">
                    {baseline ? <Badge variant="default">baseline</Badge> : null}
                    <Badge variant={searchRunSummaryVariant(run.summary)}>
                      {run.summary.qualityWarningCount
                        ? formatCount(run.summary.qualityWarningCount, "issue")
                        : "ready"}
                    </Badge>
                  </span>
                </span>
                <span className="flex min-w-0 flex-wrap gap-1.5">
                  <Badge variant="muted">{formatRunTime(run.submittedAt)}</Badge>
                  <Badge variant="muted">top {run.payload.top_k}</Badge>
                  <Badge variant="muted">
                    {formatCount(run.summary.hitCount, "hit")}
                  </Badge>
                  <Badge variant="muted">
                    {formatCount(run.summary.candidateCount, "candidate")}
                  </Badge>
                  <Badge variant="muted">
                    {formatCount(run.summary.rulePackCount, "rule pack")}
                  </Badge>
                  {run.summary.serverSignature ? (
                    <Badge variant="muted">
                      {formatShortSignature(run.summary.serverSignature)}
                    </Badge>
                  ) : null}
                  {run.summary.queryProfile ? (
                    <Badge variant="muted">
                      {humanize(run.summary.queryProfile.route)}
                    </Badge>
                  ) : null}
                  {run.summary.warningCount ? (
                    <Badge variant="warning">
                      {formatCount(run.summary.warningCount, "warning")}
                    </Badge>
                  ) : null}
                  {run.summary.correctiveActionSummary.count ? (
                    <Badge variant="warning">
                      {formatCount(run.summary.correctiveActionSummary.count, "action")}
                    </Badge>
                  ) : null}
                  <CorrectiveActionTypeCountChips
                    counts={run.summary.correctiveActionSummary.actionTypeCounts}
                  />
                </span>
                {run.summary.topSourceId ? (
                  <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
                    Top source: {run.summary.topSourceId}
                  </span>
                ) : null}
                {run.summary.queryProfile ? (
                  <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
                    Profile: {run.summary.queryProfile.label} /{" "}
                    {humanize(run.summary.queryProfile.retrievalMode)}
                  </span>
                ) : null}
                {run.summary.correctiveActionSummary.topActionTitle ? (
                  <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
                    Top action: {run.summary.correctiveActionSummary.topActionTitle}
                    {run.summary.correctiveActionSummary.highestPriority
                      ? ` / P${run.summary.correctiveActionSummary.highestPriority}`
                      : ""}
                  </span>
                ) : null}
                <SearchRunEvidenceSummary run={run} />
              </button>
              <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
                <Button
                  aria-label={
                    baseline
                      ? `Clear comparison baseline ${run.payload.query}`
                      : `Use ${run.payload.query} as comparison baseline`
                  }
                  disabled={!canSetBaseline}
                  onClick={() => onSetComparisonBaseline(baseline ? null : run.runId)}
                  size="sm"
                  type="button"
                  variant={baseline ? "secondary" : "outline"}
                >
                  <GitCompareArrows className="h-4 w-4" />
                  {baseline ? "Baseline" : "Set baseline"}
                </Button>
              </div>
            </div>
          );
        })}
        {comparisonNode ?? null}
      </CardContent>
    </Card>
  );
}

function searchRunSummaryVariant(
  summary: SearchRunHistorySummary,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (summary.qualityWarningCount > 0 || summary.warningCount > 0) return "warning";
  if (summary.hitCount > 0) return "success";
  return "destructive";
}

function formatRunTime(submittedAt: string): string {
  const date = new Date(submittedAt);
  if (Number.isNaN(date.getTime())) return "recent";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatShortSignature(signature: string): string {
  const digest = signature.includes(":") ? signature.split(":").pop() ?? signature : signature;
  return `sig ${digest.slice(0, 10)}`;
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
