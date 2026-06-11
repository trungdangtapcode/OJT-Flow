import { AlertTriangle, Search } from "lucide-react";

import { cn } from "../../../lib/utils";

export function SourceScopeStatusNotice({ sourceId }: { sourceId: string }) {
  const isScoped = Boolean(sourceId);
  return (
    <div
      className={cn(
        "flex min-w-0 items-start gap-2 rounded-md border px-3 py-2 text-xs leading-5",
        isScoped
          ? "border-amber-200 bg-amber-50 text-amber-950"
          : "border-border bg-card text-muted-foreground",
      )}
    >
      {isScoped ? (
        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-700" />
      ) : (
        <Search className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
      )}
      <span className="min-w-0 break-words font-semibold">
        {isScoped
          ? "Search is constrained to one exact source. Clear it before judging corpus-wide evidence coverage."
          : "Leave exact source blank for broad search. Pick a source only when you need source-specific evidence."}
      </span>
    </div>
  );
}
