import * as React from "react";
import { Link } from "@tanstack/react-router";
import { Activity, AlertTriangle, Fingerprint, History, Plus, Search, ShieldCheck } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { StatusBadge } from "../../components/domain/workflow-badges";
import { PageHeader } from "../../components/layout/page-header";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/form";
import { Notice } from "../../components/ui/notice";
import { PaginationFooter } from "../../components/ui/pagination";
import { Skeleton } from "../../components/ui/skeleton";
import { SummaryStrip, SummaryStripItem } from "../../components/ui/summary-strip";
import { useWorkflowEventsQuery, useWorkflowSummariesQuery, workflowErrorMessage } from "../../lib/server-state";
import { cn, formatCompactDate, formatDate, humanize } from "../../lib/utils";
import { useResponsivePageSize } from "../../lib/use-responsive-page-size";
import type { WorkflowEvent, WorkflowSummaryItem } from "../../types";

export function AuditPage() {
  const [q, setQ] = React.useState("");
  const [page, setPage] = React.useState(1);
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const pageSize = useResponsivePageSize({ narrow: 8, wide: 12 });
  const summaries = useWorkflowSummariesQuery({
    q,
    page,
    page_size: pageSize,
    sort: "updated_at",
    direction: "desc",
  });
  const items = summaries.data?.items ?? [];
  const total = summaries.data?.total ?? 0;
  const currentPage = summaries.data?.page ?? page;
  const isFiltered = Boolean(q.trim());
  const selectedWorkflow = items.find((item) => item.workflow_id === selectedId) ?? null;
  const events = useWorkflowEventsQuery(selectedId);
  const eventItems = events.data ?? [];
  const visibleIssueCount = items.reduce((count, item) => count + item.issue_count, 0);
  const visibleEvidenceCount = items.reduce((count, item) => count + item.evidence_count, 0);

  React.useEffect(() => setPage(1), [pageSize, q]);

  React.useEffect(() => {
    if (!items.length) {
      setSelectedId(null);
      return;
    }
    if (!selectedId || !items.some((item) => item.workflow_id === selectedId)) {
      setSelectedId(items[0].workflow_id);
    }
  }, [items, selectedId]);

  return (
    <div className="grid min-w-0 max-w-full gap-6">
      <PageHeader title="Audit" description="Workflow events and decisions." />
      <AuditSummaryStrip
        eventCount={eventItems.length}
        eventsLoading={events.isLoading}
        total={total}
        trailsLoading={summaries.isLoading}
        visibleEvidenceCount={visibleEvidenceCount}
        visibleIssueCount={visibleIssueCount}
        visibleTrailCount={items.length}
      />
      <div className="grid min-w-0 max-w-full items-start gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border/60 bg-muted/30 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5 text-primary" />
                  Audit trails
                </CardTitle>
                <CardDescription>Find persisted workflow trails by ID, instruction, status, or schema.</CardDescription>
              </div>
              <Badge variant="muted">
                {summaries.isLoading ? "loading trails" : formatTrailCount(total)}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="grid min-w-0 gap-3 pt-4">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                aria-label="Search audit workflows"
                className="pl-8"
                placeholder="Search workflows"
                value={q}
                onChange={(event) => setQ(event.target.value)}
              />
            </div>
            {summaries.isLoading ? <AuditTrailSkeleton /> : null}
            {summaries.isError ? (
              <Notice title="Audit search could not be loaded" tone="danger">
                {workflowErrorMessage(summaries.error)}
              </Notice>
            ) : null}
            {!summaries.isLoading && !summaries.isError && !items.length ? (
              <Notice title={isFiltered ? "No matching audit trails" : "No audit trails yet"}>
                <div className="grid gap-3">
                  <p>
                    {isFiltered
                      ? "Adjust the search to inspect more workflow trails."
                      : "Audit packets are created automatically when you run a governed workflow."}
                  </p>
                  {!isFiltered ? (
                    <div>
                      <Button asChild size="sm">
                        <Link to="/workbench">
                          <Plus className="h-4 w-4" />
                          Create workflow
                        </Link>
                      </Button>
                    </div>
                  ) : null}
                </div>
              </Notice>
            ) : null}
            {!summaries.isLoading && !summaries.isError && items.length > 0
              ? (
                <>
                  <div className="grid gap-1">
                    {items.map((item) => (
                      <button
                        className={cn(
                          "min-w-0 rounded-lg border border-transparent bg-card p-3 text-left transition-all duration-150 list-item-hover focus-ring",
                          item.workflow_id === selectedId && "list-item-active",
                        )}
                        key={item.workflow_id}
                        onClick={() => setSelectedId(item.workflow_id)}
                        type="button"
                      >
                        <div className="grid min-w-0 gap-2 sm:flex sm:items-start sm:justify-between sm:gap-3">
                          <div className="min-w-0">
                            <div className="break-all font-bold">{item.workflow_id}</div>
                            <div className="mt-1.5 line-clamp-2 text-xs leading-5 text-muted-foreground">{item.instruction}</div>
                          </div>
                          <StatusBadge className="shrink-0 whitespace-nowrap px-2 text-[11px]" status={item.status} />
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2 text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                          <span>{item.issue_count} issues</span>
                          <span>{item.evidence_count} evidence</span>
                          <span>{formatCompactDate(item.updated_at)}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                  <PaginationFooter
                    onNext={() => setPage((value) => value + 1)}
                    onPrevious={() => setPage((value) => value - 1)}
                    page={currentPage}
                    pageSize={pageSize}
                    total={total}
                  />
                </>
              )
              : null}
          </CardContent>
        </Card>
        <div className="grid min-w-0 gap-5">
          <AuditPacket workflow={selectedWorkflow} events={eventItems} loading={events.isLoading} />
          <Card className="min-w-0 overflow-hidden">
            <CardHeader className="border-b border-border/60 bg-muted/30">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <History className="h-5 w-5 text-primary" />
                    Event timeline
                  </CardTitle>
                  <CardDescription>Append-only events with actor, severity, refs, and summary.</CardDescription>
                </div>
                <Badge variant="muted">{formatEventCount(eventItems.length)}</Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              {!selectedId ? (
                <Notice title="No workflow selected">
                  Select a workflow to inspect its append-only audit events.
                </Notice>
              ) : events.isLoading ? (
                <AuditEventTimelineSkeleton />
              ) : events.isError ? (
                <Notice title="Event timeline could not be loaded" tone="danger">
                  {workflowErrorMessage(events.error)}
                </Notice>
              ) : !eventItems.length ? (
                <Notice title="No audit events recorded">
                  This workflow has no persisted audit events yet.
                </Notice>
              ) : (
                <ol className="relative grid gap-4 before:absolute before:left-[5px] before:top-2 before:h-[calc(100%-1rem)] before:w-0.5 before:rounded-full before:bg-border">
                  {eventItems.map((event) => (
                    <AuditEventItem event={event} key={event.event_id} />
                  ))}
                </ol>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function AuditSummaryStrip({
  eventCount,
  eventsLoading,
  total,
  trailsLoading,
  visibleEvidenceCount,
  visibleIssueCount,
  visibleTrailCount,
}: {
  eventCount: number;
  eventsLoading: boolean;
  total: number;
  trailsLoading: boolean;
  visibleEvidenceCount: number;
  visibleIssueCount: number;
  visibleTrailCount: number;
}) {
  return (
    <SummaryStrip>
      <SummaryStripItem
        icon={Activity}
        label="Audit trails"
        loading={trailsLoading}
        supporting={
          trailsLoading
            ? "Loading persisted trails"
            : `${visibleTrailCount} visible on this page`
        }
        value={formatTrailCount(total)}
      />
      <SummaryStripItem
        icon={AlertTriangle}
        label="Issue load"
        loading={trailsLoading}
        supporting="Visible trail total"
        tone="warning"
        value={visibleIssueCount}
      />
      <SummaryStripItem
        icon={ShieldCheck}
        label="Evidence refs"
        loading={trailsLoading}
        supporting="Visible trail total"
        tone="info"
        value={visibleEvidenceCount}
      />
      <SummaryStripItem
        icon={History}
        label="Selected events"
        loading={eventsLoading}
        supporting="Append-only timeline"
        tone="neutral"
        value={eventCount}
      />
    </SummaryStrip>
  );
}

function AuditTrailSkeleton() {
  return (
    <div aria-label="Loading audit trails" className="grid gap-1" role="status">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          aria-hidden="true"
          className="grid gap-2 rounded-lg border border-border/60 bg-card p-3"
          data-testid="audit-trail-skeleton-row"
          key={index}
        >
          <div className="grid min-w-0 gap-2 sm:flex sm:items-start sm:justify-between sm:gap-3">
            <div className="grid min-w-0 flex-1 gap-2">
              <Skeleton className="h-5 w-44 max-w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
            <Skeleton className="h-6 w-28 rounded-full" />
          </div>
          <div className="flex flex-wrap gap-2">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

function AuditEventTimelineSkeleton() {
  return (
    <ol
      aria-label="Loading audit event timeline"
      className="relative grid gap-4 before:absolute before:left-[5px] before:top-2 before:h-[calc(100%-1rem)] before:w-0.5 before:rounded-full before:bg-border"
      role="status"
    >
      {Array.from({ length: 5 }).map((_, index) => (
        <li
          aria-hidden="true"
          className="relative grid gap-2 pl-6"
          data-testid="audit-event-skeleton-row"
          key={index}
        >
          <Skeleton className="absolute left-0 top-1.5 h-3 w-3 rounded-full" />
          <div className="grid gap-2 rounded-lg border border-border/60 bg-card p-3">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="grid min-w-0 flex-1 gap-2">
                <Skeleton className="h-5 w-44 max-w-full" />
                <Skeleton className="h-4 w-full" />
              </div>
              <Skeleton className="h-6 w-20 rounded-full" />
            </div>
            <div className="flex flex-wrap gap-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-4 w-20" />
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}

function AuditPacket({
  events,
  loading,
  workflow,
}: {
  events: WorkflowEvent[];
  loading: boolean;
  workflow: WorkflowSummaryItem | null;
}) {
  const actorCount = new Set(events.map((event) => `${event.actor_type}:${event.actor_id}`)).size;
  const lastEvent = events.at(-1);
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border/60 bg-muted/30 p-4">
        <CardTitle className="flex items-center gap-2">
          <Fingerprint className="h-5 w-5 text-primary" />
          Audit packet
        </CardTitle>
        <CardDescription>Selected workflow context before inspecting event-level details.</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        {!workflow ? (
          <Notice title="No audit packet selected">
            Select a workflow trail to inspect its audit packet.
          </Notice>
        ) : (
          <div className="grid gap-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="break-all font-mono text-lg font-black leading-tight">{workflow.workflow_id}</div>
                <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-muted-foreground">{workflow.instruction}</p>
              </div>
              <StatusBadge className="shrink-0 whitespace-nowrap px-2 text-[11px]" status={workflow.status} />
            </div>
            <div className="grid divide-y divide-border/60 rounded-lg border border-border/60">
              <AuditFact label="Issues" value={workflow.issue_count} />
              <AuditFact label="Evidence" value={workflow.evidence_count} />
              <AuditFact label="Actors" value={loading ? "..." : actorCount} />
              <AuditFact label="Events" value={loading ? "..." : events.length} />
              <AuditFact label="Latest" value={loading ? "..." : lastEvent ? humanize(lastEvent.event_type) : "none"} />
              <AuditFact label="Updated" value={formatCompactDate(workflow.updated_at)} />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function formatTrailCount(count: number) {
  return `${count} ${count === 1 ? "trail" : "trails"}`;
}

function formatEventCount(count: number) {
  return `${count} ${count === 1 ? "event" : "events"}`;
}

function AuditFact({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="grid gap-1 px-3 py-2.5 sm:grid-cols-[8rem_minmax(0,1fr)]">
      <div className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="min-w-0 break-words text-sm font-semibold">{value}</div>
    </div>
  );
}

function AuditEventItem({ event }: { event: WorkflowEvent }) {
  const refCount = event.input_refs.length + event.output_refs.length;
  const dotColor =
    event.severity === "error" || event.severity === "critical"
      ? "bg-destructive"
      : event.severity === "warning"
        ? "bg-amber-500"
        : "bg-primary";
  return (
    <li className="relative grid grid-cols-[12px_minmax(0,1fr)] gap-3">
      <span className={cn("mt-4 h-3 w-3 rounded-full ring-4 ring-card", dotColor)} />
      <div className="min-w-0 rounded-lg border border-border/60 bg-card p-3.5 transition-colors hover:bg-muted/20">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="break-words font-bold">{event.event_type}</div>
            <div className="mt-1 text-[11px] text-muted-foreground sm:text-xs">
              {formatDate(event.timestamp)} / {event.actor_type}:{event.actor_id}
            </div>
          </div>
          <Badge variant={event.severity === "error" ? "destructive" : event.severity === "warning" ? "warning" : "muted"}>
            {event.severity}
          </Badge>
        </div>
        <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">{event.summary}</p>
        <div className="mt-3 hidden flex-wrap gap-2 text-xs font-semibold text-muted-foreground sm:flex">
          <span className="rounded-full bg-muted px-2 py-1">{refCount} refs</span>
          <span className="rounded-full bg-muted px-2 py-1">{Object.keys(event.metadata ?? {}).length} metadata keys</span>
          <span className="rounded-full bg-muted px-2 py-1">id {event.event_id.slice(0, 10)}</span>
        </div>
      </div>
    </li>
  );
}
