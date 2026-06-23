import {
  AlertTriangle,
  Check,
  Database,
  FileText,
  HelpCircle,
  MessageSquareText,
  ShieldCheck,
  X,
} from "lucide-react";

import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Notice } from "../../components/ui/notice";
import {
  useWorkflowInputPreviewQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import { cn, formatDate, humanize } from "../../lib/utils";
import type {
  HumanReview,
  ValidationIssue,
  WorkflowInputPreview,
  WorkflowState,
} from "../../types";

export function ReviewTab({
  error,
  isPending,
  isReviewActive,
  onDecision,
  review,
  workflow,
}: {
  error: string | null;
  isPending: boolean;
  isReviewActive: boolean;
  onDecision: (decision: string) => void;
  review: HumanReview | null;
  workflow: WorkflowState;
}) {
  const inputPreviewQuery = useWorkflowInputPreviewQuery(workflow.workflow_id, Boolean(review));

  if (review && isReviewActive) {
    return (
      <div className="grid gap-4">
        <ReviewEvidenceBeforeDecision
          inputPreview={inputPreviewQuery.data ?? null}
          inputPreviewError={inputPreviewQuery.isError ? workflowErrorMessage(inputPreviewQuery.error) : null}
          inputPreviewLoading={inputPreviewQuery.isLoading}
          workflow={workflow}
        />
        <PendingReviewGate
          error={error}
          isPending={isPending}
          onDecision={onDecision}
          review={review}
        />
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      {review ? (
        <ReviewEvidenceBeforeDecision
          inputPreview={inputPreviewQuery.data ?? null}
          inputPreviewError={inputPreviewQuery.isError ? workflowErrorMessage(inputPreviewQuery.error) : null}
          inputPreviewLoading={inputPreviewQuery.isLoading}
          workflow={workflow}
        />
      ) : null}
      <Card>
        <CardHeader>
          <CardTitle>Human review</CardTitle>
          <CardDescription>
            {review ? `${review.trigger} / ${review.review_id}` : "No review gate is attached."}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm text-muted-foreground">
          <div>{review ? `Review status: ${humanize(review.status)}` : "No review required."}</div>
          {review ? <ReviewClarificationHistory review={review} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}

export function ReviewEvidenceBeforeDecision({
  inputPreview,
  inputPreviewError,
  inputPreviewLoading,
  workflow,
}: {
  inputPreview: WorkflowInputPreview | null;
  inputPreviewError: string | null;
  inputPreviewLoading: boolean;
  workflow: WorkflowState;
}) {
  const issues = workflow.validation_report?.issues ?? [];
  const evidence = workflow.retrieved_context ?? [];
  return (
    <Card className="min-w-0 overflow-hidden border-blue-200">
      <CardHeader className="border-b border-blue-100 bg-blue-50/70">
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-blue-700" />
          Read before approval
        </CardTitle>
        <CardDescription>
          Review the source/extracted text, validation issues, and evidence before approving the
          transformation.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4">
        <InputPreviewPanel
          error={inputPreviewError}
          loading={inputPreviewLoading}
          preview={inputPreview}
        />
        <div className="grid gap-3 lg:grid-cols-2">
          <ReviewIssueSummary issues={issues} />
          <ReviewEvidenceSummary evidence={evidence} />
        </div>
      </CardContent>
    </Card>
  );
}

function InputPreviewPanel({
  error,
  loading,
  preview,
}: {
  error: string | null;
  loading: boolean;
  preview: WorkflowInputPreview | null;
}) {
  if (loading) {
    return (
      <div className="rounded-lg border border-border/60 bg-muted/20 p-3 text-sm font-semibold text-muted-foreground">
        Loading source preview...
      </div>
    );
  }
  if (error) {
    return (
      <Notice title="Source preview could not be loaded" tone="danger">
        {error}
      </Notice>
    );
  }
  if (!preview) {
    return (
      <Notice title="No source preview">
        The workflow has no readable input preview. Do not approve until source data is available.
      </Notice>
    );
  }
  const extractor = preview.extraction ? stringifyDisplayValue(preview.extraction.extractor_used) : "";
  return (
    <section className="grid gap-3 rounded-lg border border-border/60 bg-card p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-bold">
          <FileText className="h-4 w-4 text-primary" />
          Source / extracted input
        </div>
        <div className="flex flex-wrap gap-1.5 text-xs font-bold text-muted-foreground">
          <span className="rounded-full bg-muted px-2 py-0.5">
            {preview.source_filename || preview.detected_format}
          </span>
          <span className="rounded-full bg-muted px-2 py-0.5">
            {formatBytes(preview.byte_size)}
          </span>
          {extractor ? (
            <span className="rounded-full bg-muted px-2 py-0.5">{extractor}</span>
          ) : null}
        </div>
      </div>
      <pre className="max-h-[26rem] overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-950 p-3 font-mono text-xs leading-5 text-slate-50">
        {preview.content || "No extracted/source text available."}
      </pre>
      <div className="grid gap-1 text-xs text-muted-foreground">
        {preview.truncated ? (
          <div className="font-semibold text-amber-700">
            Preview truncated to {preview.max_chars.toLocaleString()} characters.
          </div>
        ) : null}
        <div>Input hash: {preview.input_hash}</div>
      </div>
    </section>
  );
}

function ReviewIssueSummary({ issues }: { issues: ValidationIssue[] }) {
  const visibleIssues = issues.slice(0, 6);
  return (
    <section className="grid content-start gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
      <div className="flex items-center gap-2 font-bold">
        <AlertTriangle className="h-4 w-4 text-amber-600" />
        Validation issues
      </div>
      {visibleIssues.length ? (
        <div className="grid gap-2">
          {visibleIssues.map((issue) => (
            <div className="rounded-md bg-card p-2 text-sm" key={issue.issue_id}>
              <div className="font-bold">{humanize(issue.kind)}</div>
              <div className="mt-1 text-xs leading-5 text-muted-foreground">{issue.message}</div>
            </div>
          ))}
          {issues.length > visibleIssues.length ? (
            <div className="text-xs font-semibold text-muted-foreground">
              {issues.length - visibleIssues.length} more issue
              {issues.length - visibleIssues.length === 1 ? "" : "s"} in the Issues tab.
            </div>
          ) : null}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No validation issues recorded.</p>
      )}
    </section>
  );
}

function ReviewEvidenceSummary({ evidence }: { evidence: WorkflowState["retrieved_context"] }) {
  const visibleEvidence = evidence.slice(0, 5);
  return (
    <section className="grid content-start gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
      <div className="flex items-center gap-2 font-bold">
        <Database className="h-4 w-4 text-primary" />
        Evidence
      </div>
      {visibleEvidence.length ? (
        <div className="grid gap-2">
          {visibleEvidence.map((item) => (
            <div className="rounded-md bg-card p-2 text-sm" key={item.evidence_id}>
              <div className="break-all font-mono text-xs text-muted-foreground">
                {item.source_id}
              </div>
              <div className="mt-1 line-clamp-2 text-xs leading-5">{item.claim}</div>
            </div>
          ))}
          {evidence.length > visibleEvidence.length ? (
            <div className="text-xs font-semibold text-muted-foreground">
              {evidence.length - visibleEvidence.length} more evidence item
              {evidence.length - visibleEvidence.length === 1 ? "" : "s"} in the Evidence tab.
            </div>
          ) : null}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          No evidence attached. Do not approve evidence-dependent transformations without context.
        </p>
      )}
    </section>
  );
}

export function PendingReviewGate({
  compact = false,
  error,
  isPending,
  onDecision,
  review,
}: {
  compact?: boolean;
  error: string | null;
  isPending: boolean;
  onDecision: (decision: string) => void;
  review: HumanReview;
}) {
  return (
    <Card
      className={cn(
        "min-w-0 overflow-hidden border-amber-200",
        compact ? "bg-card shadow-sm" : "bg-amber-50/35",
      )}
    >
      <CardHeader className={cn("gap-3", compact && "gap-2 p-3 sm:p-4")}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <span
              className={cn(
                "mt-0.5 flex shrink-0 items-center justify-center rounded-md bg-warning text-warning-foreground",
                compact ? "h-8 w-8" : "h-9 w-9",
              )}
            >
              <AlertTriangle className={cn(compact ? "h-4 w-4" : "h-5 w-5")} />
            </span>
            <div className="min-w-0">
              <CardTitle>{compact ? "Human review" : "Decision required"}</CardTitle>
              <CardDescription className="mt-1">
                {review.trigger} / {review.review_id}
              </CardDescription>
            </div>
          </div>
          <span className="rounded-full border border-amber-200 bg-warning px-2.5 py-1 text-xs font-bold text-warning-foreground">
            {humanize(review.status)}
          </span>
        </div>
        <p className={cn("text-sm text-muted-foreground", compact ? "line-clamp-2 leading-5" : "leading-6")}>
          {review.question}
        </p>
      </CardHeader>
      <CardContent className={cn("grid gap-3", compact && "gap-2 px-3 pb-3 sm:px-4 sm:pb-4")}>
        {error ? (
          <Notice title="Review decision could not be recorded" tone="danger">
            {error}
          </Notice>
        ) : null}
        <ReviewClarificationHistory review={review} />
        {!compact ? <ReviewActionSummary review={review} /> : null}
        <ReviewDecisionButtons
          allowedDecisions={review.allowed_decisions}
          compact={compact}
          disabled={isPending}
          onDecision={onDecision}
        />
      </CardContent>
    </Card>
  );
}

export function ReviewClarificationHistory({ review }: { review: HumanReview }) {
  const requests = review.clarification_requests ?? [];
  if (!requests.length) return null;

  return (
    <div
      className="grid gap-2 rounded-md border border-amber-200 bg-card/80 p-3 text-sm"
      data-testid="review-clarification-history"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-bold text-foreground">
          <MessageSquareText className="h-4 w-4 text-warning-foreground" />
          Clarification history
        </div>
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-bold text-muted-foreground">
          {requests.length} request{requests.length === 1 ? "" : "s"}
        </span>
      </div>
      <ol className="grid gap-2">
        {requests.map((request, index) => (
          <li
            className="grid gap-1 rounded-lg border border-border/60 bg-muted/20 p-2"
            key={`${request.requested_at ?? "clarification"}-${index}`}
          >
            <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-muted-foreground">
              <span>{request.requested_by || "unknown reviewer"}</span>
              {request.requested_at ? <span>{formatDate(request.requested_at)}</span> : null}
            </div>
            <ClarificationPayload payload={request.payload ?? {}} />
          </li>
        ))}
      </ol>
    </div>
  );
}

function ClarificationPayload({ payload }: { payload: Record<string, unknown> }) {
  const entries = Object.entries(payload);
  if (!entries.length) {
    return <div className="text-xs text-muted-foreground">No additional payload.</div>;
  }
  return (
    <dl className="grid gap-1 text-xs">
      {entries.map(([key, value]) => (
        <div className="grid gap-1 sm:grid-cols-[8rem_minmax(0,1fr)]" key={key}>
          <dt className="font-bold uppercase text-muted-foreground">{humanize(key)}</dt>
          <dd className="min-w-0 break-words text-foreground">{stringifyDisplayValue(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function ReviewActionSummary({ review }: { review: HumanReview }) {
  const actions = extractReviewActions(review.proposed_action);
  const visibleActionCount = 4;
  const visibleActions = actions.slice(0, visibleActionCount);
  return (
    <div className="grid gap-3 rounded-md border border-amber-200 bg-card/80 p-3 text-sm" data-testid="review-action-summary">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="font-bold">Proposed action</div>
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-bold text-muted-foreground">
          {actions.length || 1} action{actions.length === 1 ? "" : "s"}
        </span>
      </div>
      {actions.length ? (
        <>
          <div className="overflow-hidden rounded-lg border border-border/60 bg-card">
            {visibleActions.map((action, index) => (
              <div
                className="grid gap-2 border-t border-border p-3 first:border-t-0 lg:grid-cols-[8rem_minmax(10rem,0.9fr)_minmax(0,1.4fr)]"
                data-testid="review-action-card"
                key={`${action.action}-${action.field}-${index}`}
              >
                <div className="text-xs font-bold uppercase tracking-normal text-muted-foreground">
                  {action.field || "record"}
                </div>
                <div className="font-bold leading-5">{humanize(action.action || "review action")}</div>
                {action.reason ? (
                  <p className="line-clamp-2 text-xs leading-5 text-muted-foreground">
                    {action.reason}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
          {actions.length > visibleActions.length ? (
            <div className="text-xs font-semibold text-muted-foreground">
              {actions.length - visibleActions.length} more action
              {actions.length - visibleActions.length === 1 ? "" : "s"} in the raw payload.
            </div>
          ) : null}
        </>
      ) : (
        <p className="text-sm leading-6 text-muted-foreground">
          Review the proposed transformation payload before approving execution.
        </p>
      )}
      <details className="group rounded-lg border border-border/60 bg-muted/25">
        <summary className="cursor-pointer px-3 py-2 text-xs font-bold uppercase text-muted-foreground">
          Raw action payload
        </summary>
        <pre
          className="max-h-52 overflow-auto whitespace-pre-wrap break-words border-t border-border p-3 font-mono text-xs leading-5 text-muted-foreground"
          data-testid="review-raw-action-payload"
        >
          {JSON.stringify(review.proposed_action, null, 2)}
        </pre>
      </details>
    </div>
  );
}

function ReviewDecisionButtons({
  allowedDecisions,
  compact = false,
  disabled,
  onDecision,
}: {
  allowedDecisions: string[];
  compact?: boolean;
  disabled: boolean;
  onDecision: (decision: string) => void;
}) {
  const visibleDecisions = allowedDecisions.filter((decision) => decision !== "approve_with_edits");
  return (
    <div className={cn(compact ? "grid grid-cols-2 gap-2 sm:flex sm:flex-wrap" : "flex flex-wrap gap-2")}>
      {visibleDecisions.map((decision) => {
        const isApprove = decision === "approve";
        const isReject = decision === "reject";
        const isClarify = decision === "clarify";
        const Icon = isApprove ? Check : isClarify ? HelpCircle : X;
        const label = {
          approve: "Approve",
          approve_with_edits: "Approve with edits",
          cancel: "Cancel",
          clarify: "Clarify",
          reject: "Reject",
        }[decision] ?? humanize(decision);
        return (
          <Button
            className={compact ? "w-full sm:w-auto" : undefined}
            disabled={disabled}
            key={decision}
            onClick={() => onDecision(decision)}
            size={compact ? "sm" : "default"}
            type="button"
            variant={isApprove ? "default" : isReject ? "destructive" : "secondary"}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Button>
        );
      })}
    </div>
  );
}

function extractReviewActions(proposedAction: Record<string, unknown>) {
  const rawActions = proposedAction.actions;
  if (!Array.isArray(rawActions)) return [];
  return rawActions
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object" && !Array.isArray(item))
    .map((item) => ({
      action: stringifyReviewValue(item.action),
      field: stringifyReviewValue(item.field),
      reason: stringifyReviewValue(item.reason),
    }));
}

function stringifyReviewValue(value: unknown) {
  return typeof value === "string" ? value : "";
}

function stringifyDisplayValue(value: unknown) {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (value === null || value === undefined) return "-";
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function formatBytes(bytes: number) {
  if (!Number.isFinite(bytes)) return "n/a";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
