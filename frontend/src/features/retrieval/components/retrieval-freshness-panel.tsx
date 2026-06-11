import { DatabaseZap, RefreshCw, ShieldCheck } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Notice } from "../../../components/ui/notice";
import { cn } from "../../../lib/utils";
import type { RetrievalFreshnessReport, RetrievalFreshnessSource } from "../../../types";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export function RetrievalFreshnessPanel({
  errorMessage,
  isFetching,
  onRefresh,
  report,
}: {
  errorMessage: string | null;
  isFetching: boolean;
  onRefresh: () => void;
  report: RetrievalFreshnessReport | null;
}) {
  const riskySources = (report?.sources ?? [])
    .filter((source) => source.status !== "ready")
    .slice(0, 5);
  const statusView = freshnessStatusView(report?.status ?? "watch");

  return (
    <section className="grid gap-3 rounded-md border border-border bg-card p-4">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="inline-flex min-w-0 items-center gap-2">
            <ShieldCheck className="h-4 w-4 shrink-0 text-primary" />
            <h2 className="break-words text-sm font-black">Source freshness gate</h2>
          </div>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Check source lifecycle, reviewer state, indexing, policies, and refresh cadence.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Badge variant={statusView.variant}>{statusView.label}</Badge>
          <Button
            aria-label="Refresh source freshness"
            disabled={isFetching}
            onClick={onRefresh}
            size="icon"
            type="button"
            variant="outline"
          >
            <RefreshCw className={cn("h-4 w-4", isFetching && "animate-spin")} />
          </Button>
        </div>
      </div>

      {errorMessage ? (
        <Notice title="Source freshness could not be loaded" tone="danger">
          {errorMessage}
        </Notice>
      ) : null}

      <div className="grid gap-2 sm:grid-cols-4">
        <FreshnessMetric label="Score" value={report ? `${report.score}/100` : "loading"} />
        <FreshnessMetric label="Sources" value={String(report?.source_count ?? 0)} />
        <FreshnessMetric label="Needs review" value={String(report?.needs_review_count ?? 0)} />
        <FreshnessMetric label="Unindexed" value={String(report?.unindexed_count ?? 0)} />
      </div>

      {report?.warnings.length ? (
        <div className="grid gap-2">
          {report.warnings.slice(0, 3).map((warning) => (
            <div
              className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-900"
              key={warning}
            >
              {warning}
            </div>
          ))}
        </div>
      ) : null}

      {riskySources.length ? (
        <div className="grid gap-2">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            <DatabaseZap className="h-3.5 w-3.5" />
            Highest-risk sources
          </div>
          {riskySources.map((source) => (
            <FreshnessSourceRow key={source.source_id} source={source} />
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-border bg-muted/30 p-3 text-sm text-muted-foreground">
          All configured retrieval sources are inside the current readiness gate.
        </div>
      )}

      {report ? (
        <div className="flex min-w-0 flex-wrap gap-1.5 text-xs text-muted-foreground">
          <Badge variant="muted">{report.adapter_catalog_version}</Badge>
          <Badge variant="muted">{report.policy_catalog_version}</Badge>
          <Badge variant="muted">{new Date(report.generated_at).toLocaleString()}</Badge>
        </div>
      ) : null}
    </section>
  );
}

function FreshnessMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md border border-border bg-card/80 px-3 py-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 break-words text-sm font-black tabular-nums">{value}</div>
    </div>
  );
}

function FreshnessSourceRow({ source }: { source: RetrievalFreshnessSource }) {
  const statusView = freshnessStatusView(source.status);
  const primaryAction = source.recommended_actions[0] ?? "Review source governance metadata.";
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="break-words text-sm font-bold">{source.title}</div>
          <div className="mt-1 break-words text-xs text-muted-foreground">
            {source.source_id}
          </div>
        </div>
        <Badge variant={statusView.variant}>{statusView.label}</Badge>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {source.standard_system ? <Badge variant="muted">{source.standard_system}</Badge> : null}
        {source.refresh_cadence ? <Badge variant="muted">{source.refresh_cadence}</Badge> : null}
        <Badge variant="muted">{source.indexed_chunk_count} chunks</Badge>
        {source.age_days !== null && source.age_days !== undefined ? (
          <Badge variant={source.age_days > (source.freshness_window_days ?? 999999) ? "warning" : "muted"}>
            {source.age_days}d old
          </Badge>
        ) : null}
      </div>
      {source.issues.length ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {source.issues.slice(0, 4).map((issue) => (
            <Badge key={issue} variant={source.status === "blocked" ? "destructive" : "warning"}>
              {issue}
            </Badge>
          ))}
        </div>
      ) : null}
      <div className="text-xs leading-5 text-muted-foreground">{primaryAction}</div>
    </div>
  );
}

function freshnessStatusView(status: string): { label: string; variant: BadgeVariant } {
  if (status === "ready") return { label: "ready", variant: "success" };
  if (status === "blocked") return { label: "blocked", variant: "destructive" };
  if (status === "needs_review") return { label: "needs review", variant: "warning" };
  return { label: "watch", variant: "muted" };
}
