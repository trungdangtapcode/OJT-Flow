import { Badge } from "../../../components/ui/badge";
import { cn } from "../../../lib/utils";
import type { RetrievalSource } from "../../../types";
import { SourceMetadataBadges } from "./source-metadata-badges";

export function SourceScopeOptionRow({
  isSearchPending,
  isSelected,
  onSelect,
  source,
}: {
  isSearchPending: boolean;
  isSelected: boolean;
  onSelect: (sourceId: string) => void;
  source: RetrievalSource;
}) {
  return (
    <button
      className={cn(
        "grid min-w-0 gap-1 rounded-md border px-3 py-2 text-left text-sm transition-colors",
        isSelected
          ? "border-primary bg-primary/10"
          : "border-border bg-card hover:border-primary hover:bg-primary/5",
      )}
      disabled={isSearchPending}
      onClick={() => onSelect(source.source_id)}
      type="button"
    >
      <span className="break-words font-bold">{source.title}</span>
      {isSelected ? (
        <Badge className="w-fit" variant="success">
          applied exact source
        </Badge>
      ) : null}
      <span className="break-all font-mono text-xs text-muted-foreground">
        {source.source_id}
      </span>
      <SourceMetadataBadges source={source} />
    </button>
  );
}
