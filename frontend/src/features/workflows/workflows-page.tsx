import * as React from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Activity, AlertTriangle, ArrowLeft, BarChart3, CheckCircle2, ChevronRight, Plus, Search } from "lucide-react";

import { StatusBadge } from "../../components/domain/workflow-badges";
import { PageHeader } from "../../components/layout/page-header";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input, Label, Select } from "../../components/ui/form";
import { GuideGrid, GuideItem, GuidePanel } from "../../components/ui/guide-panel";
import { HelpTooltip } from "../../components/ui/help-tooltip";
import { Notice } from "../../components/ui/notice";
import { PaginationFooter } from "../../components/ui/pagination";
import { Skeleton } from "../../components/ui/skeleton";
import { SummaryStrip, SummaryStripItem } from "../../components/ui/summary-strip";
import { useWorkflowStatsQuery, useWorkflowSummariesQuery, workflowErrorMessage } from "../../lib/server-state";
import { cn, formatCompactDate } from "../../lib/utils";
import { useResponsivePageSize } from "../../lib/use-responsive-page-size";
import type { WorkflowSummaryItem } from "../../types";
import { WorkflowDetail } from "./workflow-detail";

export function WorkflowsPage({ workflowId }: { workflowId?: string }) {
  const navigate = useNavigate();
  const [q, setQ] = React.useState("");
  const [status, setStatus] = React.useState<string>("");
  const [page, setPage] = React.useState(1);
  const [sort, setSort] = React.useState("updated_at");
  const [direction, setDirection] = React.useState("desc");
  const pageSize = useResponsivePageSize();
  React.useEffect(() => setPage(1), [pageSize]);

  const statsQuery = useWorkflowStatsQuery();
  const summariesQuery = useWorkflowSummariesQuery({
    q,
    status: status || null,
    page,
    page_size: pageSize,
    sort,
    direction,
  });
  const items = summariesQuery.data?.items ?? [];
  const selectedId = workflowId ?? items[0]?.workflow_id ?? null;

  const stats = statsQuery.data;
  const total = summariesQuery.data?.total ?? 0;
  const currentPage = summariesQuery.data?.page ?? page;
  const isFiltered = Boolean(q.trim() || status);
  const visibleReviewCount = items.filter((item) => item.status === "needs_human_review").length;
  const openWorkflow = (nextWorkflowId: string) =>
    void navigate({
      to: "/workflows/$workflowId",
      params: { workflowId: nextWorkflowId },
    });

  if (workflowId) {
    return (
      <div className="grid gap-5">
        <PageHeader
          action={
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="outline">
                <Link to="/workflows">
                  <ArrowLeft className="h-4 w-4" />
                  Queue
                </Link>
              </Button>
              <Button asChild>
                <Link to="/workbench">
                  <Plus className="h-4 w-4" />
                  New workflow
                </Link>
              </Button>
            </div>
          }
          title="Workflow detail"
          description="Inspect workflow state, validation issues, evidence, review gates, output, and audit history."
        />
        <WorkflowDetail focused workflowId={selectedId} />
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      <PageHeader
        action={
          <div className="flex flex-wrap gap-2">
            <Button asChild>
              <Link to="/workbench">
                <Plus className="h-4 w-4" />
                New workflow
              </Link>
            </Button>
          </div>
        }
        title="Workflow operations"
        description="Command center for governed healthcare data workflows, review gates, evidence, and audit state."
      />
      <GuidePanel title="How to read workflow operations">
        <GuideGrid>
          <GuideItem title="Queue">
            Each row is one persisted run. Select a workflow to inspect parser output, validation issues, evidence, and audit history.
          </GuideItem>
          <GuideItem title="Status">
            Completed means output exists. Needs review means a human must approve, edit, reject, or clarify before completion.
          </GuideItem>
          <GuideItem title="Issues and evidence">
            Issue count shows validation pressure. Evidence count shows how much trusted support was attached to the run.
          </GuideItem>
        </GuideGrid>
      </GuidePanel>
      <OperationsSummary
        queueLoading={summariesQuery.isLoading}
        stats={stats}
        statsLoading={statsQuery.isLoading}
        visibleReviewCount={visibleReviewCount}
      />
      {statsQuery.isError ? (
        <Notice title="Dashboard metrics could not be loaded" tone="danger">
          {workflowErrorMessage(statsQuery.error)}
        </Notice>
      ) : null}
      <div
        className={cn(
          "grid items-start gap-4",
          selectedId
            ? "xl:grid-cols-[minmax(320px,390px)_minmax(0,1fr)] 2xl:grid-cols-[minmax(340px,410px)_minmax(0,1fr)]"
            : "xl:grid-cols-1",
        )}
      >
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border bg-card/70 p-4">
            <div className="grid gap-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <CardTitle>Workflow queue</CardTitle>
                  <p className="mt-1 inline-flex items-center gap-1.5 text-sm text-muted-foreground">
                    Search, filter, and inspect governed runs.
                    <HelpTooltip label="Workflow queue help">
                      Use this queue to find a run, then inspect the selected detail panel for issues, evidence, output, and audit events.
                    </HelpTooltip>
                  </p>
                </div>
                <span className="rounded-full border border-border bg-muted px-2.5 py-1 text-xs font-bold text-muted-foreground">
                  {summariesQuery.isLoading ? "loading queue" : `${total} queued`}
                </span>
              </div>
              <div className="grid min-w-0 gap-2 md:grid-cols-2">
                <div className="relative max-sm:w-full">
                  <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    aria-label="Search workflows"
                    className="w-full pl-8"
                    onChange={(event) => {
                      setPage(1);
                      setQ(event.target.value);
                    }}
                    placeholder="Search queue"
                    value={q}
                  />
                </div>
                <Select
                  aria-label="Workflow status"
                  className="w-full"
                  onChange={(event) => {
                    setPage(1);
                    setStatus(event.target.value);
                  }}
                  value={status}
                >
                  <option value="">All statuses</option>
                  <option value="needs_human_review">Needs review</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                  <option value="running">Running</option>
                </Select>
                <Label className="gap-1 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1.5">
                    Sort
                    <HelpTooltip label="Workflow sort help">
                      Sort by updated time for active work, created time for chronology, issues for risk triage, or evidence for grounding coverage.
                    </HelpTooltip>
                  </span>
                  <Select
                    className="w-full"
                    onChange={(event) => {
                      setPage(1);
                      setSort(event.target.value);
                    }}
                    value={sort}
                  >
                    <option value="updated_at">Updated</option>
                    <option value="created_at">Created</option>
                    <option value="workflow_id">Workflow ID</option>
                    <option value="issue_count">Issues</option>
                    <option value="evidence_count">Evidence</option>
                    <option value="status">Status</option>
                  </Select>
                </Label>
                <Label className="gap-1 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1.5">
                    Direction
                    <HelpTooltip label="Workflow direction help">
                      Desc shows newest or highest values first. Asc shows oldest or lowest values first.
                    </HelpTooltip>
                  </span>
                  <Select
                    className="w-full"
                    onChange={(event) => {
                      setPage(1);
                      setDirection(event.target.value);
                    }}
                    value={direction}
                  >
                    <option value="desc">Desc</option>
                    <option value="asc">Asc</option>
                  </Select>
                </Label>
              </div>
            </div>
          </CardHeader>
          <CardContent className={cn("pt-4", items.length ? "p-2 sm:p-2" : "")}>
            {summariesQuery.isLoading ? (
              <WorkflowQueueSkeleton />
            ) : summariesQuery.isError ? (
              <Notice title="Workflow queue could not be loaded" tone="danger">
                {workflowErrorMessage(summariesQuery.error)}
              </Notice>
            ) : !items.length ? (
              <Notice title={isFiltered ? "No matching workflows" : "No workflows yet"}>
                <div className="grid gap-3">
                  <p>
                    {isFiltered
                      ? "Adjust the search or status filters to widen the queue."
                      : "Start from the workbench to create your first governed healthcare data workflow."}
                  </p>
                  {!isFiltered ? (
                    <div>
                      <Button asChild size="sm">
                        <Link to="/workbench">
                          <Plus className="h-4 w-4" />
                          Start in workbench
                        </Link>
                      </Button>
                    </div>
                  ) : null}
                </div>
              </Notice>
            ) : (
              <>
                <div className="grid auto-rows-max divide-y divide-border">
                  {items.map((item) => (
                    <WorkflowQueueItem
                      active={item.workflow_id === selectedId}
                      item={item}
                      key={item.workflow_id}
                      onClick={() => openWorkflow(item.workflow_id)}
                    />
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
            )}
          </CardContent>
        </Card>
        {selectedId ? (
          <div className="min-w-0 max-xl:hidden xl:sticky xl:top-4">
            <WorkflowDetail workflowId={selectedId} />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function OperationsSummary({
  queueLoading,
  stats,
  statsLoading,
  visibleReviewCount,
}: {
  queueLoading: boolean;
  stats:
    | {
        average_issue_count: number;
        completed: number;
        pending_reviews: number;
        total: number;
      }
    | undefined;
  statsLoading: boolean;
  visibleReviewCount: number;
}) {
  return (
    <SummaryStrip>
      <SummaryStripItem
        icon={Activity}
        label="Workflows"
        loading={statsLoading || queueLoading}
        supporting="Total persisted runs"
        value={formatRunCount(stats?.total ?? 0)}
      />
      <SummaryStripItem
        icon={AlertTriangle}
        label="Pending reviews"
        loading={statsLoading}
        supporting={
          queueLoading
            ? "Loading current queue"
            : `${visibleReviewCount} visible in current queue`
        }
        tone="warning"
        value={stats?.pending_reviews ?? 0}
      />
      <SummaryStripItem
        icon={CheckCircle2}
        label="Completed"
        loading={statsLoading}
        supporting="Finished with stored output"
        tone="success"
        value={stats?.completed ?? 0}
      />
      <SummaryStripItem
        icon={BarChart3}
        label="Average issues"
        loading={statsLoading}
        supporting="Validation load per workflow"
        tone="info"
        value={stats?.average_issue_count ?? 0}
      />
    </SummaryStrip>
  );
}

function formatRunCount(count: number) {
  return `${count} ${count === 1 ? "run" : "runs"}`;
}

function WorkflowQueueSkeleton() {
  return (
    <div aria-label="Loading workflow queue" className="grid gap-2" role="status">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          aria-hidden="true"
          className="grid gap-2 rounded-md border border-border bg-card p-2.5"
          data-testid="workflow-queue-skeleton-row"
          key={index}
        >
          <div className="grid min-w-0 grid-cols-[minmax(0,1fr)_auto] gap-3">
            <div className="grid min-w-0 gap-2">
              <Skeleton className="h-4 w-40 max-w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
            </div>
            <Skeleton className="mt-0.5 h-4 w-4 rounded-full" />
          </div>
          <div className="flex flex-wrap gap-1.5">
            <Skeleton className="h-6 w-32 rounded-full" />
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-24 rounded-full" />
          </div>
          <Skeleton className="h-3 w-32" />
        </div>
      ))}
    </div>
  );
}

function WorkflowQueueItem({
  active,
  item,
  onClick,
}: {
  active: boolean;
  item: WorkflowSummaryItem;
  onClick: () => void;
}) {
  return (
    <button
      className={cn(
        "grid w-full gap-2 rounded-md border border-transparent bg-card p-2.5 text-left transition hover:border-primary/25 hover:bg-slate-50 focus-ring",
        active && "border-primary/35 bg-teal-50/75 shadow-[inset_3px_0_0_#087f7a]",
      )}
      onClick={onClick}
      type="button"
    >
      <div className="grid min-w-0 grid-cols-[minmax(0,1fr)_auto] gap-3">
        <div className="min-w-0">
          <div className="break-all font-mono text-[13px] font-extrabold leading-tight">{item.workflow_id}</div>
          <div className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
            {item.instruction}
          </div>
        </div>
        <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        <StatusBadge className="max-w-full whitespace-normal px-2 py-0.5 text-[11px] leading-tight" status={item.status} />
        <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-bold text-muted-foreground">
          {item.issue_count} issues
        </span>
        <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-bold text-muted-foreground">
          {item.evidence_count} evidence
        </span>
      </div>
      <div className="text-[10px] font-bold uppercase text-muted-foreground">
        Updated {formatCompactDate(item.updated_at)}
      </div>
    </button>
  );
}
