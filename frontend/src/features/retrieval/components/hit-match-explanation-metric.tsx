export function HitMatchExplanationMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs">
      <span className="font-bold text-muted-foreground">{label}</span>
      <span className="min-w-0 break-words font-semibold">{value}</span>
    </div>
  );
}
