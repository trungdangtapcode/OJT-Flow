export function QueryAnalysisCounter({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-md border border-border bg-card px-2 py-1.5">
      <div className="font-bold text-muted-foreground">{label}</div>
      <div className="text-base font-black tabular-nums">{value}</div>
    </div>
  );
}
