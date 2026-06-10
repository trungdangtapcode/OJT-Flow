import * as React from "react";
import { Copy, X } from "lucide-react";

import { API_REQUEST_ERROR_EVENT } from "../api";
import { Button } from "../components/ui/button";
import {
  type ApiErrorDiagnostic,
  cleanApiErrorMessage,
} from "../lib/api-error-diagnostics";

export function ApiErrorPanel() {
  const [error, setError] = React.useState<ApiErrorDiagnostic | null>(null);

  React.useEffect(() => {
    const onApiError = (event: Event) => {
      const detail = (event as CustomEvent<ApiErrorDiagnostic>).detail;
      if (!detail?.code) return;
      setError({
        ...detail,
        message: cleanApiErrorMessage(detail.message, detail.code),
      });
    };
    window.addEventListener(API_REQUEST_ERROR_EVENT, onApiError);
    return () => window.removeEventListener(API_REQUEST_ERROR_EVENT, onApiError);
  }, []);

  if (!error) return null;

  const payload = JSON.stringify(error, null, 2);
  const copyPayload = async () => {
    await navigator.clipboard?.writeText(payload);
  };

  return (
    <aside className="fixed bottom-4 right-4 z-50 w-[min(28rem,calc(100vw-2rem))] rounded-md border border-red-200 bg-card p-3 text-sm shadow-2xl">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-bold text-red-900">API request failed</div>
          <div className="mt-1 break-words text-foreground">
            {error.code}: {error.message}
          </div>
        </div>
        <Button
          aria-label="Dismiss API error"
          className="h-8 w-8 shrink-0"
          onClick={() => setError(null)}
          size="icon"
          type="button"
          variant="ghost"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="mt-3 grid gap-1 text-xs text-muted-foreground">
        <DiagnosticRow label="Status" value={error.status === null ? null : String(error.status)} />
        <DiagnosticRow label="Request" value={error.requestId} />
        <DiagnosticRow label="Workflow" value={error.workflowId} />
        <DiagnosticRow label="Endpoint" value={shortEndpoint(error.endpoint)} />
      </div>
      <div className="mt-3 flex items-center justify-between gap-2">
        <details className="min-w-0 flex-1">
          <summary className="cursor-pointer text-xs font-bold text-muted-foreground">
            Diagnostic payload
          </summary>
          <pre className="mt-2 max-h-48 overflow-auto rounded-md bg-muted p-2 text-[11px] text-muted-foreground">
            {payload}
          </pre>
        </details>
        <Button
          className="shrink-0"
          onClick={() => void copyPayload()}
          size="sm"
          type="button"
          variant="outline"
        >
          <Copy className="h-3.5 w-3.5" />
          Copy
        </Button>
      </div>
    </aside>
  );
}

function DiagnosticRow({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="grid grid-cols-[5rem_minmax(0,1fr)] gap-2">
      <span className="font-bold text-foreground">{label}</span>
      <span className="truncate" title={value}>
        {value}
      </span>
    </div>
  );
}

function shortEndpoint(endpoint: string | null) {
  if (!endpoint) return null;
  try {
    const url = new URL(endpoint, window.location.origin);
    return `${url.pathname}${url.search}`;
  } catch {
    return endpoint;
  }
}
