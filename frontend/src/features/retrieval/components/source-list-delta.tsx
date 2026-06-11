import { Badge } from "../../../components/ui/badge";

export function SourceListDelta({
  label,
  sourceIds,
  variant,
}: {
  label: string;
  sourceIds: string[];
  variant: "success" | "warning" | "muted";
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-start gap-2">
      <span className="w-28 shrink-0 font-semibold text-muted-foreground">
        {label}
      </span>
      {sourceIds.length ? (
        sourceIds.slice(0, 8).map((sourceId) => (
          <Badge key={sourceId} variant={variant}>
            {sourceId}
          </Badge>
        ))
      ) : (
        <Badge variant="muted">none</Badge>
      )}
    </div>
  );
}
