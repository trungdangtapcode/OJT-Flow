import type {
  ApiEnvelope,
  AssistantChatPayload,
  AssistantChatMessage,
  AssistantChatSessionDetail,
  AssistantChatSessionSummary,
  AssistantExample,
  AssistantResponse,
  AssistantSessionCreatePayload,
  AssistantSessionMessagePayload,
  AssistantSessionRenamePayload,
  AssistantStreamEvent,
  AssistantStreamReplay,
  AssistantToolSpec,
  AuthLoginResponse,
  AuthSessionResponse,
  BackgroundJob,
  ExtractedDocument,
  ExtractorInventory,
  MigrationDiagnostics,
  OcrEvidenceFieldInput,
  OcrEvidenceResponse,
  RetrievalJudgmentEvaluationPayload,
  RetrievalJudgmentEvaluationResult,
  RetrievalIntegrityReport,
  RetrievalJudgmentPayload,
  RetrievalPackage,
  RetrievalPlan,
  RetrievalRelevanceJudgment,
  RetrievalRelevanceJudgmentSummary,
  RetrievalReindexPayload,
  RetrievalReindexJobPayload,
  RetrievalReindexResult,
  RetrievalSearchPayload,
  RetrievalSearchOptions,
  RetrievalSearchPreset,
  RetrievalSource,
  RetrievalSourceTrustPolicyCatalog,
  RetrievalStrategyCatalog,
  RuntimeAssistantSettingsPayload,
  RuntimeAssistantSettingsUpdate,
  RuntimeConfig,
  RuntimeHealth,
  RuntimeReadiness,
  RuntimeRetrievalSettingsPayload,
  RuntimeRetrievalSettingsUpdate,
  SchemaEntry,
  StartWorkflowPayload,
  UploadParseJobResponse,
  WorkflowEvent,
  WorkflowOutputArtifact,
  WorkflowStats,
  WorkflowSummaryPage,
  WorkflowState,
} from "./types";

const configuredBase = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const API_BASE_URL =
  configuredBase && configuredBase.length > 0
    ? configuredBase.replace(/\/$/, "")
    : "/api/v1";

export const AUTH_SESSION_EXPIRED_EVENT = "ojtflow:auth-session-expired";
export const API_REQUEST_ERROR_EVENT = "ojtflow:api-request-error";

export class ApiRequestError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;
  workflowId: string | null;
  requestId: string | null;
  endpoint: string | null;

  constructor({
    status,
    code,
    message,
    details,
    workflowId = null,
    requestId = null,
    endpoint = null,
  }: {
    status: number;
    code: string;
    message: string;
    details?: Record<string, unknown>;
    workflowId?: string | null;
    requestId?: string | null;
    endpoint?: string | null;
  }) {
    super(`${code}: ${message}`);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
    this.details = details ?? {};
    this.workflowId = workflowId;
    this.requestId = requestId;
    this.endpoint = endpoint;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetchApi(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: requestHeaders(init),
  });
  const envelope = await parseEnvelope<T>(response);
  if (!response.ok || envelope.error) {
    throwApiRequestError(
      response,
      envelope,
      "request_failed",
      `Request failed with status ${response.status}`,
    );
  }
  return envelope.data as T;
}

function requestHeaders(init?: RequestInit): Headers {
  const headers = new Headers(init?.headers);
  if (!headers.has("X-Request-ID")) {
    headers.set("X-Request-ID", newRequestId());
  }
  if (
    init?.body !== undefined &&
    !(init.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

function newRequestId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `web_${crypto.randomUUID()}`;
  }
  return `web_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

function requestIdFromInit(init?: RequestInit): string | null {
  const value = new Headers(init?.headers).get("X-Request-ID");
  return value && value.trim() ? value : null;
}

function responseRequestId(response: Response): string | null {
  const value = response.headers.get("X-Request-ID");
  return value && value.trim() ? value : null;
}

async function fetchApi(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch (error) {
    const apiError = new ApiRequestError({
      status: 0,
      code: "network_error",
      message: "API request could not reach the server.",
      details: {
        reason: error instanceof Error ? error.message : String(error),
      },
      requestId: requestIdFromInit(init),
      endpoint: String(input),
    });
    emitApiRequestError(apiError);
    throw apiError;
  }
}

async function parseEnvelope<T>(response: Response): Promise<ApiEnvelope<T>> {
  const contentType = response.headers.get("content-type") ?? "";
  const body = await response.text();
  if (contentType.includes("application/json")) {
    try {
      return normalizeEnvelope(JSON.parse(body), response, contentType, body);
    } catch (error) {
      return invalidJsonEnvelope(response, contentType, body, error);
    }
  }
  return {
    data: null,
    error: {
      code: response.ok ? "invalid_response" : "http_error",
      message: body || `HTTP ${response.status}`,
      details: {
        status: response.status,
        content_type: contentType || null,
        request_id: responseRequestId(response),
      },
      workflow_id: null,
      request_id: responseRequestId(response),
    },
  };
}

function normalizeEnvelope<T>(
  value: unknown,
  response: Response,
  contentType: string,
  body: string,
): ApiEnvelope<T> {
  if (!isApiEnvelope(value)) {
    return invalidEnvelope(response, contentType, body, "API response envelope is invalid.");
  }
  return value as ApiEnvelope<T>;
}

function isApiEnvelope(value: unknown): value is ApiEnvelope<unknown> {
  if (!isRecord(value)) return false;
  if (!hasOwn(value, "data") || !hasOwn(value, "error")) return false;
  const error = value.error;
  return error === null || isApiError(error);
}

function isApiError(value: unknown): boolean {
  if (!isRecord(value)) return false;
  if (typeof value.code !== "string" || typeof value.message !== "string") return false;
  return value.details === undefined || isRecord(value.details);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOwn(value: Record<string, unknown>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function invalidEnvelope<T>(
  response: Response,
  contentType: string,
  body: string,
  message: string,
): ApiEnvelope<T> {
  return {
    data: null,
    error: {
      code: "invalid_response",
      message,
      details: {
        status: response.status,
        content_type: contentType || null,
        body_length: body.length,
        request_id: responseRequestId(response),
      },
      workflow_id: null,
      request_id: responseRequestId(response),
    },
  };
}

function invalidJsonEnvelope<T>(
  response: Response,
  contentType: string,
  body: string,
  error: unknown,
): ApiEnvelope<T> {
  return {
    data: null,
    error: {
      code: "invalid_response",
      message: "API returned malformed JSON.",
      details: {
        status: response.status,
        content_type: contentType || null,
        body_length: body.length,
        parse_error: error instanceof Error ? error.message : String(error),
        request_id: responseRequestId(response),
      },
      workflow_id: null,
      request_id: responseRequestId(response),
    },
  };
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") ?? "";
  const body = await response.text();
  if (!contentType.includes("application/json")) {
    const error = new ApiRequestError({
      status: response.status,
      code: "invalid_response",
      message: "API returned a non-JSON response.",
      details: {
        status: response.status,
        content_type: contentType || null,
        body_length: body.length,
        request_id: responseRequestId(response),
      },
      requestId: responseRequestId(response),
      endpoint: response.url,
    });
    emitApiRequestError(error);
    throw error;
  }
  try {
    return JSON.parse(body) as T;
  } catch (error) {
    const apiError = new ApiRequestError({
      status: response.status,
      code: "invalid_response",
      message: "API returned malformed JSON.",
      details: {
        status: response.status,
        content_type: contentType || null,
        body_length: body.length,
        parse_error: error instanceof Error ? error.message : String(error),
        request_id: responseRequestId(response),
      },
      requestId: responseRequestId(response),
      endpoint: response.url,
    });
    emitApiRequestError(apiError);
    throw apiError;
  }
}

function queryString(params: Record<string, string | number | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const value = search.toString();
  return value ? `?${value}` : "";
}

function parseAssistantStreamBuffer(buffer: string): {
  events: AssistantStreamEvent[];
  remainder: string;
} {
  const parts = buffer.split(/\r?\n\r?\n/);
  const remainder = parts.pop() ?? "";
  const events = parts
    .map(parseAssistantStreamEvent)
    .filter((event): event is AssistantStreamEvent => event !== null);
  return { events, remainder };
}

function parseAssistantStreamEvent(block: string): AssistantStreamEvent | null {
  const dataLine = block.split(/\r?\n/).find((line) => line.startsWith("data:"));
  if (!dataLine) return null;
  try {
    return JSON.parse(dataLine.slice(5).trim()) as AssistantStreamEvent;
  } catch {
    return null;
  }
}

function requestIdFromStreamEvent(event: AssistantStreamEvent): string | null {
  const value = (event as { request_id?: unknown }).request_id;
  return typeof value === "string" && value.trim() ? value : null;
}

function pathSegment(value: string): string {
  return encodeURIComponent(value);
}

function throwApiRequestError<T>(
  response: Response,
  envelope: ApiEnvelope<T>,
  fallbackCode: string,
  fallbackMessage: string,
): never {
  const error = new ApiRequestError({
    status: response.status,
    code: envelope.error?.code ?? fallbackCode,
    message: envelope.error?.message ?? fallbackMessage,
    details: envelope.error?.details,
    workflowId: envelope.error?.workflow_id ?? null,
    requestId: envelope.error?.request_id ?? responseRequestId(response),
    endpoint: response.url,
  });
  emitApiRequestError(error);
  if (error.status === 401) notifyAuthSessionExpired();
  throw error;
}

function emitApiRequestError(error: ApiRequestError) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent(API_REQUEST_ERROR_EVENT, {
      detail: {
        status: error.status,
        code: error.code,
        message: error.message,
        details: error.details,
        workflowId: error.workflowId,
        requestId: error.requestId,
        endpoint: error.endpoint,
        occurredAt: new Date().toISOString(),
      },
    }),
  );
}

function notifyAuthSessionExpired() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(AUTH_SESSION_EXPIRED_EVENT));
}

export function getGoogleAuthorizationUrl(redirectUri: string): Promise<{
  authorization_url: string;
  state: string;
}> {
  const query = `?redirect_uri=${encodeURIComponent(redirectUri)}`;
  return request(`/auth/google/url${query}`, { headers: {} });
}

export function completeGoogleLogin(
  code: string,
  state: string,
): Promise<AuthLoginResponse> {
  const query = `?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`;
  return request<AuthLoginResponse>(`/auth/google/callback${query}`, { headers: {} });
}

export function getCurrentAuthSession(): Promise<AuthSessionResponse> {
  return request<AuthSessionResponse>("/auth/me");
}

export function logoutCurrentSession(): Promise<{ status: string }> {
  return request<{ status: string }>("/auth/logout", { method: "POST" });
}

export function listWorkflowSummaries(params: {
  status?: string | null;
  q?: string | null;
  page?: number;
  page_size?: number;
  sort?: string;
  direction?: string;
}): Promise<WorkflowSummaryPage> {
  return request<WorkflowSummaryPage>(`/workflows/summary${queryString(params)}`);
}

export function getWorkflowStats(): Promise<WorkflowStats> {
  return request<WorkflowStats>("/workflows/stats");
}

export function getWorkflow(workflowId: string): Promise<WorkflowState> {
  return request<WorkflowState>(`/workflows/${pathSegment(workflowId)}`);
}

export function listWorkflowEvents(workflowId: string): Promise<WorkflowEvent[]> {
  return request<WorkflowEvent[]>(`/workflows/${pathSegment(workflowId)}/events`);
}

export function getWorkflowOutput(workflowId: string): Promise<WorkflowOutputArtifact> {
  return request<WorkflowOutputArtifact>(`/workflows/${pathSegment(workflowId)}/output`);
}

export function createWorkflow(payload: StartWorkflowPayload): Promise<WorkflowState> {
  return request<WorkflowState>("/workflows", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listReviewSummaries(params: {
  status?: string | null;
  q?: string | null;
  page?: number;
  page_size?: number;
  sort?: string;
  direction?: string;
}): Promise<WorkflowSummaryPage> {
  return request<WorkflowSummaryPage>(`/reviews/summary${queryString(params)}`);
}

export function submitReview(
  reviewId: string,
  decision: string,
  payload: Record<string, unknown> = {},
): Promise<WorkflowState> {
  return request<WorkflowState>(`/review/${pathSegment(reviewId)}`, {
    method: "POST",
    body: JSON.stringify({
      decision,
      payload,
    }),
  });
}

export function listSchemas(): Promise<SchemaEntry[]> {
  return request<SchemaEntry[]>("/schemas");
}

export function searchRetrieval(payload: RetrievalSearchPayload): Promise<RetrievalPackage> {
  return request<RetrievalPackage>("/retrieval/search", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function planRetrieval(payload: RetrievalSearchPayload): Promise<RetrievalPlan> {
  return request<RetrievalPlan>("/retrieval/plan", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listRetrievalPresets(): Promise<RetrievalSearchPreset[]> {
  return request<RetrievalSearchPreset[]>("/retrieval/presets");
}

export function getRetrievalSearchOptions(): Promise<RetrievalSearchOptions> {
  return request<RetrievalSearchOptions>("/retrieval/search-options");
}

export function getRetrievalSourcePolicies(): Promise<RetrievalSourceTrustPolicyCatalog> {
  return request<RetrievalSourceTrustPolicyCatalog>("/retrieval/source-policies");
}

export function getRetrievalStrategies(): Promise<RetrievalStrategyCatalog> {
  return request<RetrievalStrategyCatalog>("/retrieval/strategies");
}

export function listRetrievalJudgments(params: {
  query?: string | null;
  run_id?: string | null;
  evidence_id?: string | null;
  limit?: number;
}): Promise<RetrievalRelevanceJudgment[]> {
  return request<RetrievalRelevanceJudgment[]>(
    `/retrieval/judgments${queryString(params)}`,
  );
}

export function getRetrievalJudgmentSummary(params: {
  query?: string | null;
  limit?: number;
}): Promise<RetrievalRelevanceJudgmentSummary> {
  return request<RetrievalRelevanceJudgmentSummary>(
    `/retrieval/judgments/summary${queryString(params)}`,
  );
}

export function evaluateRetrievalJudgments(
  payload: RetrievalJudgmentEvaluationPayload,
): Promise<RetrievalJudgmentEvaluationResult> {
  return request<RetrievalJudgmentEvaluationResult>("/retrieval/judgments/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function upsertRetrievalJudgment(
  payload: RetrievalJudgmentPayload,
): Promise<RetrievalRelevanceJudgment> {
  return request<RetrievalRelevanceJudgment>("/retrieval/judgments", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteRetrievalJudgment(judgmentId: string): Promise<{
  deleted: boolean;
  judgment_id: string;
}> {
  return request(`/retrieval/judgments/${pathSegment(judgmentId)}`, {
    method: "DELETE",
  });
}

export function chatWithAssistant(
  payload: AssistantChatPayload,
): Promise<AssistantResponse> {
  return request<AssistantResponse>("/assistant/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listAssistantSessions(params: {
  include_archived?: boolean;
  limit?: number;
  q?: string;
} = {}): Promise<AssistantChatSessionSummary[]> {
  return request<AssistantChatSessionSummary[]>(
    `/assistant/sessions${queryString({
      include_archived: params.include_archived ? "true" : undefined,
      limit: params.limit,
      q: params.q,
    })}`,
  );
}

export function createAssistantSession(
  payload: AssistantSessionCreatePayload = {},
): Promise<AssistantChatSessionSummary> {
  return request<AssistantChatSessionSummary>("/assistant/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getAssistantSession(
  sessionId: string,
): Promise<AssistantChatSessionDetail> {
  return request<AssistantChatSessionDetail>(
    `/assistant/sessions/${pathSegment(sessionId)}`,
  );
}

export function getAssistantSessionStreamReplays(
  sessionId: string,
): Promise<AssistantStreamReplay[]> {
  return request<AssistantStreamReplay[]>(
    `/assistant/sessions/${pathSegment(sessionId)}/stream-replays`,
  );
}

export function renameAssistantSession(
  sessionId: string,
  payload: AssistantSessionRenamePayload,
): Promise<AssistantChatSessionSummary> {
  return request<AssistantChatSessionSummary>(
    `/assistant/sessions/${pathSegment(sessionId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}

export function archiveAssistantSession(
  sessionId: string,
): Promise<AssistantChatSessionSummary> {
  return request<AssistantChatSessionSummary>(
    `/assistant/sessions/${pathSegment(sessionId)}/archive`,
    { method: "POST" },
  );
}

export function deleteAssistantSession(sessionId: string): Promise<{
  deleted: boolean;
  session_id: string;
}> {
  return request(`/assistant/sessions/${pathSegment(sessionId)}`, {
    method: "DELETE",
  });
}

export function appendAssistantSessionMessage(
  sessionId: string,
  payload: AssistantSessionMessagePayload,
): Promise<AssistantChatMessage> {
  return request<AssistantChatMessage>(
    `/assistant/sessions/${pathSegment(sessionId)}/messages`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function streamAssistantChat(
  payload: AssistantChatPayload,
  onEvent: (event: AssistantStreamEvent) => void,
  signal?: AbortSignal,
): Promise<AssistantResponse> {
  const body = JSON.stringify(payload);
  const response = await fetchApi(`${API_BASE_URL}/assistant/chat/stream`, {
    method: "POST",
    credentials: "include",
    headers: requestHeaders({ body }),
    signal,
    body,
  });
  if (!response.ok) {
    const envelope = await parseEnvelope<AssistantResponse>(response);
    throwApiRequestError(
      response,
      envelope,
      "assistant_stream_failed",
      `Assistant stream failed with status ${response.status}`,
    );
  }
  if (!response.body) {
    const error = new ApiRequestError({
      status: response.status,
      code: "assistant_stream_unavailable",
      message: "Assistant stream response did not include a readable body.",
      requestId: responseRequestId(response),
      endpoint: response.url,
    });
    emitApiRequestError(error);
    throw error;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResponse: AssistantResponse | null = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseAssistantStreamBuffer(buffer);
    buffer = parsed.remainder;
    for (const event of parsed.events) {
      onEvent(event);
      if (event.type === "error") {
        const error = new ApiRequestError({
          status: response.status,
          code: event.code,
          message: event.message,
          details: event.details,
          requestId: requestIdFromStreamEvent(event) ?? responseRequestId(response),
          endpoint: response.url,
        });
        emitApiRequestError(error);
        throw error;
      }
      if (event.type === "final") finalResponse = event.response;
    }
  }
  buffer += decoder.decode();
  const parsed = parseAssistantStreamBuffer(buffer);
  for (const event of parsed.events) {
    onEvent(event);
    if (event.type === "error") {
      const error = new ApiRequestError({
        status: response.status,
        code: event.code,
        message: event.message,
        details: event.details,
        requestId: requestIdFromStreamEvent(event) ?? responseRequestId(response),
        endpoint: response.url,
      });
      emitApiRequestError(error);
      throw error;
    }
    if (event.type === "final") finalResponse = event.response;
  }
  if (!finalResponse) {
    const error = new ApiRequestError({
      status: response.status,
      code: "assistant_stream_incomplete",
      message: "Assistant stream ended before the final response was received.",
      requestId: responseRequestId(response),
      endpoint: response.url,
    });
    emitApiRequestError(error);
    throw error;
  }
  return finalResponse;
}

export function listAssistantExamples(): Promise<AssistantExample[]> {
  return request<AssistantExample[]>("/assistant/examples");
}

export function listAssistantTools(): Promise<AssistantToolSpec[]> {
  return request<AssistantToolSpec[]>("/assistant/tools");
}

export function normalizeOcrEvidence(
  fields: OcrEvidenceFieldInput[],
): Promise<OcrEvidenceResponse> {
  return request<OcrEvidenceResponse>("/ocr/evidence", {
    method: "POST",
    body: JSON.stringify({ fields }),
  });
}

export function listRetrievalSources(): Promise<RetrievalSource[]> {
  return request<RetrievalSource[]>("/retrieval/sources");
}

export function getRetrievalIntegrity(params: {
  include_seeded: boolean;
  include_corpus: boolean;
}): Promise<RetrievalIntegrityReport> {
  return request<RetrievalIntegrityReport>(
    `/retrieval/integrity${queryString({
      include_seeded: String(params.include_seeded),
      include_corpus: String(params.include_corpus),
    })}`,
  );
}

export function reindexRetrieval(
  payload: RetrievalReindexPayload,
): Promise<RetrievalReindexResult> {
  return request<RetrievalReindexResult>("/retrieval/reindex", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listJobs(params: {
  status?: string | null;
  job_type?: string | null;
  limit?: number;
} = {}): Promise<BackgroundJob[]> {
  return request<BackgroundJob[]>(
    `/jobs${queryString({
      status: params.status ?? undefined,
      job_type: params.job_type ?? undefined,
      limit: params.limit,
    })}`,
  );
}

export function getJob(jobId: string): Promise<BackgroundJob> {
  return request<BackgroundJob>(`/jobs/${pathSegment(jobId)}`);
}

export function createRetrievalReindexJob(
  payload: RetrievalReindexJobPayload,
): Promise<BackgroundJob> {
  return request<BackgroundJob>("/jobs/retrieval-reindex", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getExtractorInventory(): Promise<ExtractorInventory> {
  return request<ExtractorInventory>("/parse/extractors");
}

export async function extractFileText(
  file: File,
  options: { extractor: string },
): Promise<ExtractedDocument> {
  const form = new FormData();
  form.append("file", file);
  form.append("extractor", options.extractor);

  const response = await fetchApi(`${API_BASE_URL}/parse/extract`, {
    method: "POST",
    body: form,
    credentials: "include",
  });
  const envelope = await parseEnvelope<ExtractedDocument>(response);
  if (!response.ok || envelope.error) {
    throwApiRequestError(
      response,
      envelope,
      "extract_failed",
      `Extraction failed with status ${response.status}`,
    );
  }
  return envelope.data as ExtractedDocument;
}

export function createClipboardImageParseJob(payload: {
  data_base64: string;
  filename: string;
  mime_type: string;
  extractor: string;
  execute_now: boolean;
  include_extracted_document?: boolean;
}): Promise<UploadParseJobResponse> {
  return request<UploadParseJobResponse>("/parse/clipboard/images/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getRuntimeConfig(): Promise<RuntimeConfig> {
  return request<RuntimeConfig>("/runtime/config");
}

export function getRuntimeReadiness(): Promise<RuntimeReadiness> {
  return request<RuntimeReadiness>("/runtime/readiness");
}

export function getRuntimeMigrations(): Promise<MigrationDiagnostics> {
  return request<MigrationDiagnostics>("/runtime/migrations");
}

export function updateRuntimeRetrievalSettings(
  payload: RuntimeRetrievalSettingsPayload,
): Promise<RuntimeRetrievalSettingsUpdate> {
  return request<RuntimeRetrievalSettingsUpdate>("/runtime/retrieval-settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function updateRuntimeAssistantSettings(
  payload: RuntimeAssistantSettingsPayload,
): Promise<RuntimeAssistantSettingsUpdate> {
  return request<RuntimeAssistantSettingsUpdate>("/runtime/assistant-settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function getRuntimeHealth(): Promise<RuntimeHealth> {
  const rootPrefix = API_BASE_URL.endsWith("/api/v1")
    ? API_BASE_URL.slice(0, -"/api/v1".length)
    : "";
  const response = await fetchApi(`${rootPrefix}/health`, { credentials: "include" });
  if (!response.ok) {
    throw new ApiRequestError({
      status: response.status,
      code: "health_check_failed",
      message: `Health check failed with status ${response.status}`,
      details: {},
    });
  }
  return parseJsonResponse<RuntimeHealth>(response);
}

export async function uploadFileWorkflow(
  file: File,
  options: {
    instruction: string;
    targetFormat: string;
    schemaId: string | null;
    requireHumanReview: boolean;
    extractor: string;
  },
): Promise<WorkflowState> {
  const form = new FormData();
  form.append("file", file);
  form.append("instruction", options.instruction);
  form.append("target_format", options.targetFormat);
  if (options.schemaId) form.append("schema_id", options.schemaId);
  form.append("require_human_review", String(options.requireHumanReview));
  form.append("extractor", options.extractor);

  const response = await fetchApi(`${API_BASE_URL}/parse/upload/workflow`, {
    method: "POST",
    body: form,
    credentials: "include",
    // Do NOT set Content-Type — browser sets multipart boundary automatically
  });
  const envelope = await parseEnvelope<WorkflowState>(response);
  if (!response.ok || envelope.error) {
    throwApiRequestError(
      response,
      envelope,
      "upload_failed",
      `Upload failed with status ${response.status}`,
    );
  }
  return envelope.data as WorkflowState;
}
