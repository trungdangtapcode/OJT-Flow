import { AlertTriangle, Copy, Download } from "lucide-react";
import { toast } from "sonner";

import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { SeverityBadge } from "../../components/domain/workflow-badges";
import { Notice } from "../../components/ui/notice";
import { Skeleton } from "../../components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "../../components/ui/table";
import {
  useWorkflowOutputQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import { formatDate, humanize } from "../../lib/utils";
import type { HumanReview, ValidationIssue, WorkflowEvent, WorkflowState } from "../../types";
import { PendingReviewGate } from "./workflow-detail-review";

export function Overview({
  compactReview,
  onReviewDecision,
  review,
  reviewError,
  reviewIsPending,
  workflow,
}: {
  compactReview: boolean;
  onReviewDecision: (decision: string) => void;
  review: HumanReview | null;
  reviewError: string | null;
  reviewIsPending: boolean;
  workflow: WorkflowState;
}) {
  return (
    <div className="grid min-w-0 max-w-full gap-4">
      {review ? (
        <PendingReviewGate
          compact={compactReview}
          error={reviewError}
          isPending={reviewIsPending}
          onDecision={onReviewDecision}
          review={review}
        />
      ) : null}
      <div className="grid min-w-0 max-w-full gap-4 xl:grid-cols-[minmax(280px,0.78fr)_minmax(0,1.22fr)]">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border bg-card/70 p-4">
            <CardTitle>Steps</CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <ol className="grid">
              {workflow.steps.map((step) => (
                <li className="grid grid-cols-[12px_minmax(0,1fr)_auto] items-start gap-3 border-t border-border py-2.5 first:border-t-0 first:pt-0 last:pb-0" key={step.step_id}>
                  <span className="mt-1.5 h-2.5 w-2.5 rounded-full bg-primary shadow-[0_0_0_3px_rgba(11,122,117,0.12)]" />
                  <div className="min-w-0">
                    <div className="font-extrabold leading-tight">{humanize(step.name)}</div>
                    <div className="line-clamp-2 text-sm leading-5 text-muted-foreground">{step.summary}</div>
                  </div>
                  {step.issue_count ? (
                    <span className="rounded-full bg-warning px-2 py-0.5 text-xs font-bold text-warning-foreground">{step.issue_count}</span>
                  ) : null}
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
        <Issues workflow={workflow} compact />
      </div>
    </div>
  );
}

export function Issues({ workflow, compact = false }: { workflow: WorkflowState; compact?: boolean }) {
  const issues = workflow.validation_report?.issues ?? [];
  if (compact) {
    const visibleIssues = issues.slice(0, 5);
    return (
      <Card className="min-w-0 overflow-hidden">
        <CardHeader className="border-b border-border bg-card/70 p-4">
          <CardTitle>Validation issues</CardTitle>
          <CardDescription>{formatCount(issues.length, "issue")} found</CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="grid">
            {visibleIssues.map((issue) => (
              <div
                className="grid gap-2 border-t border-border py-3 first:border-t-0 first:pt-0 last:pb-0"
                key={issue.issue_id}
              >
                <div className="flex min-w-0 flex-wrap items-center gap-2">
                  <SeverityBadge severity={issue.severity} />
                  <span className="min-w-0 break-words text-sm font-bold">{issue.kind}</span>
                </div>
                <p className="text-sm leading-5 text-muted-foreground">{issue.message}</p>
                <IssueMetadata issue={issue} />
              </div>
            ))}
            {issues.length > visibleIssues.length ? (
              <div className="mt-3 rounded-md bg-muted px-3 py-2 text-xs font-semibold text-muted-foreground">
                {formatCount(issues.length - visibleIssues.length, "more issue")} in the Issues tab.
              </div>
            ) : null}
            {!issues.length ? (
              <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
                No validation issues recorded.
              </div>
            ) : null}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70 p-4">
        <CardTitle>Validation issues</CardTitle>
        <CardDescription>{formatCount(issues.length, "issue")} found</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="grid gap-3 md:hidden">
          {issues.map((issue) => (
            <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3" key={issue.issue_id}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <SeverityBadge severity={issue.severity} />
                <IssueRowBadge issue={issue} />
              </div>
              <div className="font-semibold">{issue.kind}</div>
              <p className="text-sm leading-6 text-muted-foreground">{issue.message}</p>
              <IssueMetadata issue={issue} />
            </div>
          ))}
          {!issues.length ? (
            <div className="rounded-md border border-border p-3 text-sm text-muted-foreground">
              No validation issues recorded.
            </div>
          ) : null}
        </div>
        <Table wrapperClassName="hidden md:block">
          <THead>
            <TR>
              <TH>Severity</TH>
              <TH>Kind</TH>
              <TH>Field</TH>
              {!compact ? <TH>Row</TH> : null}
              <TH>Message</TH>
            </TR>
          </THead>
          <TBody>
            {issues.map((issue) => (
              <TR key={issue.issue_id}>
                <TD><SeverityBadge severity={issue.severity} /></TD>
                <TD className="font-medium">{issue.kind}</TD>
                <TD>{issueField(issue) ?? "-"}</TD>
                {!compact ? <TD>{issueRow(issue) ?? "-"}</TD> : null}
                <TD className="min-w-64">{issue.message}</TD>
              </TR>
            ))}
            {!issues.length ? (
              <TR><TD colSpan={compact ? 4 : 5}>No validation issues recorded.</TD></TR>
            ) : null}
          </TBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export function Evidence({ workflow }: { workflow: WorkflowState }) {
  const trace = workflow.handoff_context?.retrieval_trace;
  const safetyFlags = trace?.safety_flags ?? [];
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70 p-4">
        <div className="min-w-0">
          <CardTitle>Retrieval evidence</CardTitle>
          <CardDescription>{formatCount(workflow.retrieved_context.length, "evidence item")}</CardDescription>
        </div>
        {trace ? (
          <span className="max-w-full break-words rounded-full bg-muted px-2 py-1 text-xs font-bold">
            {trace.strategy}
          </span>
        ) : null}
      </CardHeader>
      <CardContent className="p-0 md:p-4">
        {safetyFlags.length ? (
          <div className="border-b border-amber-200 bg-amber-50 p-4 text-amber-950 md:mb-4 md:rounded-md md:border">
            <div className="flex min-w-0 items-start gap-3">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-warning text-warning-foreground">
                <AlertTriangle className="h-4 w-4" />
              </span>
              <div className="min-w-0">
                <div className="text-sm font-extrabold">Retrieval safety flags</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {safetyFlags.map((flag) => (
                    <span
                      className="rounded-full border border-amber-200 bg-warning px-2 py-1 text-xs font-bold text-warning-foreground"
                      key={flag}
                    >
                      {humanize(flag)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : null}
        {!workflow.retrieved_context.length ? (
          <div className="p-4">
            <Notice title="No retrieval evidence">
              Evidence will appear here after retrieval or FHIR profiling contributes context.
            </Notice>
          </div>
        ) : (
          <div className="grid gap-3 p-4">
            {workflow.retrieved_context.map((evidence) => (
              <EvidenceCard evidence={evidence} key={evidence.evidence_id} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function Output({ workflow }: { workflow: WorkflowState }) {
  const output = workflow.output?.transformation;
  const outputQuery = useWorkflowOutputQuery(workflow.workflow_id, Boolean(output?.output_ref));
  const artifact = outputQuery.data;
  const content = artifact?.content ?? output?.preview ?? "";
  const hasGeneratedOutput = Boolean(output?.output_ref);

  const copyOutput = async () => {
    if (!content) return;
    await navigator.clipboard.writeText(content);
    toast.success("Output copied");
  };

  const downloadOutput = () => {
    if (!content) return;
    const extension = extensionForFormat(artifact?.output_format ?? output?.output_format ?? "txt");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = `${workflow.workflow_id}.${extension}`;
    anchor.click();
    URL.revokeObjectURL(href);
  };

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>Output artifact</CardTitle>
            <CardDescription>Generated artifact, deterministic metadata, and explanation package</CardDescription>
          </div>
          {hasGeneratedOutput ? (
            <div className="flex flex-wrap gap-2">
              <Button disabled={!content} onClick={() => void copyOutput()} size="sm" type="button" variant="outline">
                <Copy className="h-4 w-4" />
                Copy
              </Button>
              <Button disabled={!content} onClick={downloadOutput} size="sm" type="button" variant="outline">
                <Download className="h-4 w-4" />
                Download
              </Button>
            </div>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
        {!hasGeneratedOutput ? (
          <Notice title="Output is not generated yet">
            Approve the review gate or resolve blocking issues before the transformation artifact is created.
          </Notice>
        ) : outputQuery.isError ? (
          <Notice title="Output artifact could not be loaded" tone="danger">
            {workflowErrorMessage(outputQuery.error)}
          </Notice>
        ) : (
          <div className="min-w-0 rounded-md border border-border bg-muted/20">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-3 py-2">
              <div className="text-sm font-bold">Artifact preview</div>
              <div className="text-xs font-semibold text-muted-foreground">
                {artifact ? formatBytes(artifact.byte_size) : "loading"}
              </div>
            </div>
            {outputQuery.isLoading ? (
              <div className="p-3">
                <Skeleton className="h-72" />
              </div>
            ) : (
              <pre className="max-h-[32rem] overflow-auto whitespace-pre-wrap break-words p-3 font-mono text-xs leading-5 text-foreground">
                {content || "No output content available."}
              </pre>
            )}
          </div>
        )}

        <div className="grid gap-4">
          <div className="grid gap-2 rounded-md border border-border p-3 text-sm">
            <Row label="Format" value={output?.output_format ?? "not generated"} />
            <Row label="Output ref" value={displayArtifactRef(output?.output_ref)} />
            <Row label="Output hash" value={artifact?.output_hash ?? output?.output_hash ?? "not generated"} />
            <Row label="Byte size" value={artifact ? formatBytes(artifact.byte_size) : "not loaded"} />
            <Row label="Warnings" value={output?.warnings.length ? output.warnings.join(", ") : "none"} />
          </div>
          <div className="rounded-md border border-border p-3 text-sm">
            <h4 className="mb-2 font-bold">Conversion metadata</h4>
            <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-words rounded-md bg-muted p-2 text-xs text-muted-foreground">
              {JSON.stringify(artifact?.diff_summary ?? output?.diff_summary ?? {}, null, 2)}
            </pre>
          </div>
          <div className="rounded-md border border-border p-3 text-sm">
            <h4 className="mb-2 font-bold">Explanation</h4>
            <p className="text-muted-foreground">{workflow.explanation?.summary ?? "Explanation is not generated yet."}</p>
            {workflow.explanation?.limitations.length ? (
              <ul className="mt-3 list-disc pl-5">
                {workflow.explanation.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
              </ul>
            ) : null}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function Audit({ events }: { events: WorkflowEvent[] }) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70 p-4">
        <CardTitle>Audit timeline</CardTitle>
        <CardDescription>{formatCount(events.length, "append-only event")}</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <ol className="relative grid gap-0 before:absolute before:left-[5px] before:top-3 before:h-[calc(100%-1.5rem)] before:w-px before:bg-border">
          {events.map((event) => (
            <li className="relative grid grid-cols-[12px_minmax(0,1fr)] gap-3" key={event.event_id}>
              <span className="mt-4 h-2.5 w-2.5 rounded-full bg-primary ring-4 ring-card" />
              <div className="min-w-0 border-b border-border py-3 last:border-b-0">
                <div className="break-words font-bold">{event.event_type}</div>
                <div className="text-xs text-muted-foreground">
                  {formatDate(event.timestamp)} / {event.actor_type}:{event.actor_id}
                </div>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">{event.summary}</p>
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

function IssueMetadata({ issue }: { issue: ValidationIssue }) {
  const field = issueField(issue);
  const row = issueRow(issue);
  const metadata = [
    field ? `Field ${field}` : null,
    row ? `Row ${row}` : null,
  ].filter((item): item is string => Boolean(item));

  if (!metadata.length) return null;

  return (
    <div className="flex flex-wrap gap-2 text-[11px] font-bold uppercase text-muted-foreground">
      {metadata.map((item) => (
        <span className="max-w-full break-words" key={item}>{item}</span>
      ))}
    </div>
  );
}

function IssueRowBadge({ issue }: { issue: ValidationIssue }) {
  const row = issueRow(issue);
  if (!row) return null;
  return (
    <span className="text-xs font-bold uppercase text-muted-foreground">
      row {row}
    </span>
  );
}

function issueField(issue: ValidationIssue) {
  return issue.location?.field ?? issue.location?.column ?? null;
}

function issueRow(issue: ValidationIssue) {
  return issue.location?.row ?? null;
}

function EvidenceCard({ evidence }: { evidence: WorkflowState["retrieved_context"][number] }) {
  return (
    <article className="grid min-w-0 gap-3 rounded-md border border-border bg-card p-3 shadow-sm">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="break-words font-extrabold leading-5" title={evidence.source_id}>
            {evidence.source_id}
          </div>
          <div className="mt-0.5 break-words text-xs font-semibold text-muted-foreground">
            {evidence.source_type}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
          <span className="rounded-full bg-muted px-2 py-1 text-xs font-bold text-muted-foreground">
            {evidence.trust_level}
          </span>
          <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-bold tabular-nums text-emerald-800">
            {formatConfidence(evidence.confidence)}
          </span>
        </div>
      </div>
      <p className="min-w-0 break-words text-sm leading-6 text-foreground">
        {formatEvidenceClaim(evidence.claim)}
      </p>
      <div className="grid gap-1 border-t border-border pt-2 text-[11px] font-bold uppercase text-muted-foreground sm:grid-cols-[7rem_minmax(0,1fr)]">
        <span>Evidence ID</span>
        <span className="min-w-0 break-all font-mono normal-case tracking-normal">{evidence.evidence_id}</span>
      </div>
    </article>
  );
}

function formatEvidenceClaim(claim: string) {
  return claim
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[ \t]+/g, " ")
    .trim();
}

function formatConfidence(confidence: number | null | undefined) {
  return typeof confidence === "number" ? `${Math.round(confidence * 100)}%` : "n/a";
}

function extensionForFormat(format: string) {
  if (format === "json") return "json";
  if (format === "yaml") return "yaml";
  if (format === "csv") return "csv";
  return "txt";
}

function displayArtifactRef(outputRef: string | null | undefined) {
  if (!outputRef) return "not stored";
  const lastSegment = outputRef.split("/").filter(Boolean).at(-1) ?? outputRef;
  return lastSegment.replace(/\.[^.]+$/, "");
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[110px_minmax(0,1fr)] gap-3">
      <span className="font-bold text-muted-foreground">{label}</span>
      <span className="break-words">{value}</span>
    </div>
  );
}
