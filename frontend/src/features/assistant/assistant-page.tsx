import * as React from "react";
import { Link } from "@tanstack/react-router";
import {
  Bot,
  BookOpen,
  CheckCircle2,
  Clipboard,
  ExternalLink,
  HelpCircle,
  Image,
  Loader2,
  MessageSquareText,
  Network,
  Paperclip,
  Plus,
  Route,
  Send,
  Settings2,
  ShieldAlert,
  Sparkles,
  Square,
  Trash2,
  UserRound,
  X,
} from "lucide-react";

import { PageHeader } from "../../components/layout/page-header";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Label, Textarea } from "../../components/ui/form";
import { HelpTooltip } from "../../components/ui/help-tooltip";
import { Notice } from "../../components/ui/notice";
import {
  useAssistantChatStreamMutation,
  useAssistantExamplesQuery,
  useAssistantToolsQuery,
  useExtractorInventoryQuery,
  useExtractFileTextMutation,
  useRuntimeConfigQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import { cn, humanize } from "../../lib/utils";
import type {
  AssistantEvidenceSummary,
  AssistantExample,
  AssistantFinding,
  AssistantResponse,
  AssistantStreamEvent,
  AssistantToolSpec,
  AssistantToolResult,
  AssistantTranscriptItem,
  ExtractedDocument,
  Evidence,
  RetrievalDiversitySelection,
  RetrievalDiversitySummary,
  RetrievalEvidenceBucket,
  RetrievalStandardSearchPlan,
  RetrievalStandardSearchStep,
} from "../../types";

type AssistantChatSession = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  transcript: AssistantTranscriptItem[];
};

export function AssistantPage() {
  const initialSession = React.useMemo(() => createAssistantChatSession(), []);
  const runtimeQuery = useRuntimeConfigQuery();
  const toolsQuery = useAssistantToolsQuery();
  const examplesQuery = useAssistantExamplesQuery();
  const extractorsQuery = useExtractorInventoryQuery();
  const assistantMutation = useAssistantChatStreamMutation();
  const extractMutation = useExtractFileTextMutation();
  const [message, setMessage] = React.useState("");
  const [contextText, setContextText] = React.useState("");
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [executeWriteActions, setExecuteWriteActions] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [sessions, setSessions] = React.useState<AssistantChatSession[]>([initialSession]);
  const [activeSessionId, setActiveSessionId] = React.useState(initialSession.id);
  const activeStreamRef = React.useRef<AbortController | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const transcriptEndRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(
    () => () => {
      activeStreamRef.current?.abort();
    },
    [],
  );

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const cleanMessage = message.trim();
    if (!cleanMessage && !selectedFile) {
      setFormError("Enter a command.");
      return;
    }
    const parsedContext = parseContext(contextText);
    if (parsedContext.error) {
      setFormError(parsedContext.error);
      return;
    }
    setFormError(null);
    let extractedDocument: ExtractedDocument | null = null;
    if (selectedFile) {
      const validationError = validateAssistantAttachment(
        selectedFile,
        runtimeQuery.data?.upload.allowed_extensions ?? extractorsQuery.data?.supported_extensions ?? [],
        runtimeQuery.data?.upload.max_upload_bytes ?? null,
      );
      if (validationError) {
        setFormError(validationError);
        return;
      }
      try {
        extractedDocument = await extractMutation.mutateAsync({
          file: selectedFile,
          extractor: "auto",
        });
      } catch (error) {
        setFormError(workflowErrorMessage(error));
        return;
      }
    }
    const assistantContext = assistantContextWithAttachment(
      parsedContext.value,
      extractedDocument,
    );
    const assistantMessage =
      cleanMessage || `Analyze the attached file ${selectedFile?.name ?? ""}.`.trim();
    activeStreamRef.current?.abort();
    const abortController = new AbortController();
    activeStreamRef.current = abortController;
    const transcriptId = crypto.randomUUID();
    const targetSessionId = activeSessionId || sessions[0]?.id || createAndSelectSession();
    appendTranscriptItem(targetSessionId, {
      id: transcriptId,
      message: assistantMessage,
      context: assistantContext,
      stream_events: [],
      streamed_answer: "",
    });
    setMessage("");
    setSelectedFile(null);
    try {
      const response = await assistantMutation.mutateAsync({
        payload: {
          message: assistantMessage,
          context: assistantContext,
          execute_write_actions: executeWriteActions,
        },
        signal: abortController.signal,
        onEvent: (streamEvent) => {
          updateTranscriptItem(
            targetSessionId,
            transcriptId,
            (item) => transcriptItemWithStreamEvent(item, streamEvent),
          );
        },
      });
      updateTranscriptItem(
        targetSessionId,
        transcriptId,
        (item) => ({ ...item, response }),
      );
    } catch (error) {
      const errorMessage = abortController.signal.aborted
        ? "Assistant request was cancelled."
        : workflowErrorMessage(error);
      updateTranscriptItem(
        targetSessionId,
        transcriptId,
        (item) => ({ ...item, error: errorMessage }),
      );
    } finally {
      if (activeStreamRef.current === abortController) {
        activeStreamRef.current = null;
      }
    }
  };

  const cancelActiveStream = () => {
    activeStreamRef.current?.abort();
  };

  const createAndSelectSession = () => {
    const session = createAssistantChatSession();
    setSessions((items) => [session, ...items]);
    setActiveSessionId(session.id);
    return session.id;
  };

  const deleteSession = (sessionId: string) => {
    setSessions((items) => {
      const next = items.filter((session) => session.id !== sessionId);
      if (next.length) {
        if (sessionId === activeSessionId) {
          setActiveSessionId(next[0].id);
        }
        return next;
      }
      const replacement = createAssistantChatSession();
      setActiveSessionId(replacement.id);
      return [replacement];
    });
  };

  const appendTranscriptItem = (
    sessionId: string,
    item: AssistantTranscriptItem,
  ) => {
    setSessions((items) =>
      items.map((session) =>
        session.id === sessionId
          ? sessionWithAppendedTranscriptItem(session, item)
          : session,
      ),
    );
  };

  const updateTranscriptItem = (
    sessionId: string,
    transcriptId: string,
    update: (item: AssistantTranscriptItem) => AssistantTranscriptItem,
  ) => {
    setSessions((items) =>
      items.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              updatedAt: new Date().toISOString(),
              transcript: session.transcript.map((item) =>
                item.id === transcriptId ? update(item) : item,
              ),
            }
          : session,
      ),
    );
  };

  const uploadExtensions =
    runtimeQuery.data?.upload.allowed_extensions ?? extractorsQuery.data?.supported_extensions ?? [];
  const acceptedUploadExtensions = uploadExtensions.join(",") || undefined;
  const maxUploadBytes = runtimeQuery.data?.upload.max_upload_bytes ?? null;
  const isBusy = assistantMutation.isPending || extractMutation.isPending;
  const llm = runtimeQuery.data?.llm;
  const activeSession = sessions.find((session) => session.id === activeSessionId) ?? sessions[0];
  const transcript = activeSession?.transcript ?? [];
  const latestTranscriptItem = transcript[transcript.length - 1] ?? null;
  const latestStreamEventCount = latestTranscriptItem?.stream_events?.length ?? 0;
  const activeToolName = assistantActiveToolName(latestTranscriptItem, toolsQuery.data ?? []);

  React.useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ block: "end" });
  }, [activeSessionId, transcript.length, latestStreamEventCount, latestTranscriptItem?.response?.message]);

  return (
    <div className="grid min-h-0 gap-4 lg:h-[calc(100dvh-6rem)] lg:grid-rows-[auto_auto_auto_minmax(0,1fr)] lg:overflow-hidden">
      <PageHeader
        title="AI Assistant"
        description="Ask about your data in natural language. The AI uses OJTFlow tools to validate, convert, retrieve evidence, and explain."
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
      <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-muted-foreground">
        <Bot className="h-3.5 w-3.5" />
        <span>{llm?.model ?? "deterministic assistant"}</span>
        {llm?.provider ? <span>/ {llm.provider}</span> : null}
      </div>
      <AssistantInlineGuide />

      <div className="grid min-h-0 gap-4 lg:h-full lg:min-h-0 lg:grid-cols-[280px_minmax(0,1fr)]">
        <AssistantSessionSidebar
          activeSessionId={activeSession?.id ?? ""}
          onDeleteSession={deleteSession}
          onNewSession={createAndSelectSession}
          onSelectSession={setActiveSessionId}
          sessions={sessions}
        />
        <section className="grid min-h-[640px] min-w-0 overflow-hidden rounded-lg border border-border bg-[#f7f7fb] shadow-sm lg:min-h-0">
          <div className="flex min-w-0 items-center justify-between gap-3 border-b border-border bg-muted/35 px-4 py-2">
            <div className="flex min-w-0 items-center gap-2 rounded-md border border-border bg-card px-3 py-1.5 text-xs font-mono font-semibold text-muted-foreground">
              <Settings2 className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{activeToolName}</span>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Badge variant={isBusy ? "warning" : "muted"}>
                {extractMutation.isPending
                  ? "extracting"
                  : assistantMutation.isPending
                    ? "streaming"
                    : "ready"}
              </Badge>
              <Badge variant={executeWriteActions ? "warning" : "success"}>
                {executeWriteActions ? "writes enabled" : "writes gated"}
              </Badge>
            </div>
          </div>
          <div className="grid min-h-0 grid-rows-[minmax(0,1fr)_auto]">
            <div className="min-h-0 overflow-y-auto overscroll-contain px-4 py-5 sm:px-6">
              {transcript.length === 0 ? (
                <ChatEmptyState
                  error={
                    examplesQuery.isError
                      ? workflowErrorMessage(examplesQuery.error)
                      : null
                  }
                  examples={examplesQuery.data ?? []}
                  isLoading={examplesQuery.isLoading}
                  onSelect={(example) => {
                    setMessage(example.message);
                    setContextText(formatContext(example.context));
                  }}
                />
              ) : (
                <div className="mx-auto grid max-w-7xl gap-5">
                  {transcript.map((item) => (
                    <ConversationTurn item={item} key={item.id} />
                  ))}
                  {assistantMutation.isPending &&
                  !(latestTranscriptItem?.stream_events?.length) ? (
                    <PendingAssistantBubble />
                  ) : null}
                  <div ref={transcriptEndRef} />
                </div>
              )}
            </div>

            <form
              className="border-t border-border bg-card/95 p-4"
              onSubmit={(event) => void submit(event)}
            >
              <div className="mx-auto grid max-w-7xl gap-3">
                {formError ? (
                  <Notice title="Message blocked" tone="danger">
                    {formError}
                  </Notice>
                ) : null}
                <div className="grid gap-2">
                  <Textarea
                    aria-label="Message"
                    className="min-h-24 resize-y lg:min-h-28"
                    disabled={isBusy}
                    onChange={(event) => setMessage(event.target.value)}
                    onPaste={(event) => {
                      const file = fileFromClipboard(event.clipboardData);
                      if (!file) return;
                      const validationError = validateAssistantAttachment(
                        file,
                        uploadExtensions,
                        maxUploadBytes,
                      );
                      event.preventDefault();
                      setSelectedFile(file);
                      setFormError(validationError);
                    }}
                    placeholder="Ask about your data. Paste an image, attach a file, Enter to send, Shift+Enter for newline."
                    value={message}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        event.currentTarget.form?.requestSubmit();
                      }
                    }}
                  />
                  {selectedFile ? (
                    <AttachmentPreview
                      file={selectedFile}
                      onRemove={() => setSelectedFile(null)}
                    />
                  ) : null}
                  <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                    <div className="flex min-w-0 max-w-full flex-wrap items-center gap-2">
                      <input
                        accept={acceptedUploadExtensions}
                        className="hidden"
                        disabled={isBusy}
                        onChange={(event) => {
                          const file = event.target.files?.[0] ?? null;
                          const validationError = file
                            ? validateAssistantAttachment(file, uploadExtensions, maxUploadBytes)
                            : null;
                          setSelectedFile(file);
                          setFormError(validationError);
                          event.target.value = "";
                        }}
                        ref={fileInputRef}
                        type="file"
                      />
                      <Button
                        disabled={isBusy}
                        onClick={() => fileInputRef.current?.click()}
                        type="button"
                        variant="outline"
                      >
                        <Paperclip className="h-4 w-4" />
                        Attach
                      </Button>
                      <AttachmentCapabilityBadge
                        availableExtractors={extractorsQuery.data?.available ?? []}
                        isLoading={extractorsQuery.isLoading}
                        supportedExtensions={uploadExtensions}
                      />
                      <AssistantControlsPanel
                        contextText={contextText}
                        executeWriteActions={executeWriteActions}
                        onContextTextChange={setContextText}
                        onExecuteWriteActionsChange={setExecuteWriteActions}
                      />
                      <ToolCatalogPanel
                        error={toolsQuery.isError ? workflowErrorMessage(toolsQuery.error) : null}
                        isLoading={toolsQuery.isLoading}
                        tools={toolsQuery.data ?? []}
                      />
                    </div>
                    <div className="flex min-w-0 shrink-0 flex-wrap items-center gap-2">
                      {assistantMutation.isPending ? (
                        <Button
                          className="min-h-10"
                          onClick={cancelActiveStream}
                          type="button"
                          variant="outline"
                        >
                          <Square className="h-4 w-4" />
                          Stop
                        </Button>
                      ) : null}
                      <Button
                        className="min-h-10 min-w-36"
                        disabled={isBusy}
                        type="submit"
                      >
                        {isBusy ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                        {extractMutation.isPending ? "Parsing" : "Send"}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}

function AssistantSessionSidebar({
  activeSessionId,
  onDeleteSession,
  onNewSession,
  onSelectSession,
  sessions,
}: {
  activeSessionId: string;
  onDeleteSession: (sessionId: string) => void;
  onNewSession: () => void;
  onSelectSession: (sessionId: string) => void;
  sessions: AssistantChatSession[];
}) {
  return (
    <aside className="grid min-h-0 rounded-lg border border-border bg-card shadow-sm lg:h-full lg:grid-rows-[auto_minmax(0,1fr)] lg:overflow-hidden">
      <div className="flex items-center justify-between gap-2 border-b border-border p-3">
        <div>
          <div className="text-sm font-black">Chats</div>
          <div className="text-xs text-muted-foreground">
            {formatCount(sessions.length, "session")}
          </div>
        </div>
        <Button onClick={onNewSession} size="sm" type="button" variant="outline">
          <Plus className="h-4 w-4" />
          New
        </Button>
      </div>
      <div className="grid max-h-72 content-start gap-1 overflow-y-auto overscroll-contain p-2 lg:max-h-none">
        {sessions.map((session) => (
          <div
            className={cn(
              "group grid gap-1 rounded-md border p-2 text-left transition",
              session.id === activeSessionId
                ? "border-primary bg-primary/5"
                : "border-transparent hover:border-border hover:bg-muted/40",
            )}
            key={session.id}
          >
            <button
              className="grid min-w-0 gap-1 text-left focus-ring"
              onClick={() => onSelectSession(session.id)}
              type="button"
            >
              <div className="line-clamp-2 break-words text-sm font-black">
                {session.title}
              </div>
              <div className="flex min-w-0 flex-wrap gap-2 text-[11px] font-semibold text-muted-foreground">
                <span>{formatCount(session.transcript.length, "message")}</span>
                <span>{relativeSessionTime(session.updatedAt)}</span>
              </div>
            </button>
            <div className="flex justify-end">
              <Button
                aria-label={`Delete chat ${session.title}`}
                onClick={() => onDeleteSession(session.id)}
                size="sm"
                type="button"
                variant="ghost"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

function createAssistantChatSession(): AssistantChatSession {
  const now = new Date().toISOString();
  return {
    id: crypto.randomUUID(),
    title: "New chat",
    createdAt: now,
    updatedAt: now,
    transcript: [],
  };
}

function sessionWithAppendedTranscriptItem(
  session: AssistantChatSession,
  item: AssistantTranscriptItem,
): AssistantChatSession {
  const now = new Date().toISOString();
  return {
    ...session,
    title:
      session.transcript.length === 0 && session.title === "New chat"
        ? assistantSessionTitle(item.message)
        : session.title,
    updatedAt: now,
    transcript: [...session.transcript, item],
  };
}

function assistantSessionTitle(message: string) {
  const normalized = message.replace(/\s+/g, " ").trim();
  if (!normalized) return "New chat";
  return normalized.length > 52 ? `${normalized.slice(0, 52)}...` : normalized;
}

function relativeSessionTime(value: string) {
  const timestamp = new Date(value).getTime();
  if (!Number.isFinite(timestamp)) return "just now";
  const elapsedSeconds = Math.max(0, Math.round((Date.now() - timestamp) / 1000));
  if (elapsedSeconds < 60) return "just now";
  const elapsedMinutes = Math.round(elapsedSeconds / 60);
  if (elapsedMinutes < 60) return `${elapsedMinutes}m ago`;
  const elapsedHours = Math.round(elapsedMinutes / 60);
  if (elapsedHours < 24) return `${elapsedHours}h ago`;
  const elapsedDays = Math.round(elapsedHours / 24);
  return `${elapsedDays}d ago`;
}

function ChatEmptyState({
  error,
  examples,
  isLoading,
  onSelect,
}: {
  error: string | null;
  examples: AssistantExample[];
  isLoading: boolean;
  onSelect: (example: AssistantExample) => void;
}) {
  return (
    <div className="mx-auto grid min-h-[420px] max-w-3xl place-items-center">
      <div className="grid w-full gap-5 text-center">
        <div>
          <div className="mx-auto grid h-12 w-12 place-items-center rounded-full border border-border bg-muted">
            <Sparkles className="h-6 w-6 text-primary" />
          </div>
          <div className="mt-3 text-xl font-black">Start with a healthcare data task</div>
          <div className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
            The assistant will call backend tools, return evidence, and flag review gates.
          </div>
        </div>
        {error ? (
          <Notice title="Examples unavailable" tone="danger">
            {error}
          </Notice>
        ) : null}
        {!error && isLoading ? (
          <div className="grid gap-3 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div
                aria-hidden="true"
                className="h-28 rounded-md border border-border bg-muted/35"
                key={index}
              />
            ))}
          </div>
        ) : null}
        {!error && !isLoading && examples.length ? (
          <div className="grid min-w-0 gap-3 text-left sm:grid-cols-3">
            {examples.map((example) => (
              <button
                className="grid min-h-28 min-w-0 gap-2 rounded-md border border-border bg-card p-3 text-left transition hover:border-primary hover:bg-primary/5"
                key={example.example_id}
                onClick={() => onSelect(example)}
                type="button"
              >
                <div className="min-w-0 break-words text-sm font-black">{example.label}</div>
                <div className="min-w-0 break-words text-sm leading-5 text-muted-foreground">
                  {example.description}
                </div>
              </button>
            ))}
          </div>
        ) : null}
        {!error && !isLoading && !examples.length ? (
          <div className="rounded-md border border-border bg-muted/25 p-3 text-sm text-muted-foreground">
            No starter tasks are configured.
          </div>
        ) : null}
      </div>
    </div>
  );
}

function AttachmentPreview({
  file,
  onRemove,
}: {
  file: File;
  onRemove: () => void;
}) {
  const isImage = file.type.startsWith("image/");
  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-muted/30 px-3 py-2 text-sm">
      <div className="flex min-w-0 items-center gap-2">
        {isImage ? (
          <Image className="h-4 w-4 shrink-0 text-primary" />
        ) : (
          <Paperclip className="h-4 w-4 shrink-0 text-primary" />
        )}
        <div className="min-w-0">
          <div className="truncate font-black">{file.name}</div>
          <div className="text-xs text-muted-foreground">
            {file.type || "unknown type"} / {formatBytes(file.size)}
          </div>
        </div>
      </div>
      <Button
        aria-label="Remove attached file"
        onClick={onRemove}
        size="sm"
        type="button"
        variant="ghost"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

function AttachmentCapabilityBadge({
  availableExtractors,
  isLoading,
  supportedExtensions,
}: {
  availableExtractors: string[];
  isLoading: boolean;
  supportedExtensions: string[];
}) {
  const primaryExtractor = availableExtractors[0] ?? null;
  const hasVisionOcr = availableExtractors.includes("openai_vision");
  const imageCapable = supportedExtensions.some((extension) =>
    [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"].includes(extension.toLowerCase()),
  );
  return (
    <span className="flex min-w-0 flex-wrap items-center gap-1.5 text-xs font-semibold text-muted-foreground">
      <Badge variant={availableExtractors.length ? "success" : "warning"}>
        {isLoading
          ? "checking extractors"
          : hasVisionOcr
            ? "vision OCR enabled"
            : primaryExtractor
            ? `${primaryExtractor} parser`
            : "parser unavailable"}
      </Badge>
      {imageCapable ? <Badge variant="muted">image paste</Badge> : null}
      {supportedExtensions.length ? (
        <Badge variant="muted">{formatCount(supportedExtensions.length, "format")}</Badge>
      ) : null}
    </span>
  );
}

function AssistantControlsPanel({
  contextText,
  executeWriteActions,
  onContextTextChange,
  onExecuteWriteActionsChange,
}: {
  contextText: string;
  executeWriteActions: boolean;
  onContextTextChange: (value: string) => void;
  onExecuteWriteActionsChange: (value: boolean) => void;
}) {
  return (
    <details className="group relative">
      <summary className="flex h-10 cursor-pointer list-none items-center gap-2 rounded-md border border-border bg-card px-3 text-sm font-black shadow-sm transition hover:border-primary">
        <Settings2 className="h-4 w-4 text-primary" />
        Advanced context
      </summary>
      <div className="absolute bottom-12 right-0 z-20 hidden w-[min(620px,calc(100vw-2rem))] gap-4 rounded-md border border-border bg-card p-4 shadow-lg group-open:grid">
        <div>
          <div className="text-sm font-black">Advanced context</div>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Context and safety gates for the next message.
          </p>
        </div>
        <label className="flex items-center gap-2 rounded-md border border-border bg-muted/35 px-3 py-2 text-sm font-semibold">
          <input
            checked={executeWriteActions}
            className="h-4 w-4 accent-primary"
            onChange={(event) => onExecuteWriteActionsChange(event.target.checked)}
            type="checkbox"
          />
          Execute write actions
          <HelpTooltip label="Execute write actions help">
            Keep this off for normal questions. Turn it on only when you explicitly want the assistant to run approved write-capable tools.
          </HelpTooltip>
        </label>
        <Label>
          <span className="inline-flex items-center gap-1.5">
            Optional context JSON
            <HelpTooltip label="Optional context JSON help">
              Structured data for the next message. Use this for schema IDs, formats, fields, or payload snippets when the chat text alone is not enough.
            </HelpTooltip>
          </span>
          <Textarea
            className="min-h-48 resize-y font-mono text-xs"
            onChange={(event) => onContextTextChange(event.target.value)}
            spellCheck={false}
            value={contextText}
          />
        </Label>
      </div>
    </details>
  );
}

function transcriptItemWithStreamEvent(
  item: AssistantTranscriptItem,
  streamEvent: AssistantStreamEvent,
): AssistantTranscriptItem {
  const stream_events = [...(item.stream_events ?? []), streamEvent];
  if (streamEvent.type === "answer_delta") {
    return {
      ...item,
      stream_events,
      streamed_answer: `${item.streamed_answer ?? ""}${streamEvent.delta}`,
    };
  }
  if (streamEvent.type === "final") {
    return {
      ...item,
      stream_events,
      response: streamEvent.response,
      streamed_answer: item.streamed_answer || streamEvent.response.message,
    };
  }
  return { ...item, stream_events };
}

function ConversationTurn({ item }: { item: AssistantTranscriptItem }) {
  const attachments = attachmentSummariesFromContext(item.context);
  const hasAssistantActivity = Boolean(
    item.response || item.stream_events?.length || item.error,
  );
  return (
    <div className="grid gap-3">
      <div className="flex justify-end">
        <div className="grid max-w-[min(760px,94%)] gap-1">
          <div className="flex items-center justify-end gap-2 text-xs font-bold uppercase text-muted-foreground">
            <span>You</span>
            <UserRound className="h-3.5 w-3.5" />
          </div>
          <div className="whitespace-pre-wrap rounded-lg border border-teal-700/30 bg-teal-700 px-4 py-3 text-sm font-semibold leading-6 text-white shadow-sm">
            {item.message}
          </div>
          {attachments.length ? (
            <div className="flex justify-end">
              <div className="grid max-w-full gap-1 rounded-md border border-teal-700/20 bg-teal-50 px-3 py-2 text-xs font-semibold text-teal-950">
                {attachments.map((attachment) => (
                  <div className="break-words" key={attachment.filename}>
                    <div>
                      {attachment.filename} / {attachment.source_format} /{" "}
                      {attachment.extractor_used} / {formatCount(attachment.char_count, "char")}
                    </div>
                    {attachment.warnings.length ? (
                      <div className="mt-1 grid gap-1 text-[11px] text-amber-900">
                        {attachment.warnings.map((warning) => (
                          <span key={warning}>Warning: {warning}</span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="flex justify-start">
        <div className="grid max-w-[min(1040px,96%)] grid-cols-[32px_minmax(0,1fr)] gap-3">
          <div className="mt-9 grid h-8 w-8 place-items-center rounded-full border border-teal-200 bg-teal-50 text-teal-800">
            <Bot className="h-4 w-4" />
          </div>
          <div className="grid gap-2">
            <div className="flex flex-wrap items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
              <span>OJTFlow</span>
              {item.response ? <AssistantStatus response={item.response} /> : null}
            </div>
            <div className="grid gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
              {item.error ? (
                <Notice title="Assistant request failed" tone="danger">
                  {item.error}
                </Notice>
              ) : null}
              {!hasAssistantActivity ? (
                <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Working on it
                </div>
              ) : null}
              <LiveToolTimeline
                response={item.response ?? null}
                streamEvents={item.stream_events ?? []}
              />
              {item.response ? <AssistantResponseDetails response={item.response} /> : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function PendingAssistantBubble() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-2 rounded-md border border-border bg-muted/35 px-3 py-2 text-sm font-semibold text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Connecting to assistant stream
      </div>
    </div>
  );
}

function AssistantInlineGuide() {
  return (
    <details className="rounded-md border border-border bg-muted/25 px-4 py-3">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2 text-sm font-black">
        <HelpCircle className="h-4 w-4 text-primary" />
        How to use Assistant
        <Badge variant="muted">guide</Badge>
      </summary>
      <div className="mt-3 grid gap-3 text-sm leading-6 md:grid-cols-3">
        <InlineGuideItem title="1. Ask normally">
          Example: validate this CSV, explain PHI risks, find trusted evidence, or list pending reviews.
        </InlineGuideItem>
        <InlineGuideItem title="2. Attach data when needed">
          Use CSV, JSON, YAML, PDF, DOCX, or image files. Extraction warnings mean the file may need review.
        </InlineGuideItem>
        <InlineGuideItem title="3. Read the timeline">
          LLM text is the explanation. Tool calls are real backend actions. Expand tools only when you need details.
        </InlineGuideItem>
      </div>
      <div className="mt-3">
        <Button asChild size="sm" type="button" variant="outline">
          <Link to="/help">
            <BookOpen className="h-4 w-4" />
            Open full manual
          </Link>
        </Button>
      </div>
    </details>
  );
}

function InlineGuideItem({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <div className="mt-1 text-muted-foreground">{children}</div>
    </div>
  );
}

function LiveToolTimeline({
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

type PlannerStreamPlan = {
  message: string;
  toolCalls: {
    arguments: Record<string, unknown>;
    rationale: string;
    toolName: string;
  }[];
  warnings: string[];
};

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

function planningStartedDetail(
  event: Extract<AssistantStreamEvent, { type: "planning_started" }>,
): string {
  const parts = [
    event.message,
    event.model ? `Model: ${event.model}.` : null,
    typeof event.available_tool_count === "number"
      ? `Tools available: ${event.available_tool_count}.`
      : null,
    typeof event.max_tool_calls === "number" ? `Max tool calls: ${event.max_tool_calls}.` : null,
  ].filter((part): part is string => Boolean(part));
  return parts.join(" ");
}

function formatPlannerStreamText(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) {
    return "Waiting for planner tokens...";
  }
  try {
    const parsed = JSON.parse(trimmed);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return formattedPlannerObject(parsed as Record<string, unknown>);
    }
  } catch {
    return trimmed.length > 4000 ? trimmed.slice(-4000) : trimmed;
  }
  return trimmed.length > 4000 ? trimmed.slice(-4000) : trimmed;
}

function plannerStreamPlan(text: string): PlannerStreamPlan | null {
  const trimmed = text.trim();
  if (!trimmed) return null;
  try {
    const parsed = JSON.parse(trimmed);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
    const record = parsed as Record<string, unknown>;
    const toolCalls = Array.isArray(record.tool_calls) ? record.tool_calls : [];
    const warnings = Array.isArray(record.warnings)
      ? record.warnings.filter((item): item is string => typeof item === "string")
      : [];
    return {
      message: typeof record.message === "string" ? record.message : "",
      toolCalls: toolCalls
        .map(plannerToolCallValue)
        .filter((item): item is PlannerStreamPlan["toolCalls"][number] => item !== null),
      warnings,
    };
  } catch {
    return null;
  }
}

function plannerToolCallValue(value: unknown): PlannerStreamPlan["toolCalls"][number] | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  const toolName = typeof record.tool_name === "string" ? record.tool_name : "";
  if (!toolName) return null;
  return {
    arguments: plannerArgumentsValue(record),
    rationale: typeof record.rationale === "string" ? record.rationale : "",
    toolName,
  };
}

function plannerArgumentsValue(record: Record<string, unknown>): Record<string, unknown> {
  if (record.arguments && typeof record.arguments === "object" && !Array.isArray(record.arguments)) {
    return record.arguments as Record<string, unknown>;
  }
  if (typeof record.arguments_json === "string") {
    try {
      const parsed = JSON.parse(record.arguments_json);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed)
        ? (parsed as Record<string, unknown>)
        : {};
    } catch {
      return { arguments_json: record.arguments_json };
    }
  }
  return {};
}

function plannerArgumentPreview(value: unknown): string {
  if (typeof value === "string") {
    const payload = structuredPayloadPreview(value);
    if (payload) return payload;
    const clean = value.replace(/\s+/g, " ").trim();
    return clean.length > 28 ? `${clean.slice(0, 28)}...` : clean || "empty";
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return formatCount(value.length, "item");
  }
  if (value && typeof value === "object") {
    return formatCount(Object.keys(value).length, "field");
  }
  return "null";
}

function structuredPayloadPreview(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return "empty";
  const lines = trimmed.split(/\r?\n/).filter((line) => line.trim());
  const looksCsv =
    lines.length > 1 &&
    lines[0].includes(",") &&
    lines.slice(1).some((line) => line.includes(","));
  if (looksCsv) {
    return `CSV ${formatCount(Math.max(0, lines.length - 1), "row")}`;
  }
  if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
    try {
      const parsed = JSON.parse(trimmed);
      if (Array.isArray(parsed)) return `JSON ${formatCount(parsed.length, "item")}`;
      if (parsed && typeof parsed === "object") {
        return `JSON ${formatCount(Object.keys(parsed).length, "field")}`;
      }
    } catch {
      return null;
    }
  }
  if (trimmed.length > 120 || lines.length > 3) {
    return `${formatCount(trimmed.length, "char")} payload`;
  }
  return null;
}

function formattedPlannerObject(value: Record<string, unknown>): string {
  const lines: string[] = [];
  const message = typeof value.message === "string" ? value.message.trim() : "";
  if (message) {
    lines.push(`Message: ${message}`);
  }
  const toolCalls = Array.isArray(value.tool_calls) ? value.tool_calls : [];
  if (toolCalls.length) {
    lines.push("Tools:");
    toolCalls.forEach((item, index) => {
      if (!item || typeof item !== "object" || Array.isArray(item)) return;
      const record = item as Record<string, unknown>;
      const toolName = typeof record.tool_name === "string" ? record.tool_name : "tool";
      const rationale =
        typeof record.rationale === "string" && record.rationale.trim()
          ? ` - ${record.rationale.trim()}`
          : "";
      lines.push(`${index + 1}. ${toolName}${rationale}`);
      const args = plannerArgumentsText(record);
      if (args) lines.push(`   args: ${args}`);
    });
  } else {
    lines.push("Tools: none selected yet");
  }
  const warnings = Array.isArray(value.warnings)
    ? value.warnings.filter((item): item is string => typeof item === "string")
    : [];
  if (warnings.length) {
    lines.push("Warnings:");
    warnings.forEach((warning) => lines.push(`- ${warning}`));
  }
  return lines.join("\n");
}

function plannerArgumentsText(record: Record<string, unknown>): string {
  if (record.arguments && typeof record.arguments === "object") {
    return JSON.stringify(record.arguments);
  }
  if (typeof record.arguments_json === "string") {
    try {
      return JSON.stringify(JSON.parse(record.arguments_json));
    } catch {
      return record.arguments_json;
    }
  }
  return "";
}

type LiveToolStep = {
  index: number;
  plan?: Extract<AssistantStreamEvent, { type: "tool_started" }>["tool_call"];
  result?: AssistantToolResult;
};

function liveToolSteps(
  streamEvents: AssistantStreamEvent[],
  response: AssistantResponse | null,
): LiveToolStep[] {
  const steps = new Map<number, LiveToolStep>();
  for (const event of streamEvents) {
    if (event.type === "tool_started") {
      steps.set(event.index, {
        ...(steps.get(event.index) ?? { index: event.index }),
        plan: event.tool_call,
      });
    }
    if (event.type === "tool_completed") {
      steps.set(event.index, {
        ...(steps.get(event.index) ?? { index: event.index }),
        result: event.tool_result,
      });
    }
  }
  if (!steps.size && response) {
    response.tool_calls.forEach((result, index) => {
      steps.set(index + 1, { index: index + 1, result });
    });
  }
  return [...steps.values()].sort((left, right) => left.index - right.index);
}

function completedToolResultByIndex(
  streamEvents: AssistantStreamEvent[],
  response: AssistantResponse | null,
): Map<number, AssistantToolResult> {
  const completed = new Map<number, AssistantToolResult>();
  for (const event of streamEvents) {
    if (event.type === "tool_completed") {
      completed.set(event.index, event.tool_result);
    }
  }
  if (!completed.size && response) {
    response.tool_calls.forEach((result, index) => {
      completed.set(index + 1, result);
    });
  }
  return completed;
}

function assistantActiveToolName(
  latestTranscriptItem: AssistantTranscriptItem | null,
  tools: AssistantToolSpec[],
) {
  const streamEvents = latestTranscriptItem?.stream_events ?? [];
  const latestStarted = [...streamEvents]
    .reverse()
    .find((event): event is Extract<AssistantStreamEvent, { type: "tool_started" }> =>
      event.type === "tool_started",
    );
  if (latestStarted) return latestStarted.tool_call.tool_name;
  const latestCompleted = latestTranscriptItem?.response?.tool_calls.at(-1);
  if (latestCompleted) return latestCompleted.tool_name;
  const retrievalTool = tools.find((tool) => tool.name.includes("retrieval"));
  return retrievalTool?.name ?? tools[0]?.name ?? "governed_tool";
}

function liveStatusBadgeVariant(
  status: AssistantToolResult["status"] | "running" | "warning",
) {
  if (status === "completed") return "success";
  if (status === "failed") return "destructive";
  if (status === "requires_approval" || status === "warning") return "warning";
  return "muted";
}

function AssistantResponseDetails({ response }: { response: AssistantResponse }) {
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
        <EvidenceSummaryPanel evidence={response.evidence_summary} />
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

function ToolCatalogPanel({
  error,
  isLoading,
  tools,
}: {
  error: string | null;
  isLoading: boolean;
  tools: AssistantToolSpec[];
}) {
  return (
    <details className="group relative">
      <summary className="flex h-10 cursor-pointer list-none items-center gap-2 rounded-md border border-border bg-card px-3 text-sm font-black shadow-sm transition hover:border-primary">
        <MessageSquareText className="h-4 w-4 text-primary" />
        Tool catalog
        <HelpTooltip label="Tool catalog help">
          The real backend tools the assistant is allowed to call. Approval badges mean a tool can pause or require human review before changing state.
        </HelpTooltip>
        <Badge variant="muted">{isLoading ? "loading" : `${tools.length}`}</Badge>
      </summary>
      <div className="absolute bottom-12 right-0 z-20 grid max-h-[560px] w-[min(720px,calc(100vw-2rem))] gap-3 overflow-auto rounded-md border border-border bg-card p-4 shadow-lg max-sm:left-0 max-sm:right-auto">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <div className="text-sm font-black">Assistant tool catalog</div>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              Server allowlist used by chat and local MCP clients.
            </p>
          </div>
          <Badge variant="muted">{isLoading ? "loading" : `${tools.length} tools`}</Badge>
        </div>
        {error ? (
          <Notice title="Tool catalog unavailable" tone="danger">
            {error}
          </Notice>
        ) : null}
        {!error && isLoading ? (
          <div className="grid gap-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                aria-hidden="true"
                className="h-16 rounded-md border border-border bg-muted/35"
                key={index}
              />
            ))}
          </div>
        ) : null}
        {!error && !isLoading ? (
          <div className="grid gap-2">
            {tools.map((tool) => (
              <div className="rounded-md border border-border bg-muted/20 p-3" key={tool.name}>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="min-w-0 flex-1 break-words font-mono text-sm font-black">
                    {tool.name}
                  </div>
                  <Badge variant={tool.requires_approval ? "warning" : "success"}>
                    {tool.requires_approval ? "approval" : "read/run"}
                  </Badge>
                  <Badge variant="muted">{humanize(tool.permission_scope)}</Badge>
                </div>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  {tool.description}
                </p>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </details>
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

function EvidenceSummaryPanel({ evidence }: { evidence: AssistantEvidenceSummary[] }) {
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
  const evidenceBuckets = toolEvidenceBuckets(call);
  const standardSearchPlan = toolStandardSearchPlan(call);
  const searchHints = toolSearchHints(call);
  const diversity = toolDiversitySummary(call);
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
            {evidence.slice(0, 3).map((item) => (
              <div className="rounded-md border border-border bg-card p-3" key={item.evidence_id}>
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
    </details>
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

type AssistantSearchHint = {
  metadata: Record<string, unknown>;
  query: string;
  rationale: string;
  target: string;
  url: string | null;
  warnings: string[];
};

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

function assistantStandardSearchMatchReasons(metadata: Record<string, unknown>) {
  const sources: {
    key: string;
    label: string;
    variant: React.ComponentProps<typeof Badge>["variant"];
  }[] = [
    { key: "matched_fields", label: "field", variant: "default" },
    { key: "matched_query_aspects", label: "aspect", variant: "muted" },
    { key: "matched_standards", label: "standard", variant: "success" },
    { key: "matched_concepts", label: "concept", variant: "muted" },
    { key: "source_quality_signal_codes", label: "signal", variant: "warning" },
  ];
  return sources.flatMap((source) =>
    stringArrayValue(metadata[source.key])
      .slice(0, 3)
      .map((value) => ({
        label: source.label,
        value,
        variant: source.variant,
      })),
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

function assistantContextWithAttachment(
  context: Record<string, unknown>,
  document: ExtractedDocument | null,
): Record<string, unknown> {
  if (!document) return context;
  const attachment = {
    filename: document.filename,
    source_format: document.source_format,
    extractor_used: document.extractor_used,
    page_count: document.page_count ?? null,
    char_count: document.char_count,
    word_count: document.word_count,
    warnings: document.warnings,
  };
  return {
    ...context,
    data:
      typeof context.data === "string" && context.data.trim()
        ? context.data
        : document.text,
    input_format:
      typeof context.input_format === "string" && context.input_format.trim()
        ? context.input_format
        : document.source_format,
    attachments: [
      ...attachmentSummariesFromContext(context),
      {
        ...attachment,
        text: document.text,
      },
    ],
  };
}

function attachmentSummariesFromContext(
  context: Record<string, unknown>,
): Array<{
  filename: string;
  source_format: string;
  extractor_used: string;
  char_count: number;
  warnings: string[];
}> {
  const attachments = context.attachments;
  if (!Array.isArray(attachments)) return [];
  return attachments
    .map((item) => {
      if (!item || typeof item !== "object" || Array.isArray(item)) return null;
      const record = item as Record<string, unknown>;
      const filename = typeof record.filename === "string" ? record.filename : "";
      const sourceFormat =
        typeof record.source_format === "string" ? record.source_format : "unknown";
      const extractorUsed =
        typeof record.extractor_used === "string" ? record.extractor_used : "unknown";
      const charCount =
        typeof record.char_count === "number" && Number.isFinite(record.char_count)
          ? record.char_count
          : 0;
      const warnings = Array.isArray(record.warnings)
        ? record.warnings.filter((warning): warning is string => typeof warning === "string")
        : [];
      return filename
        ? {
            filename,
            source_format: sourceFormat,
            extractor_used: extractorUsed,
            char_count: charCount,
            warnings,
          }
        : null;
    })
    .filter(
      (
        item,
      ): item is {
        filename: string;
        source_format: string;
        extractor_used: string;
        char_count: number;
        warnings: string[];
      } => item !== null,
    );
}

function validateAssistantAttachment(
  file: File,
  allowedExtensions: string[],
  maxUploadBytes: number | null,
): string | null {
  if (maxUploadBytes && file.size > maxUploadBytes) {
    return `Attachment is too large: ${formatBytes(file.size)} selected, ${formatBytes(
      maxUploadBytes,
    )} allowed.`;
  }
  const allowed = new Set(
    allowedExtensions
      .map((extension) => extension.trim().toLowerCase())
      .filter(Boolean),
  );
  if (!allowed.size) return null;
  const extension = extensionFromFilename(file.name);
  if (!extension) {
    return "Attachment needs a supported file extension.";
  }
  if (!allowed.has(extension)) {
    return `Unsupported attachment type ${extension}. Supported: ${allowedExtensions.join(", ")}.`;
  }
  return null;
}

function fileFromClipboard(clipboardData: DataTransfer): File | null {
  const fileFromList = Array.from(clipboardData.files).find((file) =>
    Boolean(file.name || file.type),
  );
  if (fileFromList) return fileFromList;
  for (const item of Array.from(clipboardData.items)) {
    if (item.kind !== "file") continue;
    const file = item.getAsFile();
    if (!file) continue;
    if (file.name) return file;
    const extension = extensionFromMimeType(file.type);
    return new File([file], `clipboard-image-${Date.now()}${extension}`, {
      type: file.type,
    });
  }
  return null;
}

function extensionFromMimeType(mimeType: string) {
  if (mimeType === "image/png") return ".png";
  if (mimeType === "image/jpeg") return ".jpg";
  if (mimeType === "image/webp") return ".webp";
  if (mimeType === "image/gif") return ".gif";
  if (mimeType === "image/tiff") return ".tiff";
  return "";
}

function extensionFromFilename(filename: string) {
  const dotIndex = filename.lastIndexOf(".");
  if (dotIndex < 0) return "";
  return filename.slice(dotIndex).toLowerCase();
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatCount(value: number, noun: string) {
  return `${value} ${noun}${value === 1 ? "" : "s"}`;
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

type AssistantEvidenceMatchExplanation = {
  aspectLabels: string[];
  bucketLabels: string[];
  conceptLabels: string[];
  provenanceCount: number;
  rankingSignalCount: number;
  supportStatus: "strong" | "partial" | "weak";
  topScoreDriver: string | null;
};

function assistantEvidenceMatchExplanation(
  item: AssistantEvidenceSummary,
): AssistantEvidenceMatchExplanation | null {
  const explanation = recordValue(item.match_explanation);
  const supportStatus = matchSupportStatusValue(explanation.support_status);
  if (!supportStatus) return null;
  return {
    aspectLabels: stringArrayValue(explanation.aspect_labels).slice(0, 3),
    bucketLabels: stringArrayValue(explanation.bucket_labels).slice(0, 3),
    conceptLabels: stringArrayValue(explanation.concept_labels).slice(0, 3),
    provenanceCount: numberValue(explanation.provenance_count) ?? 0,
    rankingSignalCount: numberValue(explanation.ranking_signal_count) ?? 0,
    supportStatus,
    topScoreDriver: optionalStringValue(explanation.top_score_driver),
  };
}

function matchSupportStatusValue(value: unknown): "strong" | "partial" | "weak" | null {
  return value === "strong" || value === "partial" || value === "weak" ? value : null;
}

function matchSupportBadgeVariant(
  status: "strong" | "partial" | "weak",
): React.ComponentProps<typeof Badge>["variant"] {
  if (status === "strong") return "success";
  if (status === "partial") return "warning";
  return "destructive";
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
    : [];
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatContext(context: Record<string, unknown>) {
  return Object.keys(context).length ? JSON.stringify(context, null, 2) : "";
}

function toolEvidence(call: AssistantToolResult): Evidence[] {
  const evidence = call.output.evidence;
  if (Array.isArray(evidence)) return evidence as Evidence[];
  const retrieval = call.output.retrieval;
  if (retrieval && typeof retrieval === "object" && !Array.isArray(retrieval)) {
    const nested = (retrieval as Record<string, unknown>).evidence;
    if (Array.isArray(nested)) return nested as Evidence[];
  }
  return [];
}

function toolEvidenceBuckets(call: AssistantToolResult): RetrievalEvidenceBucket[] {
  const direct = call.output.evidence_buckets;
  if (Array.isArray(direct)) return direct as RetrievalEvidenceBucket[];
  const retrieval = call.output.retrieval;
  if (retrieval && typeof retrieval === "object" && !Array.isArray(retrieval)) {
    const nested = (retrieval as Record<string, unknown>).evidence_buckets;
    if (Array.isArray(nested)) return nested as RetrievalEvidenceBucket[];
  }
  return [];
}

function toolStandardSearchPlan(call: AssistantToolResult): RetrievalStandardSearchPlan | null {
  const direct = standardSearchPlanValue(call.output.standard_search_plan);
  if (direct) return direct;
  const handoff = recordValue(call.output.handoff_context);
  const handoffPlan = standardSearchPlanValue(handoff.standard_search_plan);
  if (handoffPlan) return handoffPlan;
  const retrieval = recordValue(call.output.retrieval);
  const retrievalPlan = standardSearchPlanValue(retrieval.standard_search_plan);
  if (retrievalPlan) return retrievalPlan;
  const retrievalHandoff = recordValue(retrieval.handoff_context);
  return standardSearchPlanValue(retrievalHandoff.standard_search_plan);
}

function toolSearchHints(call: AssistantToolResult): AssistantSearchHint[] {
  const direct = searchHintsValue(call.output.search_hints);
  if (direct.length) return direct;
  const queryAnalysis = recordValue(call.output.query_analysis);
  const queryAnalysisHints = searchHintsValue(queryAnalysis.search_hints);
  if (queryAnalysisHints.length) return queryAnalysisHints;
  const handoff = recordValue(call.output.handoff_context);
  const handoffAnalysis = recordValue(handoff.query_analysis);
  const handoffHints = searchHintsValue(handoffAnalysis.search_hints);
  if (handoffHints.length) return handoffHints;
  const retrieval = recordValue(call.output.retrieval);
  const retrievalAnalysis = recordValue(retrieval.query_analysis);
  const retrievalAnalysisHints = searchHintsValue(retrievalAnalysis.search_hints);
  if (retrievalAnalysisHints.length) return retrievalAnalysisHints;
  const retrievalHandoff = recordValue(retrieval.handoff_context);
  const retrievalHandoffAnalysis = recordValue(retrievalHandoff.query_analysis);
  return searchHintsValue(retrievalHandoffAnalysis.search_hints);
}

function toolDiversitySummary(call: AssistantToolResult): RetrievalDiversitySummary | null {
  const direct = diversitySummaryValue(call.output.diversity);
  if (direct) return direct;
  const handoff = recordValue(call.output.handoff_context);
  const handoffDiversity = diversitySummaryValue(handoff.diversity);
  if (handoffDiversity) return handoffDiversity;
  const retrieval = recordValue(call.output.retrieval);
  const retrievalDiversity = diversitySummaryValue(retrieval.diversity);
  if (retrievalDiversity) return retrievalDiversity;
  const retrievalHandoff = recordValue(retrieval.handoff_context);
  return diversitySummaryValue(retrievalHandoff.diversity);
}

function diversitySummaryValue(value: unknown): RetrievalDiversitySummary | null {
  const record = recordValue(value);
  const candidateSourceCount = numberValue(record.candidate_source_count);
  const selectedSourceCount = numberValue(record.selected_source_count);
  const duplicateSelectedSourceCount = numberValue(record.duplicate_selected_source_count);
  if (
    candidateSourceCount === null ||
    selectedSourceCount === null ||
    duplicateSelectedSourceCount === null
  ) {
    return null;
  }
  return {
    enabled: Boolean(record.enabled),
    selection_mode: optionalStringValue(record.selection_mode) ?? "score_order",
    lambda_value: numberValue(record.lambda_value) ?? numberValue(record.lambda),
    candidate_source_count: candidateSourceCount,
    selected_source_count: selectedSourceCount,
    duplicate_selected_source_count: duplicateSelectedSourceCount,
    selected_hits: diversitySelectionValues(record.selected_hits),
  };
}

function diversitySelectionValues(value: unknown): RetrievalDiversitySelection[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      evidence_id: optionalStringValue(item.evidence_id) ?? "",
      source_id: optionalStringValue(item.source_id) ?? "",
      selected_rank: numberValue(item.selected_rank) ?? 0,
      original_rank: numberValue(item.original_rank) ?? 0,
      relevance_score: numberValue(item.relevance_score) ?? 0,
      redundancy_score: numberValue(item.redundancy_score) ?? 0,
      selection_score: numberValue(item.selection_score) ?? 0,
      reason: optionalStringValue(item.reason) ?? "Selected retrieval evidence.",
    }))
    .filter((item) => item.evidence_id && item.source_id);
}

function searchHintsValue(value: unknown): AssistantSearchHint[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      metadata: recordValue(item.metadata),
      query: optionalStringValue(item.query) ?? "",
      rationale: optionalStringValue(item.rationale) ?? "Generated by retrieval analysis.",
      target: optionalStringValue(item.target) ?? "",
      url: optionalStringValue(item.url),
      warnings: stringArrayValue(item.warnings),
    }))
    .filter((item) => item.target && item.query);
}

function arrayCount(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}

function standardSearchPlanValue(value: unknown): RetrievalStandardSearchPlan | null {
  const record = recordValue(value);
  const planId = optionalStringValue(record.plan_id);
  const summary = optionalStringValue(record.summary);
  const primaryRoute = optionalStringValue(record.primary_route);
  const rawSteps = Array.isArray(record.steps) ? record.steps : [];
  const steps = rawSteps
    .map(standardSearchStepValue)
    .filter((step): step is RetrievalStandardSearchStep => step !== null);
  if (!planId || !summary || !primaryRoute || !steps.length) {
    return null;
  }
  return {
    plan_id: planId,
    summary,
    primary_route: primaryRoute,
    steps,
    missing_routes: stringArrayValue(record.missing_routes),
    governance_notes: stringArrayValue(record.governance_notes),
    metadata: recordValue(record.metadata),
  };
}

function standardSearchStepValue(value: unknown): RetrievalStandardSearchStep | null {
  const record = recordValue(value);
  const stepId = optionalStringValue(record.step_id);
  const label = optionalStringValue(record.label);
  const standardSystem = optionalStringValue(record.standard_system);
  const routeType = optionalStringValue(record.route_type);
  const query = optionalStringValue(record.query);
  const rationale = optionalStringValue(record.rationale);
  const priority = numberValue(record.priority);
  if (
    !stepId ||
    !label ||
    !standardSystem ||
    !routeType ||
    !query ||
    !rationale ||
    priority === null
  ) {
    return null;
  }
  return {
    step_id: stepId,
    label,
    standard_system: standardSystem,
    route_type: routeType,
    query,
    rationale,
    priority,
    suggested_filters: stringRecordValue(record.suggested_filters),
    governance_notes: stringArrayValue(record.governance_notes),
    metadata: recordValue(record.metadata),
  };
}

function stringRecordValue(value: unknown): Record<string, string> {
  const record = recordValue(value);
  return Object.fromEntries(
    Object.entries(record).filter(
      (entry): entry is [string, string] => typeof entry[1] === "string",
    ),
  );
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

function findingBadgeVariant(severity: AssistantFinding["severity"]) {
  if (severity === "error") return "destructive";
  if (severity === "warning" || severity === "action_required") return "warning";
  return "success";
}

function assistantEvidenceBucketVariant(bucket: RetrievalEvidenceBucket) {
  if (bucket.hit_count > 0) return "success";
  return bucket.required ? "warning" : "muted";
}
