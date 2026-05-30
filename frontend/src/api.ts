import type {
  ApiEnvelope,
  AuthLoginResponse,
  AuthSessionResponse,
  SchemaEntry,
  StartWorkflowPayload,
  WorkflowEvent,
  WorkflowState,
} from "./types";

const configuredBase = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const API_BASE_URL =
  configuredBase && configuredBase.length > 0
    ? configuredBase.replace(/\/$/, "")
    : "/api/v1";

const AUTH_TOKEN_STORAGE_KEY = "ojtflow.auth_token";

export function getStoredAuthToken(): string | null {
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

export function storeAuthToken(token: string): void {
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

export function clearStoredAuthToken(): void {
  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getStoredAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });
  const envelope = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || envelope.error) {
    const message = envelope.error
      ? `${envelope.error.code}: ${envelope.error.message}`
      : `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return envelope.data as T;
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

export function listWorkflows(status?: string): Promise<WorkflowState[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<WorkflowState[]>(`/workflows${query}`);
}

export function getWorkflow(workflowId: string): Promise<WorkflowState> {
  return request<WorkflowState>(`/workflows/${workflowId}`);
}

export function listWorkflowEvents(workflowId: string): Promise<WorkflowEvent[]> {
  return request<WorkflowEvent[]>(`/workflows/${workflowId}/events`);
}

export function createWorkflow(payload: StartWorkflowPayload): Promise<WorkflowState> {
  return request<WorkflowState>("/workflows", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listReviews(status = "pending"): Promise<WorkflowState[]> {
  return request<WorkflowState[]>(`/reviews?status=${encodeURIComponent(status)}`);
}

export function submitReview(
  reviewId: string,
  decision: string,
  decidedBy = "ui_user",
  payload: Record<string, unknown> = {},
): Promise<WorkflowState> {
  return request<WorkflowState>(`/review/${reviewId}`, {
    method: "POST",
    body: JSON.stringify({
      decision,
      decided_by: decidedBy,
      payload,
    }),
  });
}

export function listSchemas(): Promise<SchemaEntry[]> {
  return request<SchemaEntry[]>("/schemas");
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

  const response = await fetch(`${API_BASE_URL}/parse/upload/workflow`, {
    method: "POST",
    body: form,
    headers: authHeaders(),
    // Do NOT set Content-Type — browser sets multipart boundary automatically
  });
  const envelope = (await response.json()) as ApiEnvelope<WorkflowState>;
  if (!response.ok || envelope.error) {
    const message = envelope.error
      ? `${envelope.error.code}: ${envelope.error.message}`
      : `Upload failed with status ${response.status}`;
    throw new Error(message);
  }
  return envelope.data as WorkflowState;
}
