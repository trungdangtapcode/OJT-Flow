export function SearchRunComparisonBaseline({
  baselineQuery,
}: {
  baselineQuery: string;
}) {
  return (
    <div className="grid gap-1 rounded-lg border border-border/60 bg-card px-3 py-2 text-xs">
      <span className="font-bold uppercase text-muted-foreground">Baseline query</span>
      <span className="break-words leading-5">{baselineQuery}</span>
    </div>
  );
}
