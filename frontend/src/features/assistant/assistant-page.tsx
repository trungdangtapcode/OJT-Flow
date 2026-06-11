import * as React from "react";
import {
  Bot,
  Loader2,
  Paperclip,
  Send,
  Settings2,
  Square,
  UserRound,
} from "lucide-react";

import { PageHeader } from "../../components/layout/page-header";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/form";
import { Notice } from "../../components/ui/notice";
import {
  useAppendAssistantSessionMessageMutation,
  useAssistantSessionQuery,
  useAssistantSessionsQuery,
  useAssistantChatStreamMutation,
  useClipboardImageParseJobMutation,
  useAssistantExamplesQuery,
  useAssistantToolsQuery,
  useCreateAssistantSessionMutation,
  useDeleteAssistantSessionMutation,
  useExtractorInventoryQuery,
  useExtractFileTextMutation,
  useRuntimeConfigQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import type {
  AssistantResponse,
  AssistantStreamEvent,
  AssistantTranscriptItem,
  ExtractedDocument,
} from "../../types";
import { cn } from "../../lib/utils";
import {
  assistantContextWithAttachment,
  attachmentSummariesFromContext,
  fileFromClipboard,
  fileToBase64,
  formatContext,
  parseContext,
  validateAssistantAttachment,
} from "./assistant-attachments";
import type { AssistantSelectedAttachment } from "./assistant-attachments";
import { formatCount } from "./assistant-format";
import { ChatEmptyState } from "./assistant-empty-state";
import {
  AssistantControlsPanel,
  AttachmentCapabilityBadge,
  AttachmentPreview,
} from "./assistant-input-panels";
import { AssistantInlineGuide } from "./assistant-inline-guide";
import { LiveToolTimeline } from "./assistant-live-timeline";
import {
  AssistantResponseDetails,
  AssistantStatus,
} from "./assistant-response-details";
import {
  assistantActiveToolName,
  assistantSessionFromDetail,
  assistantSessionFromSummary,
  sessionWithAppendedTranscriptItem,
  streamedAnswerFromEvents,
  transcriptItemWithStreamEvent,
} from "./assistant-session";
import type { AssistantChatSession } from "./assistant-session";
import { AssistantSessionSidebar } from "./assistant-session-sidebar";
import { ToolCatalogPanel } from "./assistant-tool-catalog-panel";

export function AssistantPage() {
  const runtimeQuery = useRuntimeConfigQuery();
  const toolsQuery = useAssistantToolsQuery();
  const examplesQuery = useAssistantExamplesQuery();
  const extractorsQuery = useExtractorInventoryQuery();
  const assistantMutation = useAssistantChatStreamMutation();
  const clipboardParseMutation = useClipboardImageParseJobMutation();
  const extractMutation = useExtractFileTextMutation();
  const createSessionMutation = useCreateAssistantSessionMutation();
  const deleteSessionMutation = useDeleteAssistantSessionMutation();
  const appendSessionMessageMutation = useAppendAssistantSessionMessageMutation();
  const [message, setMessage] = React.useState("");
  const [contextText, setContextText] = React.useState("");
  const [selectedAttachment, setSelectedAttachment] =
    React.useState<AssistantSelectedAttachment | null>(null);
  const [isDraggingFile, setIsDraggingFile] = React.useState(false);
  const [executeWriteActions, setExecuteWriteActions] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [sessionSearch, setSessionSearch] = React.useState("");
  const deferredSessionSearch = React.useDeferredValue(sessionSearch.trim());
  const sessionsQuery = useAssistantSessionsQuery({
    limit: 100,
    q: deferredSessionSearch || undefined,
  });
  const [sessionDrafts, setSessionDrafts] = React.useState<Record<string, AssistantChatSession>>({});
  const [activeSessionId, setActiveSessionId] = React.useState("");
  const activeStreamRef = React.useRef<AbortController | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const transcriptEndRef = React.useRef<HTMLDivElement | null>(null);
  const activeSessionQuery = useAssistantSessionQuery(activeSessionId || null);

  React.useEffect(
    () => () => {
      activeStreamRef.current?.abort();
    },
    [],
  );

  React.useEffect(() => {
    const firstSessionId = sessionsQuery.data?.[0]?.session_id ?? "";
    if (!activeSessionId && firstSessionId) {
      setActiveSessionId(firstSessionId);
    }
    if (
      activeSessionId &&
      sessionsQuery.data &&
      !deferredSessionSearch &&
      !sessionsQuery.data.some((session) => session.session_id === activeSessionId)
    ) {
      setActiveSessionId(firstSessionId);
    }
  }, [activeSessionId, deferredSessionSearch, sessionsQuery.data]);

  React.useEffect(() => {
    if (!activeSessionQuery.data || assistantMutation.isPending) return;
    setSessionDrafts((drafts) => {
      if (!drafts[activeSessionQuery.data.session.session_id]) return drafts;
      const next = { ...drafts };
      delete next[activeSessionQuery.data.session.session_id];
      return next;
    });
  }, [activeSessionQuery.data, assistantMutation.isPending]);

  const persistedSessions = React.useMemo(
    () => (sessionsQuery.data ?? []).map(assistantSessionFromSummary),
    [sessionsQuery.data],
  );
  const activePersistedSession = React.useMemo(
    () =>
      activeSessionQuery.data
        ? assistantSessionFromDetail(activeSessionQuery.data)
        : null,
    [activeSessionQuery.data],
  );
  const sessions = React.useMemo(() => {
    const persistedWithActive =
      activePersistedSession &&
      !persistedSessions.some((session) => session.id === activePersistedSession.id)
        ? [activePersistedSession, ...persistedSessions]
        : persistedSessions.map((session) =>
            session.id === activePersistedSession?.id
              ? activePersistedSession
              : session,
          );
    const persistedIds = new Set(persistedWithActive.map((session) => session.id));
    const draftOnlySessions = Object.values(sessionDrafts)
      .filter((session) => !persistedIds.has(session.id))
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
    return [
      ...draftOnlySessions,
      ...persistedWithActive.map((session) => sessionDrafts[session.id] ?? session),
    ];
  }, [activePersistedSession, persistedSessions, sessionDrafts]);
  const activeSession =
    sessionDrafts[activeSessionId] ??
    activePersistedSession ??
    sessions.find((session) => session.id === activeSessionId) ??
    sessions[0] ??
    null;
  const transcript = activeSession?.transcript ?? [];
  const latestTranscriptItem = transcript[transcript.length - 1] ?? null;
  const latestStreamEventCount = latestTranscriptItem?.stream_events?.length ?? 0;
  const activeToolName = assistantActiveToolName(latestTranscriptItem, toolsQuery.data ?? []);
  const selectedFile = selectedAttachment?.file ?? null;
  const uploadExtensions =
    runtimeQuery.data?.upload.allowed_extensions ?? extractorsQuery.data?.supported_extensions ?? [];
  const acceptedUploadExtensions = uploadExtensions.join(",") || undefined;
  const maxUploadBytes = runtimeQuery.data?.upload.max_upload_bytes ?? null;
  const isBusy =
    assistantMutation.isPending ||
    clipboardParseMutation.isPending ||
    extractMutation.isPending ||
    createSessionMutation.isPending ||
    deleteSessionMutation.isPending;
  const llm = runtimeQuery.data?.llm;
  const uploadExtensionHint = uploadExtensions.length
    ? `${uploadExtensions.slice(0, 8).join(", ")}${
        uploadExtensions.length > 8 ? ", ..." : ""
      }`
    : "configured file types";

  const setAttachmentFromFile = React.useCallback(
    (file: File | null, source: AssistantSelectedAttachment["source"]) => {
      if (!file) {
        setSelectedAttachment(null);
        setFormError(null);
        return;
      }
      const validationError = validateAssistantAttachment(
        file,
        uploadExtensions,
        maxUploadBytes,
      );
      setSelectedAttachment({ file, source });
      setFormError(validationError);
    },
    [maxUploadBytes, uploadExtensions],
  );

  const handleAttachmentDragOver = (event: React.DragEvent<HTMLFormElement>) => {
    if (isBusy || !Array.from(event.dataTransfer.types).includes("Files")) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setIsDraggingFile(true);
  };

  const handleAttachmentDragLeave = (event: React.DragEvent<HTMLFormElement>) => {
    const nextTarget = event.relatedTarget;
    if (nextTarget instanceof Node && event.currentTarget.contains(nextTarget)) return;
    setIsDraggingFile(false);
  };

  const handleAttachmentDrop = (event: React.DragEvent<HTMLFormElement>) => {
    if (!Array.from(event.dataTransfer.types).includes("Files")) return;
    event.preventDefault();
    setIsDraggingFile(false);
    if (isBusy) return;
    setAttachmentFromFile(event.dataTransfer.files[0] ?? null, "upload");
  };

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
    if (selectedAttachment) {
      const file = selectedAttachment.file;
      const validationError = validateAssistantAttachment(
        file,
        runtimeQuery.data?.upload.allowed_extensions ?? extractorsQuery.data?.supported_extensions ?? [],
        runtimeQuery.data?.upload.max_upload_bytes ?? null,
      );
      if (validationError) {
        setFormError(validationError);
        return;
      }
      try {
        if (selectedAttachment.source === "clipboard" && file.type.startsWith("image/")) {
          const parseJob = await clipboardParseMutation.mutateAsync({
            dataBase64: await fileToBase64(file),
            filename: file.name,
            mimeType: file.type || "image/png",
            extractor: "auto",
            executeNow: true,
          });
          extractedDocument = parseJob.extracted_document ?? null;
        }
        if (!extractedDocument) {
          extractedDocument = await extractMutation.mutateAsync({
            file,
            extractor: "auto",
          });
        }
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
    let targetSessionId = activeSessionId;
    try {
      if (!targetSessionId) {
        const session = await createSessionMutation.mutateAsync({ title: "New chat" });
        targetSessionId = session.session_id;
        setSessionDrafts((drafts) => ({
          ...drafts,
          [session.session_id]: assistantSessionFromSummary(session),
        }));
        setActiveSessionId(targetSessionId);
      }
    } catch (error) {
      setFormError(workflowErrorMessage(error));
      activeStreamRef.current = null;
      return;
    }
    let persistedUserMessageId: string = crypto.randomUUID();
    try {
      const persistedUserMessage = await appendSessionMessageMutation.mutateAsync({
        sessionId: targetSessionId,
        payload: {
          role: "user",
          content: assistantMessage,
          payload: { context: assistantContext },
        },
      });
      persistedUserMessageId = persistedUserMessage.message_id;
    } catch (error) {
      setFormError(workflowErrorMessage(error));
      activeStreamRef.current = null;
      return;
    }
    const transcriptId = persistedUserMessageId;
    const streamEvents: AssistantStreamEvent[] = [];
    appendTranscriptItem(targetSessionId, {
      id: transcriptId,
      message: assistantMessage,
      context: assistantContext,
      stream_events: [],
      streamed_answer: "",
    });
    setMessage("");
    setSelectedAttachment(null);
    try {
      const response = await assistantMutation.mutateAsync({
        payload: {
          message: assistantMessage,
          context: assistantContext,
          execute_write_actions: executeWriteActions,
          session_id: targetSessionId,
        },
        signal: abortController.signal,
        onEvent: (streamEvent) => {
          streamEvents.push(streamEvent);
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
      await appendSessionMessageMutation.mutateAsync({
        sessionId: targetSessionId,
        payload: {
          role: "assistant",
          content: response.message,
          workflow_refs: workflowRefsFromAssistantResponse(response),
          payload: {
            response,
            stream_events: streamEvents,
            streamed_answer: streamedAnswerFromEvents(streamEvents) || response.message,
          },
        },
      });
    } catch (error) {
      const errorMessage = abortController.signal.aborted
        ? "Assistant request was cancelled."
        : workflowErrorMessage(error);
      updateTranscriptItem(
        targetSessionId,
        transcriptId,
        (item) => ({ ...item, error: errorMessage }),
      );
      try {
        await appendSessionMessageMutation.mutateAsync({
          sessionId: targetSessionId,
          payload: {
            role: "assistant",
            content: errorMessage,
            payload: {
              error: errorMessage,
              stream_events: streamEvents,
              streamed_answer: errorMessage,
            },
          },
        });
      } catch {
        // Keep the visible local error; persistence failure is already surfaced by the main UI state.
      }
    } finally {
      if (activeStreamRef.current === abortController) {
        activeStreamRef.current = null;
      }
    }
  };

  const cancelActiveStream = () => {
    activeStreamRef.current?.abort();
  };

  const createAndSelectSession = async () => {
    if (isBusy) return;
    try {
      const session = await createSessionMutation.mutateAsync({ title: "New chat" });
      const draft = assistantSessionFromSummary(session);
      setSessionDrafts((drafts) => ({ ...drafts, [draft.id]: draft }));
      setActiveSessionId(draft.id);
    } catch (error) {
      setFormError(workflowErrorMessage(error));
    }
  };

  const deleteSession = async (sessionId: string) => {
    if (isBusy) return;
    const nextActiveSessionId =
      sessions.find((session) => session.id !== sessionId)?.id ?? "";
    setSessionDrafts((drafts) => {
      if (!drafts[sessionId]) return drafts;
      const next = { ...drafts };
      delete next[sessionId];
      return next;
    });
    if (sessionId === activeSessionId) {
      setActiveSessionId(nextActiveSessionId);
    }
    try {
      await deleteSessionMutation.mutateAsync(sessionId);
    } catch (error) {
      setFormError(workflowErrorMessage(error));
    }
  };

  const appendTranscriptItem = (
    sessionId: string,
    item: AssistantTranscriptItem,
  ) => {
    setSessionDrafts((drafts) => {
      const base =
        drafts[sessionId] ??
        (activePersistedSession?.id === sessionId ? activePersistedSession : null) ??
        persistedSessions.find((session) => session.id === sessionId);
      if (!base) return drafts;
      return {
        ...drafts,
        [sessionId]: sessionWithAppendedTranscriptItem(base, item),
      };
    });
  };

  const updateTranscriptItem = (
    sessionId: string,
    transcriptId: string,
    update: (item: AssistantTranscriptItem) => AssistantTranscriptItem,
  ) => {
    setSessionDrafts((drafts) => {
      const base =
        drafts[sessionId] ??
        (activePersistedSession?.id === sessionId ? activePersistedSession : null) ??
        persistedSessions.find((session) => session.id === sessionId);
      if (!base) return drafts;
      return {
        ...drafts,
        [sessionId]: {
          ...base,
          updatedAt: new Date().toISOString(),
          transcript: base.transcript.map((item) =>
            item.id === transcriptId ? update(item) : item,
          ),
        },
      };
    });
  };

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
          isBusy={isBusy}
          onDeleteSession={(sessionId) => void deleteSession(sessionId)}
          onNewSession={() => void createAndSelectSession()}
          onSelectSession={setActiveSessionId}
          onSearchTextChange={setSessionSearch}
          searchText={sessionSearch}
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
                {clipboardParseMutation.isPending
                  ? "creating artifact"
                  : extractMutation.isPending
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
              className={cn(
                "border-t border-border bg-card/95 p-4 transition-colors",
                isDraggingFile && "bg-primary/5 ring-2 ring-inset ring-primary/50",
              )}
              onDragLeave={handleAttachmentDragLeave}
              onDragOver={handleAttachmentDragOver}
              onDrop={handleAttachmentDrop}
              onSubmit={(event) => void submit(event)}
            >
              <div className="mx-auto grid max-w-7xl gap-3">
                {isDraggingFile ? (
                  <div className="flex items-center gap-2 rounded-md border border-primary/40 bg-primary/10 px-3 py-2 text-sm font-semibold text-primary">
                    <Paperclip className="h-4 w-4 shrink-0" />
                    Drop the file here to attach it to this chat.
                  </div>
                ) : null}
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
                      event.preventDefault();
                      setAttachmentFromFile(file, "clipboard");
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
                      onRemove={() => setSelectedAttachment(null)}
                      source={selectedAttachment?.source ?? "upload"}
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
                          setAttachmentFromFile(file, "upload");
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
                      <div className="min-w-0 text-xs font-semibold text-muted-foreground">
                        Drop files here or attach {uploadExtensionHint}.
                      </div>
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
                        {clipboardParseMutation.isPending
                          ? "Saving paste"
                          : extractMutation.isPending
                            ? "Parsing"
                            : "Send"}
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
                    {attachment.artifact_id ? (
                      <div className="mt-1 truncate font-mono text-[11px] text-teal-800">
                        {attachment.source ?? "artifact"} / {attachment.artifact_id}
                        {attachment.trace_id ? ` / ${attachment.trace_id}` : ""}
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

function workflowRefsFromAssistantResponse(response: AssistantResponse) {
  return workflowRefsFromValue(response);
}

function workflowRefsFromValue(value: unknown, depth = 0): string[] {
  if (depth > 8) return [];
  if (Array.isArray(value)) {
    return uniqueWorkflowRefs(
      value.flatMap((item) => workflowRefsFromValue(item, depth + 1)),
    );
  }
  if (!value || typeof value !== "object") return [];
  const record = value as Record<string, unknown>;
  const refs = Object.entries(record).flatMap(([key, nested]) => {
    if (
      key === "workflow_id" ||
      key === "workflow_ids" ||
      key === "workflow_ref" ||
      key === "workflow_refs"
    ) {
      return workflowRefsFromReferenceValue(nested);
    }
    return workflowRefsFromValue(nested, depth + 1);
  });
  return uniqueWorkflowRefs(refs);
}

function workflowRefsFromReferenceValue(value: unknown) {
  if (typeof value === "string") return [value];
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}

function uniqueWorkflowRefs(values: string[]) {
  return Array.from(new Set(values.map((value) => value.trim()).filter(Boolean)));
}
