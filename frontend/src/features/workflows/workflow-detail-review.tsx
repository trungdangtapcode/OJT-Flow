import {
  AlertTriangle,
  Check,
  HelpCircle,
  MessageSquareText,
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
import { cn, formatDate, humanize } from "../../lib/utils";
import type { HumanReview } from "../../types";

export function ReviewTab({
  error,
  isPending,
  isReviewActive,
  onDecision,
  review,
}: {
  error: string | null;
  isPending: boolean;
  isReviewActive: boolean;
  onDecision: (decision: string) => void;
  review: HumanReview | null;
}) {
  if (review && isReviewActive) {
    return (
      <PendingReviewGate
        compact
        error={error}
        isPending={isPending}
        onDecision={onDecision}
        review={review}
      />
    );
  }

  return (
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
            className="grid gap-1 rounded-md border border-border bg-muted/20 p-2"
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
          <div className="overflow-hidden rounded-md border border-border bg-card">
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
      <details className="group rounded-md border border-border bg-muted/25">
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
