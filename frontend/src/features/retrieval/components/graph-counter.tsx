export function GraphCounter({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border/60 bg-muted/20 p-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-black tabular-nums">{value}</div>
    </div>
  );
}
