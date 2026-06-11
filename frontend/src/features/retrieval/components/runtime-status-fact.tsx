import { Badge } from "../../../components/ui/badge";

export type RuntimeStatusBadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "destructive"
  | "muted";

export function RuntimeStatusFact({
  label,
  supporting,
  value,
  variant,
}: {
  label: string;
  supporting: string;
  value: string;
  variant: RuntimeStatusBadgeVariant;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-muted/20 px-3 py-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold uppercase text-muted-foreground">{label}</span>
        <Badge variant={variant}>{value}</Badge>
      </div>
      <span className="break-words text-muted-foreground">{supporting}</span>
    </div>
  );
}
