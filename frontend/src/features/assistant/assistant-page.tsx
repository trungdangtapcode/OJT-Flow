import * as React from "react";
import {
  Bot,
  CheckCircle2,
  Loader2,
  Send,
  ShieldAlert,
  TerminalSquare,
} from "lucide-react";

import { PageHeader } from "../../components/layout/page-header";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Label, Textarea } from "../../components/ui/form";
import { Notice } from "../../components/ui/notice";
import { useAssistantChatMutation, useRuntimeConfigQuery, workflowErrorMessage } from "../../lib/server-state";
import { cn, humanize } from "../../lib/utils";
import type {
  AssistantResponse,
  AssistantToolResult,
  AssistantTranscriptItem,
  Evidence,
} from "../../types";

const defaultMessage = "Find trusted evidence for HbA1c CSV rows with missing units.";
const defaultContext = JSON.stringify(
  {
    schema_id: "lab_result_v1",
    fields: ["lab_name", "value", "unit"],
    clinical_domain: "laboratory",
  },
  null,
  2,
);

export function AssistantPage() {
  const runtimeQuery = useRuntimeConfigQuery();
  const assistantMutation = useAssistantChatMutation();
  const [message, setMessage] = React.useState(defaultMessage);
  const [contextText, setContextText] = React.useState(defaultContext);
  const [executeWriteActions, setExecuteWriteActions] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [transcript, setTranscript] = React.useState<AssistantTranscriptItem[]>([]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const cleanMessage = message.trim();
    if (!cleanMessage) {
      setFormError("Enter a command.");
      return;
    }
    const parsedContext = parseContext(contextText);
    if (parsedContext.error) {
      setFormError(parsedContext.error);
      return;
    }
    setFormError(null);
    try {
      const response = await assistantMutation.mutateAsync({
        message: cleanMessage,
        context: parsedContext.value,
        execute_write_actions: executeWriteActions,
      });
      setTranscript((items) => [
        {
          id: crypto.randomUUID(),
          message: cleanMessage,
          context: parsedContext.value,
          response,
        },
        ...items,
      ]);
    } catch (error) {
      setTranscript((items) => [
        {
          id: crypto.randomUUID(),
          message: cleanMessage,
          context: parsedContext.value,
          error: workflowErrorMessage(error),
        },
        ...items,
      ]);
    }
  };

  const llm = runtimeQuery.data?.llm;

  return (
    <div className="grid gap-5">
      <PageHeader
        title="Assistant"
        description="Run governed healthcare data operations from one command."
        action={
          <div className="flex flex-wrap justify-end gap-2">
            <Badge variant={llm?.provider === "openai" ? "success" : "muted"}>
              {llm?.provider === "openai" ? "LLM openai" : "LLM deterministic"}
            </Badge>
            <Badge variant={executeWriteActions ? "warning" : "success"}>
              {executeWriteActions ? "Writes enabled" : "Writes gated"}
            </Badge>
          </div>
        }
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(360px,0.78fr)_minmax(0,1.22fr)]">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border bg-card/70">
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" />
              Command
            </CardTitle>
            <CardDescription>Assistant actions are backed by typed OJTFlow tools.</CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <form className="grid gap-4" onSubmit={(event) => void submit(event)}>
              {formError ? (
                <Notice title="Command blocked" tone="danger">
                  {formError}
                </Notice>
              ) : null}

              <Label>
                Message
                <Textarea
                  className="min-h-24 resize-y"
                  onChange={(event) => setMessage(event.target.value)}
                  value={message}
                />
              </Label>

              <Label>
                Context JSON
                <Textarea
                  className="min-h-48 resize-y font-mono text-xs"
                  onChange={(event) => setContextText(event.target.value)}
                  spellCheck={false}
                  value={contextText}
                />
              </Label>

              <label className="flex items-center gap-2 rounded-md border border-border bg-muted/35 px-3 py-2 text-sm font-semibold">
                <input
                  checked={executeWriteActions}
                  className="h-4 w-4 accent-primary"
                  onChange={(event) => setExecuteWriteActions(event.target.checked)}
                  type="checkbox"
                />
                Execute write actions
              </label>

              <Button disabled={assistantMutation.isPending} type="submit">
                {assistantMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                Run command
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="grid min-w-0 gap-4">
          {transcript.length === 0 ? (
            <Card className="min-w-0">
              <CardContent className="grid min-h-64 place-items-center p-6 text-center">
                <div className="max-w-md">
                  <TerminalSquare className="mx-auto mb-3 h-9 w-9 text-muted-foreground" />
                  <div className="text-lg font-black">No assistant run yet</div>
                  <div className="mt-1 text-sm leading-6 text-muted-foreground">
                    Submit a command to produce a retrieval, validation, conversion, FHIR,
                    review, or workflow tool result.
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            transcript.map((item) => <TranscriptCard item={item} key={item.id} />)
          )}
        </div>
      </div>
    </div>
  );
}

function TranscriptCard({ item }: { item: AssistantTranscriptItem }) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="truncate text-lg">{item.message}</CardTitle>
            {item.response ? (
              <CardDescription>
                {item.response.mode}
                {item.response.model ? ` / ${item.response.model}` : ""}
              </CardDescription>
            ) : null}
          </div>
          {item.response ? <AssistantStatus response={item.response} /> : null}
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4">
        {item.error ? (
          <Notice title="Assistant request failed" tone="danger">
            {item.error}
          </Notice>
        ) : null}
        {item.response ? (
          <>
            <div className="rounded-md border border-border bg-muted/35 p-3 text-sm font-semibold">
              {item.response.message}
            </div>
            {item.response.warnings.length > 0 ? (
              <Notice title="Warnings">
                {item.response.warnings.join(" ")}
              </Notice>
            ) : null}
            <div className="grid gap-3">
              {item.response.tool_calls.map((call, index) => (
                <ToolResultCard call={call} key={`${call.tool_name}-${index}`} />
              ))}
            </div>
            {item.response.suggestions.length > 0 ? (
              <div className="grid gap-2">
                {item.response.suggestions.map((suggestion) => (
                  <div className="flex items-start gap-2 text-sm text-muted-foreground" key={suggestion}>
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span>{suggestion}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

function AssistantStatus({ response }: { response: AssistantResponse }) {
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
  return (
    <div className="grid gap-3 rounded-md border border-border bg-card p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          {call.status === "requires_approval" ? (
            <ShieldAlert className="h-4 w-4 shrink-0 text-amber-600" />
          ) : (
            <CheckCircle2
              className={cn(
                "h-4 w-4 shrink-0",
                call.status === "completed" ? "text-primary" : "text-muted-foreground",
              )}
            />
          )}
          <div className="truncate text-sm font-black">{humanize(call.tool_name)}</div>
        </div>
        <Badge variant={badgeVariant(call.status)}>{humanize(call.status)}</Badge>
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{call.summary}</p>

      {evidence.length > 0 ? (
        <div className="grid gap-2">
          {evidence.slice(0, 3).map((item) => (
            <div className="rounded-md border border-border bg-muted/35 p-3" key={item.evidence_id}>
              <div className="text-sm font-black">{item.source_id}</div>
              <p className="mt-1 line-clamp-3 text-sm leading-6 text-muted-foreground">
                {item.claim}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <pre className="max-h-72 overflow-auto rounded-md bg-muted p-3 text-xs leading-5 text-muted-foreground">
          {previewJson(call.output)}
        </pre>
      )}
    </div>
  );
}

function parseContext(value: string): { value: Record<string, unknown>; error?: never } | { value: Record<string, unknown>; error: string } {
  if (!value.trim()) return { value: {} };
  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return { value: parsed as Record<string, unknown> };
    }
    return { value: {}, error: "Context JSON must be an object." };
  } catch (error) {
    return {
      value: {},
      error: error instanceof Error ? error.message : "Context JSON is invalid.",
    };
  }
}

function toolEvidence(call: AssistantToolResult): Evidence[] {
  const evidence = call.output.evidence;
  return Array.isArray(evidence) ? (evidence as Evidence[]) : [];
}

function previewJson(value: Record<string, unknown>) {
  const json = JSON.stringify(value, null, 2);
  return json.length > 5000 ? `${json.slice(0, 5000)}\n...` : json;
}

function badgeVariant(status: AssistantToolResult["status"]) {
  if (status === "completed") return "success";
  if (status === "failed") return "destructive";
  if (status === "requires_approval") return "warning";
  return "muted";
}
