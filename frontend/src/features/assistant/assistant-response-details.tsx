import * as React from "react";
import {
  CheckCircle2,
  Clipboard,
  ExternalLink,
  Network,
  Route,
  Settings2,
  ShieldAlert,
} from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Notice } from "../../components/ui/notice";
import { cn, humanize } from "../../lib/utils";
import { assistantEvidenceAnchorId } from "../../lib/evidence-links";
import type {
  AssistantEvidenceSummary,
  AssistantFinding,
  AssistantResponse,
  AssistantToolResult,
  RetrievalDiversitySummary,
  RetrievalEvidenceBucket,
  RetrievalStandardSearchPlan,
  RetrievalStandardSearchStep,
} from "../../types";
import { formatCount, previewJson } from "./assistant-format";
import {
  arrayCount,
  assistantEvidenceBucketVariant,
  assistantEvidenceMatchExplanation,
  assistantStandardSearchMatchReasons,
  badgeVariant,
  evidenceJumpActions,
  evidenceJumpActionsForSummary,
  evidenceLocatorSummary,
  findingBadgeVariant,
  matchSupportBadgeVariant,
  stringArrayValue,
  toolDiversitySummary,
  toolEvidence,
  toolEvidenceBuckets,
  toolSearchHints,
  toolStandardSearchPlan,
  workflowIdForToolCall,
} from "./assistant-response-model";
import type { AssistantEvidenceJumpAction } from "./assistant-response-model";
import type { AssistantSearchHint } from "./assistant-response-model";

export function AssistantResponseDetails({ response }: { response: AssistantResponse }) {
  return (
    <div className="grid gap-3">
      <div className="flex flex-wrap gap-1.5">
        <Badge variant="muted">
          plan {response.mode} / answer {response.synthesis_mode}
        </Badge>
        {response.model ? <Badge variant="muted">{response.model}</Badge> : null}
      </div>
      {response.warnings.length > 0 ? (
        <Notice title="Warnings">
          {response.warnings.join(" ")}
        </Notice>
      ) : null}
      {response.findings.length > 0 ? (
        <FindingsPanel findings={response.findings} />
      ) : null}
      {response.evidence_summary.length > 0 ? (
        <EvidenceSummaryPanel
          evidence={response.evidence_summary}
          toolCalls={response.tool_calls}
        />
      ) : null}
      {response.tool_calls.length > 0 ? (
        <div className="grid gap-3">
          {response.tool_calls.map((call, index) => (
            <ToolResultCard call={call} key={`${call.tool_name}-${index}`} />
          ))}
        </div>
      ) : null}
      {response.suggestions.length > 0 ? (
        <div className="grid gap-2">
          {response.suggestions.map((suggestion) => (
            <div className="flex items-start gap-2 text-sm text-muted-foreground" key={suggestion}>
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              <span>{suggestion}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function FindingsPanel({ findings }: { findings: AssistantFinding[] }) {
  return (
    <div className="grid gap-2">
      {findings.map((finding, index) => (
        <div
          className={cn(
            "rounded-md border p-3",
            finding.severity === "error"
              ? "border-red-200 bg-red-50"
              : finding.severity === "warning" || finding.severity === "action_required"
                ? "border-amber-200 bg-amber-50"
                : "border-border bg-muted/35",
          )}
          key={`${finding.title}-${index}`}
        >
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-black">{finding.title}</div>
            <Badge variant={findingBadgeVariant(finding.severity)}>
              {humanize(finding.severity)}
            </Badge>
            {finding.source_tool ? <Badge variant="muted">{humanize(finding.source_tool)}</Badge> : null}
          </div>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{finding.detail}</p>
        </div>
      ))}
    </div>
  );
}

function EvidenceSummaryPanel({
  evidence,
  toolCalls,
}: {
  evidence: AssistantEvidenceSummary[];
  toolCalls: AssistantToolResult[];
}) {
  return (
    <div className="grid gap-2">
      <div className="text-xs font-black uppercase text-muted-foreground">Evidence summary</div>
      {evidence.map((item) => (
        <div className="rounded-md border border-border bg-muted/35 p-3" key={`${item.source_id}-${item.claim}`}>
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-black">{item.source_id}</div>
            <Badge variant="muted">{humanize(item.trust_level)}</Badge>
            {typeof item.confidence === "number" ? (
              <Badge variant="default">{Math.round(item.confidence * 100)}%</Badge>
            ) : null}
          </div>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.claim}</p>
          <AssistantEvidenceMatchStrip item={item} />
          <AssistantEvidenceJumpActions
            actions={evidenceJumpActionsForSummary(item, toolCalls)}
          />
        </div>
      ))}
    </div>
  );
}

function AssistantEvidenceMatchStrip({ item }: { item: AssistantEvidenceSummary }) {
  const explanation = assistantEvidenceMatchExplanation(item);
  if (!explanation) return null;
  return (
    <div className="mt-2 grid gap-2 rounded-md border border-border bg-card/70 px-2 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <Badge variant={matchSupportBadgeVariant(explanation.supportStatus)}>
          {humanize(explanation.supportStatus)}
        </Badge>
        {explanation.topScoreDriver ? (
          <Badge className="max-w-full break-words" variant="muted">
            {explanation.topScoreDriver}
          </Badge>
        ) : null}
        <Badge variant="muted">
          {formatCount(explanation.provenanceCount, "provenance field")}
        </Badge>
        <Badge variant="muted">
          {formatCount(explanation.rankingSignalCount, "ranking signal")}
        </Badge>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {explanation.bucketLabels.map((label) => (
          <Badge className="max-w-full break-words" key={`bucket-${label}`} variant="muted">
            {label}
          </Badge>
        ))}
        {explanation.conceptLabels.map((label) => (
          <Badge className="max-w-full break-words" key={`concept-${label}`} variant="muted">
            {label}
          </Badge>
        ))}
        {explanation.aspectLabels.map((label) => (
          <Badge className="max-w-full break-words" key={`aspect-${label}`} variant="muted">
            {label}
          </Badge>
        ))}
      </div>
    </div>
  );
}

export function AssistantStatus({ response }: { response: AssistantResponse }) {
  const blocked = response.tool_calls.some((call) => call.status === "requires_approval");
  const failed = response.tool_calls.some((call) => call.status === "failed");
  return (
    <Badge variant={failed ? "destructive" : blocked ? "warning" : "success"}>
      {failed ? "failed" : blocked ? "approval required" : "completed"}
    </Badge>
  );
}

function ToolResultCard({ call }: { call: AssistantToolResult }) {
  const evidence = toolEvidence(call);
  const evidenceBuckets = toolEvidenceBuckets(call);
  const standardSearchPlan = toolStandardSearchPlan(call);
  const searchHints = toolSearchHints(call);
  const diversity = toolDiversitySummary(call);
  const workflowId = workflowIdForToolCall(call);
  return (
    <details className="overflow-hidden rounded-md border border-border bg-muted/20">
      <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-2 border-b border-border bg-muted/35 px-3 py-2">
        <div className="flex min-w-0 items-center gap-2">
          <Settings2 className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="truncate font-mono text-xs font-black">{call.tool_name}</span>
        </div>
        <Badge variant={badgeVariant(call.status)}>{humanize(call.status)}</Badge>
      </summary>
      <div className="grid gap-3 p-3">
        <div className="flex min-w-0 items-start gap-2 text-sm">
          {call.status === "requires_approval" ? (
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          ) : (
            <CheckCircle2
              className={cn(
                "mt-0.5 h-4 w-4 shrink-0",
                call.status === "completed" ? "text-emerald-600" : "text-muted-foreground",
              )}
            />
          )}
          <p className="min-w-0 break-words leading-6 text-muted-foreground">
            {call.summary}
          </p>
        </div>

        {evidenceBuckets.length > 0 ? (
          <AssistantEvidencePack buckets={evidenceBuckets} />
        ) : null}

        {standardSearchPlan ? (
          <AssistantStandardSearchPlan plan={standardSearchPlan} />
        ) : null}

        {searchHints.length ? (
          <AssistantMedicalSearchHints hints={searchHints} />
        ) : null}

        {diversity ? (
          <AssistantSourceDiversity diversity={diversity} />
        ) : null}

        {evidence.length > 0 ? (
          <div className="grid gap-2">
            {evidence.slice(0, 5).map((item) => (
              <div
                className="grid scroll-mt-24 gap-2 rounded-md border border-border bg-card p-3"
                id={assistantEvidenceAnchorId(item.evidence_id)}
                key={item.evidence_id}
              >
                <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="break-words text-sm font-black">{item.source_id}</div>
                    <div className="mt-0.5 break-words text-xs font-semibold text-muted-foreground">
                      {evidenceLocatorSummary(item)}
                    </div>
                  </div>
                  <Badge variant="muted">{item.evidence_id}</Badge>
                </div>
                <p className="mt-1 line-clamp-3 text-sm leading-6 text-muted-foreground">
                  {item.claim}
                </p>
                <AssistantEvidenceJumpActions
                  actions={evidenceJumpActions(item, workflowId)}
                />
              </div>
            ))}
          </div>
        ) : (
          <pre className="max-h-72 overflow-auto rounded-md bg-muted p-3 text-xs leading-5 text-muted-foreground">
            {previewJson(call.output)}
          </pre>
        )}
      </div>
    </details>
  );
}

function AssistantEvidenceJumpActions({
  actions,
}: {
  actions: AssistantEvidenceJumpAction[];
}) {
  if (!actions.length) return null;
  return (
    <div className="mt-2 flex min-w-0 flex-wrap gap-2">
      {actions.map((action) => (
        <Button
          asChild
          className="max-w-full"
          key={`${action.source}-${action.href}`}
          size="sm"
          type="button"
          variant="outline"
        >
          <a href={action.href} title={action.detail}>
            {action.source === "assistant" ? (
              <Route className="h-4 w-4" />
            ) : (
              <ExternalLink className="h-4 w-4" />
            )}
            {action.label}
          </a>
        </Button>
      ))}
    </div>
  );
}

function AssistantStandardSearchPlan({
  plan,
}: {
  plan: RetrievalStandardSearchPlan;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex min-w-0 items-center gap-2 text-xs font-black uppercase text-muted-foreground">
            <Route className="h-4 w-4 shrink-0 text-primary" />
            Standards plan
          </div>
          <div className="mt-1 break-words text-sm leading-6 text-muted-foreground">
            {plan.summary}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
          <Badge variant="default">{humanize(plan.primary_route)}</Badge>
          <Badge variant="muted">{formatCount(plan.steps.length, "step")}</Badge>
        </div>
      </div>
      <div className="grid gap-1.5">
        {plan.steps.slice(0, 3).map((step) => (
          <AssistantStandardSearchStep key={step.step_id} step={step} />
        ))}
      </div>
      {plan.governance_notes.length ? (
        <div className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-950">
          <div className="font-black uppercase">Guardrails</div>
          {plan.governance_notes.slice(0, 2).map((note) => (
            <div className="grid grid-cols-[12px_minmax(0,1fr)] gap-2" key={note}>
              <span aria-hidden="true" className="font-black">
                -
              </span>
              <span className="break-words">{note}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function AssistantStandardSearchStep({
  step,
}: {
  step: RetrievalStandardSearchStep;
}) {
  return (
    <div className="grid gap-1 rounded-md border border-border bg-muted/20 px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <Badge variant="muted">P{step.priority}</Badge>
        <Badge variant="success">{step.standard_system}</Badge>
        <Badge variant="muted">{humanize(step.route_type)}</Badge>
        <span className="min-w-0 break-words font-black">{step.label}</span>
      </div>
      <div className="break-words leading-5 text-muted-foreground">{step.rationale}</div>
      <AssistantStandardSearchMatchReasons metadata={step.metadata} />
      <div className="break-words rounded border border-border bg-card px-2 py-1.5 font-mono leading-5">
        {step.query}
      </div>
    </div>
  );
}

function AssistantStandardSearchMatchReasons({
  metadata,
}: {
  metadata: Record<string, unknown>;
}) {
  const reasons = assistantStandardSearchMatchReasons(metadata);
  if (!reasons.length) {
    return null;
  }
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5">
      <span className="font-black uppercase text-muted-foreground">Matched by</span>
      {reasons.map((reason) => (
        <Badge key={`${reason.label}:${reason.value}`} variant={reason.variant}>
          {reason.label}: {reason.value}
        </Badge>
      ))}
    </div>
  );
}

function AssistantMedicalSearchHints({ hints }: { hints: AssistantSearchHint[] }) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex min-w-0 items-center gap-2 text-xs font-black uppercase text-muted-foreground">
            <Route className="h-4 w-4 shrink-0 text-primary" />
            Medical search hints
          </div>
          <div className="mt-1 text-sm leading-6 text-muted-foreground">
            Backend-generated routes for governed terminology, FHIR, literature, or regulatory follow-up.
          </div>
        </div>
        <Badge variant="muted">{formatCount(hints.length, "hint")}</Badge>
      </div>
      <div className="grid gap-1.5">
        {hints.slice(0, 4).map((hint) => (
          <AssistantMedicalSearchHintCard hint={hint} key={`${hint.target}:${hint.query}`} />
        ))}
      </div>
    </div>
  );
}

function AssistantMedicalSearchHintCard({ hint }: { hint: AssistantSearchHint }) {
  const [copied, setCopied] = React.useState(false);
  const endpointScope = stringArrayValue(hint.metadata.scope_endpoints);
  const selectedTerms = stringArrayValue(hint.metadata.selected_terms);
  const selectedUnits = stringArrayValue(hint.metadata.selected_unit_candidates);
  const candidates = selectedTerms.length ? selectedTerms : selectedUnits;
  const parameterCount = arrayCount(hint.metadata.parameter_examples);
  const launchable = Boolean(hint.url) || Boolean(hint.metadata.launchable);
  const copyHintQuery = async () => {
    try {
      await copyTextToClipboard(hint.query);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };
  return (
    <div className="grid gap-1.5 rounded-md border border-border bg-muted/20 px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <Badge variant={launchable ? "success" : "muted"}>
            {launchable ? "launchable" : "syntax"}
          </Badge>
          <Badge variant="muted">{humanize(hint.target)}</Badge>
          {endpointScope.length ? <Badge variant="muted">scoped API</Badge> : null}
          {parameterCount ? <Badge variant="muted">{formatCount(parameterCount, "parameter")}</Badge> : null}
          <span className="min-w-0 break-words font-black">{hint.rationale}</span>
        </div>
        {hint.url ? (
          <Button asChild size="sm" type="button" variant="outline">
            <a href={hint.url} rel="noopener noreferrer" target="_blank">
              <ExternalLink className="h-4 w-4" />
              Open
            </a>
          </Button>
        ) : null}
        <Button onClick={() => void copyHintQuery()} size="sm" type="button" variant="outline">
          {copied ? <CheckCircle2 className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      {candidates.length ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {candidates.slice(0, 5).map((candidate) => (
            <Badge key={candidate} variant="success">
              {candidate}
            </Badge>
          ))}
        </div>
      ) : null}
      <code className="max-h-20 overflow-auto break-words rounded border border-border bg-card px-2 py-1.5 font-mono leading-5">
        {hint.query}
      </code>
      {hint.warnings.length ? (
        <div className="grid gap-1 rounded border border-amber-200 bg-amber-50 px-2 py-1.5 text-amber-950">
          {hint.warnings.slice(0, 2).map((warning) => (
            <span className="break-words" key={warning}>
              {warning}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function AssistantSourceDiversity({
  diversity,
}: {
  diversity: RetrievalDiversitySummary;
}) {
  const visibleSelections = diversity.selected_hits
    .filter((selection) => selection.evidence_id && selection.source_id)
    .slice(0, 3);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex min-w-0 items-center gap-2 text-xs font-black uppercase text-muted-foreground">
            <Network className="h-4 w-4 shrink-0 text-primary" />
            Source diversity
          </div>
          <div className="mt-1 break-words text-sm leading-6 text-muted-foreground">
            Evidence spread after final retrieval selection. Use this to check whether the answer depends on one repeated source or multiple independent sources.
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
          <Badge variant={diversity.enabled ? "success" : "warning"}>
            {diversity.enabled ? "balanced" : "score order"}
          </Badge>
          <Badge variant="muted">
            {diversity.selected_source_count}/{diversity.candidate_source_count} sources
          </Badge>
          <Badge variant={diversity.duplicate_selected_source_count ? "warning" : "success"}>
            {formatCount(diversity.duplicate_selected_source_count, "duplicate")}
          </Badge>
        </div>
      </div>
      {visibleSelections.length ? (
        <div className="grid gap-1.5">
          {visibleSelections.map((selection) => (
            <div
              className="grid gap-1 rounded-md border border-border bg-muted/20 px-3 py-2 text-xs"
              key={`${selection.selected_rank}:${selection.evidence_id}`}
            >
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-1.5">
                <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                  <Badge variant="muted">#{selection.selected_rank}</Badge>
                  <span className="min-w-0 break-words font-black">
                    {selection.source_id}
                  </span>
                </div>
                <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
                  <Badge variant="muted">original #{selection.original_rank}</Badge>
                  <Badge variant={selection.redundancy_score > 0 ? "warning" : "success"}>
                    redundancy {selection.redundancy_score.toFixed(2)}
                  </Badge>
                </div>
              </div>
              <div className="break-words leading-5 text-muted-foreground">
                {selection.reason}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function AssistantEvidencePack({
  buckets,
}: {
  buckets: RetrievalEvidenceBucket[];
}) {
  const missingRequired = buckets.filter(
    (bucket) => bucket.required && bucket.hit_count === 0,
  );
  const available = buckets.filter((bucket) => bucket.hit_count > 0);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-xs font-black uppercase text-muted-foreground">
            Evidence pack
          </div>
          <div className="mt-1 text-sm font-semibold">
            {available.length} evidence class{available.length === 1 ? "" : "es"} covered
          </div>
        </div>
        <Badge variant={missingRequired.length ? "warning" : "success"}>
          {missingRequired.length
            ? `${missingRequired.length} required gap${missingRequired.length === 1 ? "" : "s"}`
            : "ready"}
        </Badge>
      </div>
      <div className="grid gap-1.5 sm:grid-cols-2">
        {buckets.map((bucket) => (
          <div
            className="flex min-w-0 items-center justify-between gap-2 rounded-md border border-border bg-card px-2.5 py-2 text-xs"
            key={bucket.bucket_id}
          >
            <div className="min-w-0">
              <div className="truncate font-black">{bucket.label}</div>
              <div className="truncate text-muted-foreground">
                {bucket.required ? "Required" : "Optional"}
                {bucket.source_ids.length ? ` / ${bucket.source_ids[0]}` : ""}
              </div>
            </div>
            <Badge variant={assistantEvidenceBucketVariant(bucket)}>
              {bucket.hit_count}
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}

async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}
