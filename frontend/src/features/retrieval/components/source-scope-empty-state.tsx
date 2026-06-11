export function SourceScopeEmptyState({ hasSources }: { hasSources: boolean }) {
  return (
    <div className="rounded-md border border-border bg-card p-3 text-sm text-muted-foreground">
      {hasSources ? "No source matches this search." : "No retrieval sources loaded."}
    </div>
  );
}
