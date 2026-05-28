import type {
  ApiEnvelope,
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
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
