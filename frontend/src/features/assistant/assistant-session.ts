import type {
  AssistantChatMessage,
  AssistantChatSessionDetail,
  AssistantChatSessionSummary,
  AssistantResponse,
  AssistantStreamEvent,
  AssistantToolSpec,
  AssistantToolResult,
  AssistantTranscriptItem,
} from "../../types";

export type AssistantChatSession = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  transcript: AssistantTranscriptItem[];
};

export function createAssistantChatSession(): AssistantChatSession {
  const now = new Date().toISOString();
  return {
    id: crypto.randomUUID(),
    title: "New chat",
    createdAt: now,
    updatedAt: now,
    messageCount: 0,
    transcript: [],
  };
}

export function assistantSessionFromSummary(
  summary: AssistantChatSessionSummary,
): AssistantChatSession {
  return {
    id: summary.session_id,
    title: summary.title,
    createdAt: summary.created_at,
    updatedAt: summary.updated_at,
    messageCount: summary.message_count,
    transcript: [],
  };
}

export function assistantSessionFromDetail(
  detail: AssistantChatSessionDetail,
): AssistantChatSession {
  return {
    ...assistantSessionFromSummary(detail.session),
    transcript: transcriptFromPersistedMessages(detail.messages),
  };
}

export function assistantSessionTitle(message: string) {
  const normalized = message.replace(/\s+/g, " ").trim();
  if (!normalized) return "New chat";
  return normalized.length > 52 ? `${normalized.slice(0, 52)}...` : normalized;
}

export function sessionWithAppendedTranscriptItem(
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
    messageCount: session.messageCount + 1,
    transcript: [...session.transcript, item],
  };
}

export function relativeSessionTime(value: string) {
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

export function transcriptItemWithStreamEvent(
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

export function streamedAnswerFromEvents(streamEvents: AssistantStreamEvent[]) {
  const answer = streamEvents
    .filter(
      (event): event is Extract<AssistantStreamEvent, { type: "answer_delta" }> =>
        event.type === "answer_delta",
    )
    .map((event) => event.delta)
    .join("");
  if (answer) return answer;
  const finalEvent = [...streamEvents]
    .reverse()
    .find(
      (event): event is Extract<AssistantStreamEvent, { type: "final" }> =>
        event.type === "final",
    );
  return finalEvent?.response.message ?? "";
}

export function assistantActiveToolName(
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

export function liveStatusBadgeVariant(
  status: AssistantToolResult["status"] | "running" | "warning",
) {
  if (status === "completed") return "success";
  if (status === "failed") return "destructive";
  if (status === "requires_approval" || status === "warning") return "warning";
  return "muted";
}

function transcriptFromPersistedMessages(
  messages: AssistantChatMessage[],
): AssistantTranscriptItem[] {
  const transcript: AssistantTranscriptItem[] = [];
  for (const persistedMessage of messages) {
    if (persistedMessage.payload.artifact_type === "assistant_stream_replay") {
      continue;
    }
    if (persistedMessage.role === "user") {
      transcript.push(userTranscriptItem(persistedMessage));
      continue;
    }
    if (persistedMessage.role === "assistant") {
      const latest = transcript[transcript.length - 1];
      if (latest && !latest.response && !latest.error) {
        transcript[transcript.length - 1] = assistantMessageOnTranscriptItem(
          latest,
          persistedMessage,
        );
      } else {
        transcript.push(assistantOnlyTranscriptItem(persistedMessage));
      }
      continue;
    }
    transcript.push(toolOrSystemTranscriptItem(persistedMessage));
  }
  return transcript;
}

function userTranscriptItem(message: AssistantChatMessage): AssistantTranscriptItem {
  return {
    id: message.message_id,
    message: message.content,
    context: recordPayloadValue(message.payload, "context"),
    stream_events: assistantStreamEventsFromPayload(message.payload),
    streamed_answer: stringPayloadValue(message.payload, "streamed_answer"),
    error: stringPayloadValue(message.payload, "error") || undefined,
  };
}

function assistantMessageOnTranscriptItem(
  item: AssistantTranscriptItem,
  message: AssistantChatMessage,
): AssistantTranscriptItem {
  const response = assistantResponseFromPayload(message.payload);
  return {
    ...item,
    response,
    stream_events: assistantStreamEventsFromPayload(message.payload),
    streamed_answer:
      stringPayloadValue(message.payload, "streamed_answer") ||
      response?.message ||
      message.content,
    error: stringPayloadValue(message.payload, "error") || item.error,
  };
}

function assistantOnlyTranscriptItem(message: AssistantChatMessage): AssistantTranscriptItem {
  return {
    id: message.message_id,
    message: "Assistant response",
    context: {},
    response: assistantResponseFromPayload(message.payload),
    stream_events: assistantStreamEventsFromPayload(message.payload),
    streamed_answer:
      stringPayloadValue(message.payload, "streamed_answer") || message.content,
    error: stringPayloadValue(message.payload, "error") || undefined,
  };
}

function toolOrSystemTranscriptItem(message: AssistantChatMessage): AssistantTranscriptItem {
  return {
    id: message.message_id,
    message: message.content || message.role,
    context: {},
    stream_events: [],
    streamed_answer: message.content,
  };
}

function assistantResponseFromPayload(
  payload: Record<string, unknown>,
): AssistantResponse | undefined {
  const response = payload.response;
  if (response && typeof response === "object") {
    return response as AssistantResponse;
  }
  return undefined;
}

function assistantStreamEventsFromPayload(
  payload: Record<string, unknown>,
): AssistantStreamEvent[] {
  const events = payload.stream_events;
  return Array.isArray(events) ? (events as AssistantStreamEvent[]) : [];
}

function recordPayloadValue(payload: Record<string, unknown>, key: string) {
  const value = payload[key];
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function stringPayloadValue(payload: Record<string, unknown>, key: string) {
  const value = payload[key];
  return typeof value === "string" ? value : "";
}
