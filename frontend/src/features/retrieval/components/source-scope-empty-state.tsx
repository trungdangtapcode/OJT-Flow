export function SourceScopeEmptyState({ hasSources }: { hasSources: boolean }) {
  return (
    <div className="rounded-lg border border-border/60 bg-card p-3 text-sm text-muted-foreground">
      {hasSources ? "No source matches this search." : "No retrieval sources loaded."}
    </div>
  );
}
