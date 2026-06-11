import { Badge } from "../../../components/ui/badge";
import { standardSearchMatchReasons } from "./strategy-standard-format";

export function StandardSearchMatchReasons({
  metadata,
}: {
  metadata: Record<string, unknown>;
}) {
  const reasons = standardSearchMatchReasons(metadata);
  if (!reasons.length) {
    return null;
  }
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5 text-xs">
      <span className="font-black uppercase text-muted-foreground">Matched by</span>
      {reasons.map((reason) => (
        <Badge key={`${reason.label}:${reason.value}`} variant={reason.variant}>
          {reason.label}: {reason.value}
        </Badge>
      ))}
    </div>
  );
}
