import type { RetrievalSource } from "../../../types";
import { SourceCard } from "./source-card";

export function SourceInventorySourceList({
  hasSourceFilters,
  isLoading,
  onUseSource,
  sources,
}: {
  hasSourceFilters: boolean;
  isLoading: boolean;
  onUseSource: (sourceId: string) => void;
  sources: RetrievalSource[];
}) {
  return (
    <div className="grid gap-3">
      {sources.map((source) => (
        <SourceCard key={source.source_id} onUseSource={onUseSource} source={source} />
      ))}
      {!sources.length ? (
        <div className="rounded-md border border-border p-3 text-sm text-muted-foreground">
          {isLoading
            ? "Loading sources."
            : hasSourceFilters
              ? "No sources match the current filters."
              : "No retrieval sources indexed."}
        </div>
      ) : null}
    </div>
  );
}
