import * as React from "react";
import {
  Bot,
  FileText,
  Loader2,
  Paperclip,
  Plus,
  PlayCircle,
  RotateCcw,
  Send,
  Settings2,
  Square,
  UserRound,
  X,
} from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/form";
import { Notice } from "../../components/ui/notice";
import {
  useAppendAssistantSessionMessageMutation,
  useAssistantSessionQuery,
  useAssistantSessionsQuery,
  useAssistantChatStreamMutation,
  useAssistantMemoryPolicyQuery,
  useAssistantMemoryQuery,
  useClipboardImageParseJobMutation,
  useAssistantExamplesQuery,
  useAssistantToolsQuery,
  useCreateAssistantSessionMutation,
  useDeleteAssistantSessionMutation,
  useExtractorInventoryQuery,
  useExtractFileTextMutation,
  useDeleteAssistantMemoryMutation,
  useRuntimeConfigQuery,
  useUpsertAssistantMemoryMutation,
  workflowErrorMessage,
} from "../../lib/server-state";
import type {
  AssistantResponse,
  AssistantStreamEvent,
  AssistantToolResult,
  AssistantTranscriptItem,
  ExtractedDocument,
} from "../../types";
import { cn } from "../../lib/utils";
import {
  assistantContextFromSearchParams,
  assistantContextWithAttachments,
  attachmentSummariesFromContext,
  filesFromClipboard,
  formatContext,
  fileToBase64,
  parseContext,
  selectedContextsFromContext,
  textSnippetsFromContext,
  validateAssistantAttachments,
} from "./assistant-attachments";
import type {
  AssistantSelectedContext,
  AssistantSelectedAttachment,
  AssistantTextSnippet,
} from "./assistant-attachments";
import { formatCount } from "./assistant-format";
import { ChatEmptyState } from "./assistant-empty-state";
import {
  AssistantControlsPanel,
  AttachmentCapabilityBadge,
  AttachmentPreview,
} from "./assistant-input-panels";
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
import type {
  AssistantMappingDraft,
  AssistantReviewTaskDraft,
} from "./assistant-response-model";
import { AssistantSessionSidebar } from "./assistant-session-sidebar";
import { ToolCatalogPanel } from "./assistant-tool-catalog-panel";

export function AssistantPage() {
  const runtimeQuery = useRuntimeConfigQuery();
  const toolsQuery = useAssistantToolsQuery();
  const examplesQuery = useAssistantExamplesQuery();
  const memoryPolicyQuery = useAssistantMemoryPolicyQuery();
  const memoryQuery = useAssistantMemoryQuery();
  const extractorsQuery = useExtractorInventoryQuery();
  const assistantMutation = useAssistantChatStreamMutation();
  const clipboardParseMutation = useClipboardImageParseJobMutation();
  const extractMutation = useExtractFileTextMutation();
  const createSessionMutation = useCreateAssistantSessionMutation();
  const deleteSessionMutation = useDeleteAssistantSessionMutation();
  const upsertMemoryMutation = useUpsertAssistantMemoryMutation();
  const deleteMemoryMutation = useDeleteAssistantMemoryMutation();
  const appendSessionMessageMutation = useAppendAssistantSessionMessageMutation();
  const [message, setMessage] = React.useState("");
  const [contextText, setContextText] = React.useState("");
  const [selectedAttachments, setSelectedAttachments] = React.useState<
    AssistantSelectedAttachment[]
  >([]);
  const [snippetDraft, setSnippetDraft] = React.useState("");
  const [snippetLabel, setSnippetLabel] = React.useState("Text snippet");
  const [textSnippets, setTextSnippets] = React.useState<AssistantTextSnippet[]>([]);
  const [isDraggingFile, setIsDraggingFile] = React.useState(false);
  const [executeWriteActions, setExecuteWriteActions] = React.useState(false);
  const [writeConfirmationAccepted, setWriteConfirmationAccepted] =
    React.useState(false);
  const [memoryMutationKey, setMemoryMutationKey] = React.useState<string | null>(null);
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

  React.useEffect(() => {
    const selectedContext = assistantContextFromSearchParams(
      new URLSearchParams(window.location.search),
    );
    if (!selectedContext) return;
    setMessage((current) => current || selectedContext.message);
    setContextText((current) => {
      const parsed = parseContext(current);
      const base = parsed.error ? {} : parsed.value;
      return formatContext({ ...base, ...selectedContext.context });
    });
    window.history.replaceState({}, document.title, window.location.pathname);
  }, []);

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
  const selectedFiles = selectedAttachments.map((attachment) => attachment.file);
  const parsedComposerContext = React.useMemo(() => parseContext(contextText), [contextText]);
  const selectedContexts = React.useMemo(
    () => (parsedComposerContext.error ? [] : selectedContextsFromContext(parsedComposerContext.value)),
    [parsedComposerContext],
  );
  const existingContextSnippets = React.useMemo(
    () => (parsedComposerContext.error ? [] : textSnippetsFromContext(parsedComposerContext.value)),
    [parsedComposerContext],
  );
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
  const writeGatedTools = React.useMemo(
    () => (toolsQuery.data ?? []).filter((tool) => tool.requires_approval),
    [toolsQuery.data],
  );
  const writeConfirmationRequired =
    executeWriteActions && !writeConfirmationAccepted;
  const uploadExtensionHint = uploadExtensions.length
    ? `${uploadExtensions.slice(0, 8).join(", ")}${
        uploadExtensions.length > 8 ? ", ..." : ""
      }`
    : "configured file types";

  const addAttachmentsFromFiles = React.useCallback(
    (files: File[], source: AssistantSelectedAttachment["source"]) => {
      if (!files.length) return;
      const validationError = validateAssistantAttachments(
        files,
        uploadExtensions,
        maxUploadBytes,
      );
      if (validationError) {
        setFormError(validationError);
        return;
      }
      setSelectedAttachments((current) => [
        ...current,
        ...files.map((file) => ({
          id: crypto.randomUUID(),
          file,
          source,
        })),
      ]);
      setFormError(null);
    },
    [maxUploadBytes, uploadExtensions],
  );

  const removeAttachment = React.useCallback((id: string) => {
    setSelectedAttachments((current) =>
      current.filter((attachment) => attachment.id !== id),
    );
  }, []);

  const addTextSnippet = React.useCallback(() => {
    const text = snippetDraft.trim();
    if (!text) {
      setFormError("Text snippet is empty.");
      return;
    }
    const label = snippetLabel.trim() || "Text snippet";
    setTextSnippets((current) => [
      ...current,
      {
        snippet_id: `snippet_${crypto.randomUUID()}`,
        label,
        text,
        char_count: text.length,
        source: "manual",
      },
    ]);
    setSnippetDraft("");
    setSnippetLabel("Text snippet");
    setFormError(null);
  }, [snippetDraft, snippetLabel]);

  const removeTextSnippet = React.useCallback((snippetId: string) => {
    setTextSnippets((current) =>
      current.filter((snippet) => snippet.snippet_id !== snippetId),
    );
  }, []);

  const removeContextTextSnippet = React.useCallback((snippetId: string) => {
    setContextText((current) => {
      const parsed = parseContext(current);
      if (parsed.error) return current;
      const nextSnippets = textSnippetsFromContext(parsed.value).filter(
        (snippet) => snippet.snippet_id !== snippetId,
      );
      return formatContext({
        ...parsed.value,
        text_snippets: nextSnippets.length ? nextSnippets : undefined,
      });
    });
  }, []);

  const removeSelectedContext = React.useCallback((contextId: string) => {
    setContextText((current) => {
      const parsed = parseContext(current);
      if (parsed.error) return current;
      const nextContexts = selectedContextsFromContext(parsed.value).filter(
        (context) => context.context_id !== contextId,
      );
      return formatContext({
        ...parsed.value,
        selected_contexts: nextContexts.length ? nextContexts : undefined,
      });
    });
  }, []);

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
    addAttachmentsFromFiles(Array.from(event.dataTransfer.files), "upload");
  };

  const handleMemoryPreferenceChange = React.useCallback(
    (key: string, value: string | number | boolean) => {
      setMemoryMutationKey(key);
      upsertMemoryMutation.mutate(
        { key, payload: { value, source: "user" } },
        {
          onError: (error) => setFormError(workflowErrorMessage(error)),
          onSettled: () => setMemoryMutationKey(null),
          onSuccess: () => setFormError(null),
        },
      );
    },
    [upsertMemoryMutation],
  );

  const handleMemoryPreferenceDelete = React.useCallback(
    (key: string) => {
      setMemoryMutationKey(key);
      deleteMemoryMutation.mutate(key, {
        onError: (error) => setFormError(workflowErrorMessage(error)),
        onSettled: () => setMemoryMutationKey(null),
        onSuccess: () => setFormError(null),
      });
    },
    [deleteMemoryMutation],
  );

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const cleanMessage = message.trim();
    if (
      !cleanMessage &&
      !selectedAttachments.length &&
      !textSnippets.length &&
      !selectedContexts.length
    ) {
      setFormError("Enter a command.");
      return;
    }
    const parsedContext = parseContext(contextText);
    if (parsedContext.error) {
      setFormError(parsedContext.error);
      return;
    }
    setFormError(null);
    let extractedDocuments: ExtractedDocument[] = [];
    if (selectedAttachments.length) {
      const validationError = validateAssistantAttachments(
        selectedFiles,
        runtimeQuery.data?.upload.allowed_extensions ?? extractorsQuery.data?.supported_extensions ?? [],
        runtimeQuery.data?.upload.max_upload_bytes ?? null,
      );
      if (validationError) {
        setFormError(validationError);
        return;
      }
      try {
        const documents: ExtractedDocument[] = [];
        for (const attachment of selectedAttachments) {
          const file = attachment.file;
          let extractedDocument: ExtractedDocument | null = null;
          if (attachment.source === "clipboard" && file.type.startsWith("image/")) {
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
          documents.push(extractedDocument);
        }
        extractedDocuments = documents;
        const emptyDocument = documents.find((document) => !document.text.trim());
        if (emptyDocument) {
          setFormError(
            `No readable text was extracted from ${emptyDocument.filename}. ` +
              "Open the parse job details or retry with a different extractor.",
          );
          return;
        }
      } catch (error) {
        setFormError(workflowErrorMessage(error));
        return;
      }
    }
    const assistantContext = assistantContextWithAttachments(
      parsedContext.value,
      extractedDocuments,
      textSnippets,
    );
    const defaultAttachmentMessage =
      selectedAttachments.length > 1
        ? `Analyze ${selectedAttachments.length} attached files.`
        : selectedAttachments.length === 1
          ? `Analyze the attached file ${selectedAttachments[0].file.name}.`
          : textSnippets.length > 1
            ? `Analyze ${textSnippets.length} attached text snippets.`
            : textSnippets.length === 1
              ? `Analyze the attached text snippet ${textSnippets[0].label}.`
              : selectedContexts.length > 1
                ? `Analyze ${selectedContexts.length} selected contexts.`
                : selectedContexts.length === 1
                  ? `Analyze the selected ${selectedContexts[0].source} context ${selectedContexts[0].label}.`
                  : "Analyze the provided context.";
    const assistantMessage =
      cleanMessage || defaultAttachmentMessage;
    await runAssistantTurn({
      assistantContext,
      assistantMessage,
      clearComposer: true,
    });
  };

  const runAssistantTurn = async ({
    assistantContext,
    assistantMessage,
    clearComposer = false,
  }: {
    assistantContext: Record<string, unknown>;
    assistantMessage: string;
    clearComposer?: boolean;
  }) => {
    if (isBusy) return;
    if (writeConfirmationRequired) {
      setFormError("Confirm write-gated assistant actions before sending.");
      return;
    }
    setFormError(null);
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
    if (clearComposer) {
      setMessage("");
      setSelectedAttachments([]);
      setTextSnippets([]);
      setSnippetDraft("");
      setSnippetLabel("Text snippet");
    }
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
      if (executeWriteActions) {
        setWriteConfirmationAccepted(false);
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

  const retryFailedTool = async (
    item: AssistantTranscriptItem,
    call: AssistantToolResult,
  ) => {
    await runAssistantTurn({
      assistantMessage: `Retry failed tool call ${call.tool_name}.`,
      assistantContext: {
        ...item.context,
        assistant_recovery: {
          action: "retry_tool",
          tool_name: call.tool_name,
          arguments: call.arguments,
          failed_status: call.status,
          failed_summary: call.summary,
          failed_error: call.error ?? null,
          source_turn_id: item.id,
        },
      },
    });
  };

  const continueAfterFailure = async (item: AssistantTranscriptItem) => {
    const failedToolCalls =
      item.response?.tool_calls
        .filter((call) => call.status === "failed")
        .map((call) => ({
          tool_name: call.tool_name,
          status: call.status,
          summary: call.summary,
          error: call.error ?? null,
        })) ?? [];
    await runAssistantTurn({
      assistantMessage: "Continue without retrying the failed tool call.",
      assistantContext: {
        ...item.context,
        assistant_recovery: {
          action: "continue_after_failure",
          failed_tool_calls: failedToolCalls,
          source_turn_id: item.id,
        },
      },
    });
  };

  const prepareReviewTask = React.useCallback((draft: AssistantReviewTaskDraft) => {
    setMessage(draft.message);
    setContextText(formatContext(draft.context));
    setExecuteWriteActions(true);
    setWriteConfirmationAccepted(false);
    setFormError(null);
  }, []);

  const prepareMappingDraft = React.useCallback((draft: AssistantMappingDraft) => {
    setMessage(draft.message);
    setContextText(formatContext(draft.context));
    setExecuteWriteActions(true);
    setWriteConfirmationAccepted(false);
    setFormError(null);
  }, []);

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
    <div className="grid min-h-0 gap-0 lg:h-[calc(100dvh-6rem)] lg:grid-rows-[auto_minmax(0,1fr)] lg:overflow-hidden">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-3 border-b border-border/60 bg-card/80 px-1 py-2">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold tracking-tight text-foreground">AI Assistant</h1>
          <div className="hidden items-center gap-1.5 text-xs text-muted-foreground sm:flex">
            <Bot className="h-3.5 w-3.5" />
            <span>{llm?.model ?? "unavailable"}</span>
            {llm?.provider ? <span className="text-border">|</span> : null}
            {llm?.provider ? <span>{llm.provider}</span> : null}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={llm?.provider === "openai" ? "success" : "muted"}>
            {llm?.provider === "openai" ? "LLM openai" : "LLM unavailable"}
          </Badge>
          <Badge variant={executeWriteActions ? "warning" : "success"}>
            {executeWriteActions ? "Writes enabled" : "Writes gated"}
          </Badge>
        </div>
      </div>

      <div className="grid min-h-0 gap-3 pt-3 lg:h-full lg:min-h-0 lg:grid-cols-[260px_minmax(0,1fr)]">
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
        <section className="grid min-h-[640px] min-w-0 overflow-hidden rounded-lg border border-border/60 bg-[#f9fafb] shadow-sm lg:min-h-0">
          <div className="flex min-w-0 items-center justify-between gap-3 border-b border-border/40 bg-card/60 px-4 py-1.5">
            <div className="flex min-w-0 items-center gap-2 text-xs font-mono text-muted-foreground">
              <Settings2 className="h-3 w-3 shrink-0" />
              <span className="truncate">{activeToolName}</span>
            </div>
            <Badge variant={isBusy ? "warning" : "muted"} className="text-[11px]">
              {clipboardParseMutation.isPending
                ? "creating artifact"
                : extractMutation.isPending
                ? "extracting"
                : assistantMutation.isPending
                  ? "streaming"
                  : "ready"}
            </Badge>
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
                    <ConversationTurn
                      isBusy={isBusy}
                      item={item}
                      key={item.id}
                      onContinueAfterFailure={(failedItem) =>
                        void continueAfterFailure(failedItem)
                      }
                      onRetryFailedTool={(failedItem, call) =>
                        void retryFailedTool(failedItem, call)
                      }
                      onGenerateMappingDraft={prepareMappingDraft}
                      onCreateReviewTask={prepareReviewTask}
                    />
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
                "border-t border-border/40 bg-card/95 px-4 py-3 transition-colors",
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
                {writeConfirmationRequired ? (
                  <Notice title="Write confirmation required">
                    Open Advanced context and confirm the write-gated tool list
                    before sending this command.
                  </Notice>
                ) : null}
                <div className="grid gap-2">
                  <Textarea
                    aria-label="Message"
                    className="min-h-20 resize-y lg:min-h-20"
                    disabled={isBusy}
                    onChange={(event) => setMessage(event.target.value)}
                    onPaste={(event) => {
                      const files = filesFromClipboard(event.clipboardData);
                      if (!files.length) return;
                      event.preventDefault();
                      addAttachmentsFromFiles(files, "clipboard");
                    }}
                    placeholder="Ask about your data..."
                    value={message}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        event.currentTarget.form?.requestSubmit();
                      }
                    }}
                  />
                  {selectedAttachments.length ||
                  textSnippets.length ||
                  existingContextSnippets.length ||
                  selectedContexts.length ? (
                    <ComposerContextPreview
                      attachments={selectedAttachments}
                      contextSnippets={existingContextSnippets}
                      onRemoveAttachment={removeAttachment}
                      onRemoveContextSnippet={removeContextTextSnippet}
                      onRemoveSelectedContext={removeSelectedContext}
                      onRemoveSnippet={removeTextSnippet}
                      selectedContexts={selectedContexts}
                      snippets={textSnippets}
                    />
                  ) : null}
                  <details className="rounded-md border border-border/40 bg-muted/10 px-3 py-1.5">
                    <summary className="flex cursor-pointer list-none items-center gap-2 text-xs font-semibold text-muted-foreground">
                      <Plus className="h-3.5 w-3.5 text-primary" />
                      Add text snippet
                    </summary>
                    <div className="mt-3 grid gap-2">
                      <input
                        className="min-h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                        disabled={isBusy}
                        onChange={(event) => setSnippetLabel(event.target.value)}
                        placeholder="Snippet label"
                        value={snippetLabel}
                      />
                      <Textarea
                        className="min-h-24 resize-y"
                        disabled={isBusy}
                        onChange={(event) => setSnippetDraft(event.target.value)}
                        placeholder="Paste a log, table fragment, note, or exact text you want the assistant to analyze."
                        value={snippetDraft}
                      />
                      <Button
                        className="w-fit"
                        disabled={isBusy || !snippetDraft.trim()}
                        onClick={addTextSnippet}
                        type="button"
                        variant="outline"
                      >
                        <FileText className="h-4 w-4" />
                        Add snippet
                      </Button>
                    </div>
                  </details>
                  <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                    <div className="flex min-w-0 max-w-full flex-wrap items-center gap-1.5">
                      <input
                        accept={acceptedUploadExtensions}
                        className="hidden"
                        disabled={isBusy}
                        onChange={(event) => {
                          addAttachmentsFromFiles(
                            Array.from(event.target.files ?? []),
                            "upload",
                          );
                          event.target.value = "";
                        }}
                        multiple
                        ref={fileInputRef}
                        type="file"
                      />
                      <Button
                        disabled={isBusy}
                        onClick={() => fileInputRef.current?.click()}
                        type="button"
                        variant="outline"
                        size="sm"
                      >
                        <Paperclip className="h-3.5 w-3.5" />
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
                        isMemoryUpdating={
                          upsertMemoryMutation.isPending || deleteMemoryMutation.isPending
                        }
                        memoryMutationKey={memoryMutationKey}
                        memoryPolicy={memoryPolicyQuery.data}
                        memorySnapshot={memoryQuery.data}
                        onContextTextChange={setContextText}
                        onExecuteWriteActionsChange={setExecuteWriteActions}
                        onMemoryPreferenceChange={handleMemoryPreferenceChange}
                        onMemoryPreferenceDelete={handleMemoryPreferenceDelete}
                        onWriteConfirmationAcceptedChange={
                          setWriteConfirmationAccepted
                        }
                        writeConfirmationAccepted={writeConfirmationAccepted}
                        writeGatedTools={writeGatedTools}
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
                          className="min-h-9"
                          onClick={cancelActiveStream}
                          type="button"
                          variant="outline"
                          size="sm"
                        >
                          <Square className="h-3.5 w-3.5" />
                          Stop
                        </Button>
                      ) : null}
                      <Button
                        className="min-h-9 min-w-28"
                        disabled={isBusy || writeConfirmationRequired}
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

function ComposerContextPreview({
  attachments,
  contextSnippets,
  onRemoveAttachment,
  onRemoveContextSnippet,
  onRemoveSelectedContext,
  onRemoveSnippet,
  selectedContexts,
  snippets,
}: {
  attachments: AssistantSelectedAttachment[];
  contextSnippets: AssistantTextSnippet[];
  onRemoveAttachment: (id: string) => void;
  onRemoveContextSnippet: (snippetId: string) => void;
  onRemoveSelectedContext: (contextId: string) => void;
  onRemoveSnippet: (snippetId: string) => void;
  selectedContexts: AssistantSelectedContext[];
  snippets: AssistantTextSnippet[];
}) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Context for next message
        </div>
        <Badge variant="muted">
          {formatCount(
            attachments.length +
              snippets.length +
              contextSnippets.length +
              selectedContexts.length,
            "item",
          )}
        </Badge>
      </div>

      {selectedContexts.length ? (
        <div className="grid gap-1.5">
          {selectedContexts.map((context) => (
            <div
              className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-card px-3 py-2 text-sm"
              key={context.context_id}
            >
              <div className="min-w-0">
                <div className="flex min-w-0 flex-wrap items-center gap-2">
                  <Badge variant="success">{context.source}</Badge>
                  <span className="break-words font-black">{context.label}</span>
                </div>
                {context.summary ? (
                  <div className="mt-1 break-words text-xs font-semibold text-muted-foreground">
                    {context.summary}
                  </div>
                ) : null}
              </div>
              <Button
                aria-label={`Remove ${context.label} context`}
                onClick={() => onRemoveSelectedContext(context.context_id)}
                size="sm"
                type="button"
                variant="ghost"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      ) : null}

      {attachments.map((attachment) => (
        <AttachmentPreview
          file={attachment.file}
          key={attachment.id}
          onRemove={() => onRemoveAttachment(attachment.id)}
          source={attachment.source}
        />
      ))}

      {[...contextSnippets, ...snippets].map((snippet) => {
        const isContextSnippet = contextSnippets.some(
          (candidate) => candidate.snippet_id === snippet.snippet_id,
        );
        return (
          <div
            className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-card px-3 py-2 text-sm"
            key={`${isContextSnippet ? "context" : "draft"}-${snippet.snippet_id}`}
          >
            <div className="min-w-0">
              <div className="flex min-w-0 flex-wrap items-center gap-2">
                <FileText className="h-4 w-4 shrink-0 text-primary" />
                <span className="break-words font-black">{snippet.label}</span>
                <Badge variant={isContextSnippet ? "muted" : "success"}>
                  {isContextSnippet ? "context JSON" : "draft"}
                </Badge>
              </div>
              <div className="mt-1 text-xs font-semibold text-muted-foreground">
                {formatCount(snippet.char_count, "char")}
              </div>
            </div>
            <Button
              aria-label={`Remove ${snippet.label} snippet`}
              onClick={() =>
                isContextSnippet
                  ? onRemoveContextSnippet(snippet.snippet_id)
                  : onRemoveSnippet(snippet.snippet_id)
              }
              size="sm"
              type="button"
              variant="ghost"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        );
      })}
    </div>
  );
}

function ConversationTurn({
  isBusy,
  item,
  onContinueAfterFailure,
  onCreateReviewTask,
  onGenerateMappingDraft,
  onRetryFailedTool,
}: {
  isBusy: boolean;
  item: AssistantTranscriptItem;
  onContinueAfterFailure: (item: AssistantTranscriptItem) => void;
  onCreateReviewTask: (draft: AssistantReviewTaskDraft) => void;
  onGenerateMappingDraft: (draft: AssistantMappingDraft) => void;
  onRetryFailedTool: (
    item: AssistantTranscriptItem,
    call: AssistantToolResult,
  ) => void;
}) {
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
              <AssistantRecoveryActions
                isBusy={isBusy}
                item={item}
                onContinueAfterFailure={onContinueAfterFailure}
                onRetryFailedTool={onRetryFailedTool}
              />
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
              {item.response ? (
                <AssistantResponseDetails
                  onGenerateMappingDraft={onGenerateMappingDraft}
                  onCreateReviewTask={onCreateReviewTask}
                  response={item.response}
                  turnContext={item.context}
                  turnId={item.id}
                  userMessage={item.message}
                />
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AssistantRecoveryActions({
  isBusy,
  item,
  onContinueAfterFailure,
  onRetryFailedTool,
}: {
  isBusy: boolean;
  item: AssistantTranscriptItem;
  onContinueAfterFailure: (item: AssistantTranscriptItem) => void;
  onRetryFailedTool: (
    item: AssistantTranscriptItem,
    call: AssistantToolResult,
  ) => void;
}) {
  const failedToolCalls =
    item.response?.tool_calls.filter((call) => call.status === "failed") ?? [];
  if (!failedToolCalls.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm">
      <div className="font-black text-amber-950">Recovery actions</div>
      <div className="flex min-w-0 flex-wrap gap-2">
        {failedToolCalls.map((call, index) => (
          <Button
            disabled={isBusy}
            key={`${call.tool_name}-${index}`}
            onClick={() => onRetryFailedTool(item, call)}
            size="sm"
            type="button"
            variant="outline"
          >
            <RotateCcw className="h-4 w-4" />
            Retry {call.tool_name}
          </Button>
        ))}
        <Button
          disabled={isBusy}
          onClick={() => onContinueAfterFailure(item)}
          size="sm"
          type="button"
          variant="outline"
        >
          <PlayCircle className="h-4 w-4" />
          Continue without retry
        </Button>
      </div>
      <div className="text-xs font-semibold leading-5 text-amber-950">
        Retry reuses the original tool arguments. Continue keeps the failed step
        unresolved and avoids another backend tool call.
      </div>
    </div>
  );
}

function PendingAssistantBubble() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-muted/35 px-3 py-2 text-sm font-semibold text-muted-foreground">
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
