export function SourceDiversityMetricCard({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-2">
      <div className="text-xs font-black uppercase text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-xl font-black tabular-nums">{value}</div>
    </div>
  );
}
