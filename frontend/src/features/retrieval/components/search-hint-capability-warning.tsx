export function SearchHintCapabilityWarning({
  warning,
}: {
  warning: string | null;
}) {
  if (!warning) return null;
  return (
    <div className="rounded-md border border-border bg-card px-2 py-1.5 text-[11px] font-semibold leading-5 text-muted-foreground">
      {warning}
    </div>
  );
}
