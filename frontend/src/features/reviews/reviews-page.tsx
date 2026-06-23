import * as React from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { AlertTriangle, ChevronRight, ClipboardCheck, FileSearch, Plus, Scale, Search } from "lucide-react";

import { PageHeader } from "../../components/layout/page-header";
import { StatusBadge } from "../../components/domain/workflow-badges";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input, Select } from "../../components/ui/form";
import { Notice } from "../../components/ui/notice";
import { PaginationFooter } from "../../components/ui/pagination";
import { Skeleton } from "../../components/ui/skeleton";
import { SummaryStrip, SummaryStripItem } from "../../components/ui/summary-strip";
import { Table, TBody, TD, TH, THead, TR } from "../../components/ui/table";
import { useReviewSummariesQuery, workflowErrorMessage } from "../../lib/server-state";
import { cn, formatCompactDate } from "../../lib/utils";
import { useResponsivePageSize } from "../../lib/use-responsive-page-size";

export function ReviewsPage() {
  const navigate = useNavigate();
  const [status, setStatus] = React.useState("pending");
  const [q, setQ] = React.useState("");
  const [page, setPage] = React.useState(1);
  const [sort, setSort] = React.useState("updated_at");
  const [direction, setDirection] = React.useState("desc");
  const pageSize = useResponsivePageSize();
  React.useEffect(() => setPage(1), [pageSize]);

  const reviewsQuery = useReviewSummariesQuery({
    status,
    q,
    page,
    page_size: pageSize,
    sort,
    direction,
  });
  const items = reviewsQuery.data?.items ?? [];
  const total = reviewsQuery.data?.total ?? 0;
  const currentPage = reviewsQuery.data?.page ?? page;
  const pendingVisible = items.filter((item) => item.review_status === "pending").length;
  const visibleIssueCount = items.reduce((count, item) => count + item.issue_count, 0);
  const visibleEvidenceCount = items.reduce((count, item) => count + item.evidence_count, 0);
  const maxIssueCount = items.reduce((max, item) => Math.max(max, item.issue_count), 0);
  const isFiltered = Boolean(q.trim() || status !== "pending");

  return (
    <div className="grid gap-6">
      <PageHeader title="Review queue" description="Approve or reject pending workflows." />
      <ReviewSummaryStrip
        loading={reviewsQuery.isLoading}
        maxIssueCount={maxIssueCount}
        pendingVisible={pendingVisible}
        total={total}
        visibleEvidenceCount={visibleEvidenceCount}
        visibleIssueCount={visibleIssueCount}
      />
      <Card className="overflow-hidden">
        <CardHeader className="border-b border-border/40 bg-muted/20 p-4">
          <div className="grid gap-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2">
                <ClipboardCheck className="h-5 w-5 text-primary" />
                Pending decisions
              </CardTitle>
              <span className="rounded-full border border-border/50 bg-muted/40 px-2.5 py-1 text-xs font-medium text-muted-foreground">
                {reviewsQuery.isLoading ? "loading" : formatReviewCount(total)}
              </span>
            </div>
            <div className="flex flex-wrap items-end gap-2">
              <div className="relative min-w-0 flex-1 max-sm:w-full">
                <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  aria-label="Search reviews"
                  className="w-full pl-8"
                  onChange={(event) => {
                    setPage(1);
                    setQ(event.target.value);
                  }}
                  placeholder="Search review, workflow, schema"
                  value={q}
                />
              </div>
              <Select
                aria-label="Review status"
                className="w-auto min-w-[10rem]"
                onChange={(event) => {
                  setPage(1);
                  setStatus(event.target.value);
                }}
                value={status}
              >
                <option value="pending">Pending</option>
                <option value="all">All reviews</option>
                <option value="approved">Approved</option>
                <option value="approved_with_edits">Approved with edits</option>
                <option value="rejected">Rejected</option>
                <option value="clarification_requested">Clarification requested</option>
                <option value="cancelled">Cancelled</option>
              </Select>
              <Select
                aria-label="Sort by"
                className="w-auto min-w-[7rem]"
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
              <Select
                aria-label="Sort direction"
                className="w-auto min-w-[5.5rem]"
                onChange={(event) => {
                  setPage(1);
                  setDirection(event.target.value);
                }}
                value={direction}
              >
                <option value="desc">Desc</option>
                <option value="asc">Asc</option>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-4">
          {reviewsQuery.isLoading ? (
            <ReviewQueueSkeleton />
          ) : reviewsQuery.isError ? (
            <Notice title="Review queue could not be loaded" tone="danger">
              {workflowErrorMessage(reviewsQuery.error)}
            </Notice>
          ) : !items.length ? (
            <Notice title={isFiltered ? "No matching reviews" : "No pending reviews"}>
              <div className="grid gap-3">
                <p>
                  {isFiltered
                    ? "Adjust the filters or search terms to widen the queue."
                    : "Review-gated workflows will appear here when a transformation needs a human decision."}
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
          ) : (
            <>
              <div className="grid gap-2 md:hidden">
                {items.map((item) => (
                  <button
                    className="grid gap-2 rounded-xl border border-border/50 bg-card p-3 text-left transition-all duration-150 list-item-hover focus-ring"
                    key={item.workflow_id}
                    onClick={() => void navigate({ to: "/workflows/$workflowId", params: { workflowId: item.workflow_id } })}
                    type="button"
                  >
                    <div className="flex min-w-0 items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="break-all font-semibold leading-tight">{item.workflow_id}</div>
                        <div className="mt-1.5 line-clamp-2 text-xs leading-5 text-muted-foreground">{item.instruction}</div>
                      </div>
                      <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge className="max-w-full whitespace-normal leading-tight" status={item.status} />
                      <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                        {item.issue_count} issues
                      </span>
                      <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                        {item.evidence_count} evidence
                      </span>
                      <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                        {item.review_status ?? "pending"}
                      </span>
                    </div>
                    <div className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                      Updated {formatCompactDate(item.updated_at)}
                    </div>
                  </button>
                ))}
              </div>
              <Table className="table-fixed" wrapperClassName="hidden max-h-[calc(100vh-18rem)] rounded-xl border border-border/50 md:block">
                <THead className="sticky top-0 z-[1] bg-card">
                  <TR>
                    <TH className="w-[40%]">Workflow</TH>
                    <TH className="w-[17%]">Status</TH>
                    <TH className="w-[7%]">Issues</TH>
                    <TH className="w-[8%]">Evidence</TH>
                    <TH className="w-[9%]">Review</TH>
                    <TH className="w-[10%]">Updated</TH>
                    <TH className="w-[9%] text-right">Action</TH>
                  </TR>
                </THead>
                <TBody>
                  {items.map((item) => (
                    <TR key={item.workflow_id}>
                      <TD className="min-w-0">
                        <div className="truncate font-semibold">{item.workflow_id}</div>
                        <div className="truncate text-xs text-muted-foreground">{item.instruction}</div>
                        <div className="mt-1 flex min-w-0 flex-wrap gap-x-2 gap-y-1 text-[11px] font-medium uppercase text-muted-foreground">
                          <span className="truncate">{item.schema_id ?? "no schema"}</span>
                          {item.review_id ? <span className="truncate">{item.review_id}</span> : null}
                        </div>
                      </TD>
                      <TD className="min-w-0">
                        <StatusBadge className="max-w-full whitespace-nowrap px-2 text-[11px]" status={item.status} />
                      </TD>
                      <TD className="tabular-nums">{item.issue_count}</TD>
                      <TD className="tabular-nums">{item.evidence_count}</TD>
                      <TD className="truncate">{item.review_status ?? "-"}</TD>
                      <TD className="text-xs text-muted-foreground">{formatCompactDate(item.updated_at)}</TD>
                      <TD className="text-right">
                        <Button
                          className="w-full max-w-[5.5rem]"
                          onClick={() => void navigate({ to: "/workflows/$workflowId", params: { workflowId: item.workflow_id } })}
                          size="sm"
                          variant="outline"
                        >
                          Review
                        </Button>
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
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
    </div>
  );
}

function ReviewSummaryStrip({
  loading,
  maxIssueCount,
  pendingVisible,
  total,
  visibleEvidenceCount,
  visibleIssueCount,
}: {
  loading: boolean;
  maxIssueCount: number;
  pendingVisible: number;
  total: number;
  visibleEvidenceCount: number;
  visibleIssueCount: number;
}) {
  return (
    <SummaryStrip>
      <SummaryStripItem
        icon={ClipboardCheck}
        label="Reviews"
        loading={loading}
        supporting="Current filter"
        value={total}
      />
      <SummaryStripItem
        icon={AlertTriangle}
        label="Pending"
        loading={loading}
        supporting="Needs decision"
        tone="warning"
        value={pendingVisible}
      />
      <SummaryStripItem
        icon={Scale}
        label="Issues"
        loading={loading}
        supporting="Page total"
        tone="warning"
        value={visibleIssueCount}
      />
      <SummaryStripItem
        icon={FileSearch}
        label="Evidence"
        loading={loading}
        supporting={loading ? "Loading" : `Max ${maxIssueCount} issues`}
        tone="info"
        value={visibleEvidenceCount}
      />
    </SummaryStrip>
  );
}

function ReviewQueueSkeleton() {
  return (
    <div aria-label="Loading review queue" className="grid gap-3" role="status">
      <div className="grid gap-2 md:hidden">
        {Array.from({ length: 3 }).map((_, index) => (
          <div
            className="grid gap-3 rounded-xl border border-border/50 bg-card p-3"
            data-testid="review-queue-skeleton-card"
            key={index}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="grid min-w-0 flex-1 gap-2">
                <Skeleton className="h-5 w-40 max-w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
              <Skeleton className="h-4 w-4 rounded-full" />
            </div>
            <div className="flex flex-wrap gap-2">
              <Skeleton className="h-6 w-36 rounded-full" />
              <Skeleton className="h-6 w-20 rounded-full" />
              <Skeleton className="h-6 w-24 rounded-full" />
            </div>
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>
      <Table
        className="table-fixed"
        wrapperClassName="hidden max-h-[calc(100vh-18rem)] rounded-xl border border-border/50 md:block"
      >
        <THead className="sticky top-0 z-[1] bg-card">
          <TR>
            <TH className="w-[40%]">Workflow</TH>
            <TH className="w-[17%]">Status</TH>
            <TH className="w-[7%]">Issues</TH>
            <TH className="w-[8%]">Evidence</TH>
            <TH className="w-[9%]">Review</TH>
            <TH className="w-[10%]">Updated</TH>
            <TH className="w-[9%] text-right">Action</TH>
          </TR>
        </THead>
        <TBody>
          {Array.from({ length: 7 }).map((_, index) => (
            <TR aria-hidden="true" data-testid="review-queue-skeleton-row" key={index}>
              <TD>
                <div className="grid gap-2">
                  <Skeleton className="h-4 w-44 max-w-full" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              </TD>
              <TD>
                <Skeleton className="h-6 w-32 rounded-full" />
              </TD>
              <TD>
                <Skeleton className="h-4 w-8" />
              </TD>
              <TD>
                <Skeleton className="h-4 w-8" />
              </TD>
              <TD>
                <Skeleton className="h-4 w-16" />
              </TD>
              <TD>
                <Skeleton className="h-4 w-20" />
              </TD>
              <TD>
                <div className="flex justify-end">
                  <Skeleton className="h-8 w-20" />
                </div>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>
    </div>
  );
}

function formatReviewCount(count: number) {
  return `${count} review${count === 1 ? "" : "s"}`;
}
