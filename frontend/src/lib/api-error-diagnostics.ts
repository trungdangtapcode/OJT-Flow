import { ApiRequestError } from "../api";

export type ApiErrorDiagnostic = {
  status: number | null;
  code: string;
  message: string;
  details: Record<string, unknown>;
  workflowId: string | null;
  requestId: string | null;
  endpoint: string | null;
  occurredAt: string | null;
};

export function apiErrorDiagnostic(error: unknown): ApiErrorDiagnostic {
  if (error instanceof ApiRequestError) {
    return {
      status: error.status,
      code: error.code,
      message: cleanApiErrorMessage(error.message, error.code),
      details: error.details,
      workflowId: error.workflowId,
      requestId: error.requestId,
      endpoint: error.endpoint,
      occurredAt: null,
    };
  }
  const message = error instanceof Error ? error.message : String(error);
  return {
    status: null,
    code: "client_error",
    message,
    details: {},
    workflowId: null,
    requestId: null,
    endpoint: null,
    occurredAt: null,
  };
}

export function apiErrorMessage(error: unknown): string {
  const diagnostic = apiErrorDiagnostic(error);
  const parts = [`${diagnostic.code}: ${diagnostic.message}`];
  if (diagnostic.workflowId) parts.push(`Workflow ${diagnostic.workflowId}`);
  if (diagnostic.requestId) parts.push(`Request ${diagnostic.requestId}`);
  return parts.join(" | ");
}

export function cleanApiErrorMessage(message: string, code: string) {
  const prefix = `${code}: `;
  return message.startsWith(prefix) ? message.slice(prefix.length) : message;
}
