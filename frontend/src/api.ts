import type {
  ApiEnvelope,
  AssistantChatPayload,
  AssistantResponse,
  AuthLoginResponse,
  AuthSessionResponse,
  ExtractorInventory,
  RetrievalIntegrityReport,
  RetrievalPackage,
  RetrievalReindexPayload,
  RetrievalReindexResult,
  RetrievalSearchPayload,
  RetrievalSource,
  RuntimeAssistantSettingsPayload,
  RuntimeAssistantSettingsUpdate,
  RuntimeConfig,
  RuntimeHealth,
  RuntimeReadiness,
  RuntimeRetrievalSettingsPayload,
  RuntimeRetrievalSettingsUpdate,
  SchemaEntry,
  StartWorkflowPayload,
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

export class ApiRequestError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;
  workflowId: string | null;

  constructor({
    status,
    code,
    message,
    details,
    workflowId = null,
  }: {
    status: number;
    code: string;
    message: string;
    details?: Record<string, unknown>;
    workflowId?: string | null;
  }) {
    super(`${code}: ${message}`);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
    this.details = details ?? {};
    this.workflowId = workflowId;
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
  if (
    init?.body !== undefined &&
    !(init.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

async function fetchApi(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch (error) {
    throw new ApiRequestError({
      status: 0,
      code: "network_error",
      message: "API request could not reach the server.",
      details: {
        reason: error instanceof Error ? error.message : String(error),
      },
    });
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
      details: { status: response.status, content_type: contentType || null },
      workflow_id: null,
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
      },
      workflow_id: null,
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
      },
      workflow_id: null,
    },
  };
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") ?? "";
  const body = await response.text();
  if (!contentType.includes("application/json")) {
    throw new ApiRequestError({
      status: response.status,
      code: "invalid_response",
      message: "API returned a non-JSON response.",
      details: {
        status: response.status,
        content_type: contentType || null,
        body_length: body.length,
      },
    });
  }
  try {
    return JSON.parse(body) as T;
  } catch (error) {
    throw new ApiRequestError({
      status: response.status,
      code: "invalid_response",
      message: "API returned malformed JSON.",
      details: {
        status: response.status,
        content_type: contentType || null,
        body_length: body.length,
        parse_error: error instanceof Error ? error.message : String(error),
      },
    });
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
  });
  if (error.status === 401) notifyAuthSessionExpired();
  throw error;
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

export function chatWithAssistant(
  payload: AssistantChatPayload,
): Promise<AssistantResponse> {
  return request<AssistantResponse>("/assistant/chat", {
    method: "POST",
    body: JSON.stringify(payload),
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

export function getExtractorInventory(): Promise<ExtractorInventory> {
  return request<ExtractorInventory>("/parse/extractors");
}

export function getRuntimeConfig(): Promise<RuntimeConfig> {
  return request<RuntimeConfig>("/runtime/config");
}

export function getRuntimeReadiness(): Promise<RuntimeReadiness> {
  return request<RuntimeReadiness>("/runtime/readiness");
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
