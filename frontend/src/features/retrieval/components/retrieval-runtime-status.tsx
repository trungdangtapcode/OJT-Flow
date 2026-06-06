import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Network,
  RefreshCw,
  Loader2,
} from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { Notice } from "../../../components/ui/notice";
import { cn, humanize } from "../../../lib/utils";
import type {
  RetrievalGraphContext,
  RetrievalIntegrityItem,
  RetrievalIntegrityReport,
} from "../../../types";
import { GraphCounter } from "./graph-counter";
import { IntegrityFact, IntegrityMetric } from "./metric-primitives";
import { TokenList } from "./token-list";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export type RetrievalRuntimeStatusView = {
  graphEdgeCount: number | null;
  graphNodeCount: number | null;
  graphTripleCount: number | null;
  integrityStatus: string;
  rerankerEnabled: boolean;
  retrievalMode: string;
  sourceCoverageLabel: string;
  sourceDiversityEnabled: boolean;
};

export function RetrievalRuntimeStatusStrip({
  view,
}: {
  view: RetrievalRuntimeStatusView;
}) {
  return (
    <div
      aria-label="Retrieval runtime status"
      className="grid gap-2 rounded-md border border-border bg-card/80 p-3 text-xs sm:grid-cols-2 xl:grid-cols-4"
    >
      <RuntimeStatusFact
        label="Retrieval mode"
        supporting={view.sourceDiversityEnabled ? "diverse source selection" : "score order"}
        value={view.retrievalMode}
        variant={view.sourceDiversityEnabled ? "success" : "muted"}
      />
      <RuntimeStatusFact
        label="Reranker"
        supporting={view.rerankerEnabled ? "second-stage ranking active" : "first-stage ranking only"}
        value={view.rerankerEnabled ? "enabled" : "off"}
        variant={view.rerankerEnabled ? "success" : "muted"}
      />
      <RuntimeStatusFact
        label="Graph handoff"
        supporting={graphStatusSupporting(view)}
        value={view.graphNodeCount === null ? "not ready" : `${view.graphNodeCount} nodes`}
        variant={view.graphNodeCount === null ? "muted" : "success"}
      />
      <RuntimeStatusFact
        label="Index integrity"
        supporting={view.sourceCoverageLabel}
        value={humanize(view.integrityStatus)}
        variant={view.integrityStatus === "ok" ? "success" : "warning"}
      />
    </div>
  );
}

export function RuntimeDiversityBadge({
  enabled,
  sourceCoverageLabel,
}: {
  enabled: boolean;
  sourceCoverageLabel: string;
}) {
  if (!enabled) {
    return <Badge variant="muted">score order</Badge>;
  }
  return <Badge variant="success">{sourceCoverageLabel} sources</Badge>;
}

export function RuntimeRerankBadge({ enabled }: { enabled: boolean }) {
  if (!enabled) {
    return <Badge variant="muted">first stage only</Badge>;
  }
  return <Badge variant="success">reranked</Badge>;
}

export function GraphPanel({
  graphContext,
}: {
  graphContext: RetrievalGraphContext | undefined;
}) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5 text-primary" />
          Graph handoff
        </CardTitle>
        <CardDescription>Entity and evidence triples prepared for Graph-NER/RAG.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        {!graphContext ? (
          <Notice title="Graph context unavailable">
            Run a search to inspect graph handoff context.
          </Notice>
        ) : (
          <>
            <div className="grid gap-2 text-sm sm:grid-cols-3">
              <GraphCounter label="Nodes" value={graphContext.nodes.length} />
              <GraphCounter label="Edges" value={graphContext.edges.length} />
              <GraphCounter label="Triples" value={graphContext.triples.length} />
            </div>
            <div className="grid gap-2">
              <div className="text-xs font-bold uppercase text-muted-foreground">
                {graphContext.graph_contract}
              </div>
              {graphContext.triples.slice(0, 8).map((triple, index) => (
                <div
                  className="grid gap-1 rounded-md border border-border bg-muted/20 p-2 text-sm"
                  key={`${triple.subject}-${triple.object}-${index}`}
                >
                  <div className="break-words font-bold">{triple.subject}</div>
                  <div className="break-words text-muted-foreground">
                    {triple.predicate} / {triple.object}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function RuntimeStatusFact({
  label,
  supporting,
  value,
  variant,
}: {
  label: string;
  supporting: string;
  value: string;
  variant: BadgeVariant;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-muted/20 px-3 py-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold uppercase text-muted-foreground">{label}</span>
        <Badge variant={variant}>{value}</Badge>
      </div>
      <span className="break-words text-muted-foreground">{supporting}</span>
    </div>
  );
}

function graphStatusSupporting(view: RetrievalRuntimeStatusView) {
  if (view.graphNodeCount === null) {
    return "run search to prepare graph context";
  }
  return `${view.graphEdgeCount ?? 0} edges / ${view.graphTripleCount ?? 0} triples`;
}

export function IntegrityPanel({
  checks,
  formatCount,
  formatHash,
  includeCorpus,
  integrityBadgeVariant,
  isFetching,
  onRefresh,
  onToggleCorpus,
  report,
}: {
  checks: RetrievalIntegrityItem[];
  formatCount: (count: number, singular: string) => string;
  formatHash: (value: string | null | undefined) => string;
  includeCorpus: boolean;
  integrityBadgeVariant: (status: string) => BadgeVariant;
  isFetching: boolean;
  onRefresh: () => void;
  onToggleCorpus: () => void;
  report: RetrievalIntegrityReport | undefined;
}) {
  const status = report?.status ?? "loading";
  const hasWarnings = Boolean(report?.warnings.length);
  const StatusIcon = status === "ok" ? CheckCircle2 : AlertTriangle;

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70">
        <div className="min-w-0">
          <CardTitle className="flex items-center gap-2">
            <StatusIcon
              className={cn(
                "h-5 w-5",
                status === "ok" ? "text-emerald-700" : "text-amber-700",
              )}
            />
            Index integrity
          </CardTitle>
          <CardDescription>
            {report
              ? `${report.repository} / ${report.checked_scope}`
              : "Checking indexed knowledge consistency"}
          </CardDescription>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Button onClick={onToggleCorpus} size="sm" type="button" variant="outline">
            <Database className="h-4 w-4" />
            {includeCorpus ? "Corpus on" : "Seeded only"}
          </Button>
          <Button disabled={isFetching} onClick={onRefresh} size="sm" type="button" variant="outline">
            {isFetching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4">
        {!report ? (
          <Notice title="Integrity check running">
            The app is checking trusted source hashes against the active index.
          </Notice>
        ) : (
          <>
            <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-6">
              <IntegrityMetric
                label="Status"
                tone={integrityBadgeVariant(report.status)}
                value={humanize(report.status)}
              />
              <IntegrityMetric label="Expected" value={report.expected_source_count} />
              <IntegrityMetric label="Indexed" value={report.indexed_source_count} />
              <IntegrityMetric label="OK" tone="success" value={report.ok_count} />
              <IntegrityMetric label="Stale" tone={report.stale_count ? "warning" : "muted"} value={report.stale_count} />
              <IntegrityMetric label="Missing" tone={report.missing_count ? "destructive" : "muted"} value={report.missing_count} />
            </div>

            {hasWarnings ? (
              <TokenList items={report.warnings} title="Integrity warnings" tone="warning" />
            ) : (
              <TokenList items={[]} title="Integrity warnings" />
            )}

            <div className="grid gap-2">
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <div className="text-xs font-bold uppercase text-muted-foreground">
                  Source checks
                </div>
                <Badge variant={report.extra_count ? "warning" : "muted"}>
                  {formatCount(report.extra_count, "extra source")}
                </Badge>
              </div>
              <div className="grid gap-2">
                {checks.map((check) => (
                  <div
                    className="grid gap-2 rounded-md border border-border bg-muted/20 p-3 text-sm"
                    key={check.source_id}
                  >
                    <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="break-all font-mono text-xs font-bold">
                          {check.source_id}
                        </div>
                        <div className="mt-1 break-words text-xs text-muted-foreground">
                          {check.message}
                        </div>
                      </div>
                      <Badge variant={integrityBadgeVariant(check.status)}>
                        {humanize(check.status)}
                      </Badge>
                    </div>
                    <div className="grid gap-2 text-xs sm:grid-cols-4">
                      <IntegrityFact label="Expected" value={`${check.expected_chunk_count}`} />
                      <IntegrityFact label="Indexed" value={`${check.indexed_chunk_count}`} />
                      <IntegrityFact label="Expected hash" value={formatHash(check.expected_hash)} />
                      <IntegrityFact label="Indexed hash" value={formatHash(check.indexed_hash)} />
                    </div>
                  </div>
                ))}
                {!checks.length ? (
                  <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                    No source checks returned.
                  </div>
                ) : null}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
