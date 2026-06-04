import { Activity, AlertTriangle, FileSearch, History } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "../../components/ui/card";
import { Notice } from "../../components/ui/notice";
import { Skeleton } from "../../components/ui/skeleton";
import { SummaryStrip, SummaryStripItem } from "../../components/ui/summary-strip";
import { cn, formatDate } from "../../lib/utils";
import type { WorkflowEvent, WorkflowState } from "../../types";

export function WorkflowDetailSkeleton({ focused }: { focused: boolean }) {
  return (
    <div
      aria-label="Loading workflow detail"
      className={cn(
        "grid w-full max-w-full min-w-0 self-start",
        focused ? "mx-auto max-w-[1180px] gap-4" : "gap-3",
      )}
      role="status"
    >
      <Card className={cn("min-w-0 max-w-full overflow-hidden", focused && "border-l-4 border-l-primary/25")}>
        <CardHeader className={cn("gap-3", !focused && "gap-2 p-3 sm:p-4")}>
          <div className="flex items-center justify-between gap-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-7 w-28 rounded-full" />
          </div>
          <div className="grid gap-2">
            <Skeleton className="h-7 w-56 max-w-full" />
            <Skeleton className="h-4 w-full max-w-md" />
          </div>
          <div className="flex flex-wrap gap-2">
            <Skeleton className="h-6 w-36 rounded-full" />
            <Skeleton className="h-6 w-24 rounded-full" />
          </div>
        </CardHeader>
      </Card>

      <div className="grid overflow-hidden rounded-lg border border-border bg-card shadow-[0_1px_3px_rgba(16,24,40,0.06)] sm:grid-cols-4">
        {["steps", "issues", "evidence", "audit"].map((item) => (
          <div
            className="grid gap-2 border-b border-border p-4 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0"
            key={item}
          >
            <div className="flex items-center justify-between">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-7 w-7 rounded-md" />
            </div>
            <Skeleton className="h-7 w-10" />
            <Skeleton className="h-4 w-28" />
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-border bg-muted/45 p-1">
        <div className="flex flex-wrap gap-1">
          {["overview", "issues", "evidence", "review", "output", "audit"].map((item, index) => (
            <Skeleton
              className={cn("h-9 rounded-md", index === 0 ? "w-24 bg-card" : "w-20")}
              key={item}
            />
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader>
            <Skeleton className="h-5 w-24" />
          </CardHeader>
          <CardContent className="grid gap-3">
            {["created", "parsed", "validated", "completed"].map((item) => (
              <div
                className="flex items-start gap-3 border-b border-border pb-3 last:border-b-0"
                key={item}
              >
                <Skeleton className="mt-1 h-3 w-3 rounded-full" />
                <div className="grid min-w-0 flex-1 gap-2">
                  <Skeleton className="h-5 w-44 max-w-full" />
                  <Skeleton className="h-4 w-full max-w-xs" />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-4 w-20" />
          </CardHeader>
          <CardContent className="grid gap-3 pt-4 sm:pt-5">
            {["issue-a", "issue-b", "issue-c"].map((item) => (
              <div className="grid gap-2 border-b border-border pb-3 last:border-b-0" key={item}>
                <div className="flex flex-wrap items-center gap-2">
                  <Skeleton className="h-6 w-20 rounded-full" />
                  <Skeleton className="h-5 w-36 max-w-full" />
                </div>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-3 w-28" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function WorkflowFailureNotice({ workflow }: { workflow: WorkflowState }) {
  const failure = workflow.failure;
  if (!failure) return null;

  return (
    <div data-testid="workflow-failure-notice">
      <Notice title="Workflow failed" tone="danger">
        <div className="grid gap-3">
          <p>{failure.message}</p>
          <dl className="grid gap-2 text-xs sm:grid-cols-3">
            <div>
              <dt className="font-bold uppercase text-destructive">Code</dt>
              <dd className="mt-1 break-words font-mono text-foreground">{failure.code}</dd>
            </div>
            <div>
              <dt className="font-bold uppercase text-destructive">Type</dt>
              <dd className="mt-1 break-words font-mono text-foreground">{failure.error_type}</dd>
            </div>
            <div>
              <dt className="font-bold uppercase text-destructive">Failed</dt>
              <dd className="mt-1 text-foreground">{formatDate(failure.failed_at)}</dd>
            </div>
          </dl>
          {workflow.risk_flags?.length ? (
            <div className="flex flex-wrap gap-2">
              {workflow.risk_flags.map((flag) => (
                <span
                  className="rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-xs font-bold text-red-800"
                  key={flag}
                >
                  {flag}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </Notice>
    </div>
  );
}

export function WorkflowFactStrip({
  events,
  workflow,
}: {
  events: WorkflowEvent[];
  workflow: WorkflowState;
}) {
  const issueCount = workflow.validation_report?.issues.length ?? 0;
  return (
    <SummaryStrip>
      <SummaryStripItem
        icon={Activity}
        label="Steps"
        supporting="Workflow progress"
        tone="neutral"
        value={workflow.steps.length}
      />
      <SummaryStripItem
        icon={AlertTriangle}
        label="Issues"
        supporting="Validation load"
        tone={issueCount ? "warning" : "success"}
        value={issueCount}
      />
      <SummaryStripItem
        icon={FileSearch}
        label="Evidence"
        supporting="Retrieval context"
        tone="info"
        value={workflow.retrieved_context.length}
      />
      <SummaryStripItem
        icon={History}
        label="Audit events"
        supporting="Persisted timeline"
        tone="neutral"
        value={events.length}
      />
    </SummaryStrip>
  );
}
