import * as React from "react";
import {
  CheckCircle2,
  Loader2,
  MessageSquareText,
  Route,
  ShieldAlert,
} from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { humanize } from "../../lib/utils";
import type {
  AssistantResponse,
  AssistantStreamEvent,
  AssistantToolResult,
} from "../../types";
import { formatCount, previewJson } from "./assistant-format";
import {
  completedToolResultByIndex,
  formatPlannerStreamText,
  plannerArgumentPreview,
  plannerStreamPlan,
  planningStartedDetail,
} from "./assistant-live-timeline-model";
import type { PlannerStreamPlan } from "./assistant-live-timeline-model";
import { liveStatusBadgeVariant } from "./assistant-session";

export function LiveToolTimeline({
  response,
  streamEvents,
}: {
  response: AssistantResponse | null;
  streamEvents: AssistantStreamEvent[];
}) {
  const timelineItems = chronologicalTimelineItems(streamEvents, response);
  if (!timelineItems.length) {
    return null;
  }
  return (
    <div className="grid gap-2">
      <div className="flex items-center gap-2 text-xs font-black uppercase text-muted-foreground">
        <MessageSquareText className="h-4 w-4 text-primary" />
        Live tool calls
      </div>
      <div className="grid gap-2">
        {timelineItems.map((item) => (
          <React.Fragment key={item.key}>{item.node}</React.Fragment>
        ))}
      </div>
    </div>
  );
}

function chronologicalTimelineItems(
  streamEvents: AssistantStreamEvent[],
  response: AssistantResponse | null,
): { key: string; node: React.ReactNode }[] {
  const items: { key: string; node: React.ReactNode }[] = [];
  const completedToolResults = completedToolResultByIndex(streamEvents, response);
  const hasPlanReady = streamEvents.some((event) => event.type === "plan_ready");
  const hasFinal = streamEvents.some((event) => event.type === "final") || Boolean(response);
  let planningDeltas: Extract<AssistantStreamEvent, { type: "planning_delta" }>[] = [];
  let answerDeltas: Extract<AssistantStreamEvent, { type: "answer_delta" }>[] = [];

  const flushPlanningDeltas = (completed: boolean) => {
    if (!planningDeltas.length) return;
    items.push({
      key: `planning-deltas-${items.length}`,
      node: <PlannerStreamPreview completed={completed} deltas={planningDeltas} />,
    });
    planningDeltas = [];
  };
  const flushAnswerDeltas = (completed: boolean) => {
    if (!answerDeltas.length) return;
    items.push({
      key: `answer-deltas-${items.length}`,
      node: <AssistantTextStreamPreview completed={completed} deltas={answerDeltas} />,
    });
    answerDeltas = [];
  };

  streamEvents.forEach((event, index) => {
    if (event.type !== "planning_delta") flushPlanningDeltas(hasPlanReady);
    if (event.type !== "answer_delta") flushAnswerDeltas(hasFinal);

    if (event.type === "stream_opened") {
      items.push({
        key: `stream-opened-${index}`,
        node: (
          <LiveTimelineRow
            detail={event.message}
            label="Stream connected"
            status="completed"
          />
        ),
      });
    } else if (event.type === "planning_started") {
      items.push({
        key: `planning-started-${index}`,
        node: (
          <LiveTimelineRow
            detail={planningStartedDetail(event)}
            label="Planning"
            status={hasPlanReady ? "completed" : "running"}
          />
        ),
      });
    } else if (event.type === "planning_step") {
      items.push({
        key: `planning-step-${event.label}-${index}`,
        node: (
          <LiveTimelineRow
            detail={event.message}
            label={event.label}
            status={hasPlanReady ? "completed" : "running"}
          />
        ),
      });
    } else if (event.type === "planning_delta") {
      planningDeltas = [...planningDeltas, event];
    } else if (event.type === "planning_progress") {
      items.push({
        key: `planning-progress-${event.elapsed_seconds}-${index}`,
        node: (
          <LiveTimelineRow
            detail={event.message}
            label={`Planning ${event.elapsed_seconds}s`}
            status={hasPlanReady ? "completed" : "running"}
          />
        ),
      });
    } else if (event.type === "plan_ready") {
      items.push({
        key: `plan-ready-${index}`,
        node: <PlanReadyPreview event={event} />,
      });
    } else if (event.type === "tool_started") {
      const completed = completedToolResults.get(event.index);
      items.push({
        key: `tool-${event.index}-${index}`,
        node: (
          <ToolTimelineCard
            index={event.index}
            result={completed ?? null}
            toolCall={event.tool_call}
          />
        ),
      });
    } else if (event.type === "tool_completed") {
      if (!streamEvents.some((candidate) => candidate.type === "tool_started" && candidate.index === event.index)) {
        items.push({
          key: `tool-completed-${event.index}-${index}`,
          node: (
            <ToolTimelineCard
              index={event.index}
              result={event.tool_result}
              toolCall={null}
            />
          ),
        });
      }
    } else if (event.type === "synthesis_started") {
      items.push({
        key: `synthesis-started-${index}`,
        node: (
          <LiveTimelineRow
            detail={event.message}
            label="LLM text"
            status={hasFinal ? "completed" : "running"}
          />
        ),
      });
    } else if (event.type === "answer_delta") {
      answerDeltas = [...answerDeltas, event];
    } else if (event.type === "warning") {
      items.push({
        key: `warning-${index}`,
        node: <LiveTimelineRow detail={event.message} label="Warning" status="warning" />,
      });
    } else if (event.type === "error") {
      items.push({
        key: `error-${event.code}-${index}`,
        node: (
          <LiveTimelineRow
            detail={event.message}
            label={humanize(event.code)}
            status="failed"
          />
        ),
      });
    }
  });

  flushPlanningDeltas(hasPlanReady);
  flushAnswerDeltas(hasFinal);
  if (!answerDeltas.length && response && !streamEvents.some((event) => event.type === "answer_delta")) {
    items.push({
      key: "final-answer",
      node: <AssistantFinalTextPreview text={response.message} />,
    });
  }
  return items;
}

function PlannerStreamPreview({
  completed,
  deltas,
}: {
  completed: boolean;
  deltas: Extract<AssistantStreamEvent, { type: "planning_delta" }>[];
}) {
  const text = deltas.map((event) => event.delta).join("");
  const plannerPlan = plannerStreamPlan(text);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      <div className="flex min-w-0 items-start gap-2">
        {completed ? (
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
        ) : (
          <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-primary" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="break-words font-black">Planner stream</span>
            <Badge variant={completed ? "success" : "muted"}>
              {completed ? "validated" : "streaming"}
            </Badge>
          </div>
          {plannerPlan ? (
            <PlannerStructuredPreview plan={plannerPlan} />
          ) : (
            <pre className="mt-2 max-h-36 overflow-auto rounded-md bg-card px-3 py-2 text-[11px] leading-5 text-muted-foreground">
              {formatPlannerStreamText(text)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

function PlannerStructuredPreview({ plan }: { plan: PlannerStreamPlan }) {
  return (
    <div className="mt-2 grid gap-2">
      {plan.message ? (
        <div className="rounded-md border border-border bg-card px-3 py-2 text-sm font-semibold leading-6">
          {plan.message}
        </div>
      ) : null}
      {plan.toolCalls.length ? (
        <div className="grid gap-2">
          {plan.toolCalls.map((toolCall, index) => (
            <div
              className="grid gap-2 rounded-md border border-border bg-card px-3 py-2"
              key={`${toolCall.toolName}-${index}`}
            >
              <div className="flex min-w-0 flex-wrap items-center gap-2">
                <Route className="h-4 w-4 shrink-0 text-primary" />
                <span className="break-words font-mono text-xs font-black">
                  {index + 1}. {toolCall.toolName}
                </span>
              </div>
              {toolCall.rationale ? (
                <div className="break-words text-xs leading-5 text-muted-foreground">
                  {toolCall.rationale}
                </div>
              ) : null}
              <PlannerArgumentSummary arguments={toolCall.arguments} />
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-border bg-card px-3 py-2 text-xs font-semibold text-muted-foreground">
          No backend tool call selected yet.
        </div>
      )}
      {plan.warnings.length ? (
        <div className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950">
          {plan.warnings.map((warning) => (
            <div className="break-words font-semibold" key={warning}>
              {warning}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function PlannerArgumentSummary({ arguments: args }: { arguments: Record<string, unknown> }) {
  const entries = Object.entries(args);
  if (!entries.length) {
    return (
      <div className="rounded-md border border-border bg-muted/35 px-2 py-1.5 text-xs font-semibold text-muted-foreground">
        No arguments
      </div>
    );
  }
  return (
    <details className="rounded-md border border-border bg-muted/20">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-1.5 px-2 py-1.5 text-xs font-black">
        Arguments
        <Badge variant="muted">{formatCount(entries.length, "field")}</Badge>
        {entries.slice(0, 4).map(([key, value]) => (
          <Badge className="max-w-full break-words" key={key} variant="muted">
            {key}: {plannerArgumentPreview(value)}
          </Badge>
        ))}
      </summary>
      <pre className="max-h-40 overflow-auto border-t border-border bg-card px-2 py-1.5 text-[11px] leading-5 text-muted-foreground">
        {previewJson(args)}
      </pre>
    </details>
  );
}

function AssistantTextStreamPreview({
  completed,
  deltas,
}: {
  completed: boolean;
  deltas: Extract<AssistantStreamEvent, { type: "answer_delta" }>[];
}) {
  const text = deltas.map((event) => event.delta).join("").trim();
  return (
    <div className="grid gap-2 rounded-md border border-teal-200 bg-teal-50 px-3 py-3 text-sm">
      <div className="flex min-w-0 items-start gap-2">
        {completed ? (
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-700" />
        ) : (
          <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-teal-700" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-black">LLM text</span>
            <Badge variant={completed ? "success" : "muted"}>
              {completed ? "completed" : "streaming"}
            </Badge>
          </div>
          <div className="mt-2 whitespace-pre-wrap break-words text-sm font-semibold leading-6 text-foreground">
            {text || "Waiting for model text..."}
          </div>
        </div>
      </div>
    </div>
  );
}

function AssistantFinalTextPreview({ text }: { text: string }) {
  return (
    <div className="rounded-md border border-teal-200 bg-teal-50 px-3 py-3">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-sm">
        <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-700" />
        <span className="font-black">LLM text</span>
        <Badge variant="success">completed</Badge>
      </div>
      <div className="whitespace-pre-wrap break-words text-sm font-semibold leading-6">
        {text}
      </div>
    </div>
  );
}

function ToolTimelineCard({
  index,
  result,
  toolCall,
}: {
  index: number;
  result: AssistantToolResult | null;
  toolCall: Extract<AssistantStreamEvent, { type: "tool_started" }>["tool_call"] | null;
}) {
  const name = result?.tool_name ?? toolCall?.tool_name ?? "tool";
  const status = result?.status ?? "running";
  const summary = result?.summary || toolCall?.rationale || "Waiting for backend result.";
  return (
    <details className="group rounded-md border border-border bg-muted/20 text-sm" open={!result}>
      <summary className="flex cursor-pointer list-none flex-wrap items-start gap-2 px-3 py-2">
        {status === "running" ? (
          <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-primary" />
        ) : status === "failed" ? (
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        ) : (
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <span className="break-words font-black">
              Tool {index}: {name}
            </span>
            <Badge variant={liveStatusBadgeVariant(status)}>{humanize(status)}</Badge>
          </div>
          <div className="mt-1 break-words text-xs leading-5 text-muted-foreground">
            {summary}
          </div>
        </div>
      </summary>
      <div className="grid gap-2 border-t border-border px-3 py-2">
        {toolCall ? (
          <div>
            <div className="text-[11px] font-black uppercase text-muted-foreground">
              Arguments
            </div>
            <pre className="mt-1 max-h-28 overflow-auto rounded-md bg-card px-2 py-1.5 text-[11px] leading-5 text-muted-foreground">
              {previewJson(toolCall.arguments)}
            </pre>
          </div>
        ) : null}
        {result ? (
          <div>
            <div className="text-[11px] font-black uppercase text-muted-foreground">
              Result
            </div>
            <pre className="mt-1 max-h-40 overflow-auto rounded-md bg-card px-2 py-1.5 text-[11px] leading-5 text-muted-foreground">
              {previewJson(result.output)}
            </pre>
          </div>
        ) : null}
      </div>
    </details>
  );
}

function PlanReadyPreview({
  event,
}: {
  event: Extract<AssistantStreamEvent, { type: "plan_ready" }>;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      <div className="flex min-w-0 items-start gap-2">
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="break-words font-black">Validated plan</span>
            <Badge variant="success">{humanize(event.mode)}</Badge>
            <Badge variant="muted">{formatCount(event.plan.tool_calls.length, "tool")}</Badge>
          </div>
          {event.plan.message ? (
            <div className="mt-1 break-words text-xs leading-5 text-muted-foreground">
              {event.plan.message}
            </div>
          ) : null}
        </div>
      </div>
      {event.plan.tool_calls.length ? (
        <div className="grid gap-1.5">
          {event.plan.tool_calls.map((toolCall, index) => (
            <div
              className="grid gap-1 rounded-md border border-border bg-card px-3 py-2"
              key={`${toolCall.tool_name}-${index}`}
            >
              <div className="flex min-w-0 flex-wrap items-center gap-2">
                <Route className="h-4 w-4 shrink-0 text-primary" />
                <span className="break-words font-mono text-xs font-black">
                  {index + 1}. {toolCall.tool_name}
                </span>
              </div>
              {toolCall.rationale ? (
                <div className="break-words text-xs leading-5 text-muted-foreground">
                  {toolCall.rationale}
                </div>
              ) : null}
              <pre className="max-h-28 overflow-auto rounded-md bg-muted px-2 py-1.5 text-[11px] leading-5 text-muted-foreground">
                {previewJson(toolCall.arguments)}
              </pre>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-border bg-card px-3 py-2 text-xs font-semibold text-muted-foreground">
          No backend tool call was selected.
        </div>
      )}
    </div>
  );
}

function LiveTimelineRow({
  detail,
  label,
  status,
}: {
  detail: string;
  label: string;
  status: AssistantToolResult["status"] | "running" | "warning";
}) {
  const running = status === "running";
  return (
    <div className="flex min-w-0 items-start gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      {running ? (
        <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-primary" />
      ) : status === "failed" || status === "warning" ? (
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
      ) : (
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
      )}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="break-words font-black">{label}</span>
          <Badge variant={liveStatusBadgeVariant(status)}>{humanize(status)}</Badge>
        </div>
        <div className="mt-1 break-words text-xs leading-5 text-muted-foreground">
          {detail}
        </div>
      </div>
    </div>
  );
}
