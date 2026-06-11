import type { Evidence } from "../../../types";

export function HitLocatorDetails({
  evidence,
  sourceLocator,
}: {
  evidence: Evidence;
  sourceLocator: Record<string, unknown>;
}) {
  return (
    <details className="rounded-md border border-border bg-muted/20 p-2 text-xs">
      <summary className="cursor-pointer font-bold">Locator and evidence ID</summary>
      <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words font-mono">
        {JSON.stringify(
          {
            evidence_id: evidence.evidence_id,
            locator: evidence.locator,
            source_locator: sourceLocator,
          },
          null,
          2,
        )}
      </pre>
    </details>
  );
}
