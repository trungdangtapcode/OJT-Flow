import { SourceMetadataBadges } from "./source-metadata-badges";
import type { SourceScopeSelectionProps } from "./source-scope-picker-types";

export function SourceScopeSelectedSummary({
  selectedSource,
  sourceId,
}: SourceScopeSelectionProps) {
  return (
    <div className="grid gap-1 rounded-md border border-primary/25 bg-primary/10 p-2 text-sm">
      <div className="font-bold">{selectedSource?.title ?? sourceId}</div>
      <div className="break-all font-mono text-xs text-muted-foreground">{sourceId}</div>
      {selectedSource ? <SourceMetadataBadges source={selectedSource} /> : null}
    </div>
  );
}
