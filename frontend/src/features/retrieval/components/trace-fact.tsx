export function TraceFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[7rem_minmax(0,1fr)] gap-3 text-sm">
      <span className="font-bold text-muted-foreground">{label}</span>
      <span className="break-words">{value}</span>
    </div>
  );
}
