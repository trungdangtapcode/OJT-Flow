export function MetricMiniCard({
  label,
  supporting,
  value,
}: {
  label: string;
  supporting: string;
  value: number | string;
}) {
  return (
    <div className="min-w-0 rounded-lg border border-border/60 bg-muted/20 p-2">
      <div className="truncate text-[0.68rem] font-black uppercase text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 break-words text-lg font-black">{value}</div>
      <div className="mt-1 line-clamp-2 break-words text-xs text-muted-foreground">
        {supporting}
      </div>
    </div>
  );
}
