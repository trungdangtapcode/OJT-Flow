import { Badge } from "../../../components/ui/badge";
import type { BadgeVariant } from "./run-comparison-detail-types";

export function RunComparisonEvidenceChange({
  evidenceIds,
  label,
  variant,
}: {
  evidenceIds: string[];
  label: string;
  variant: BadgeVariant;
}) {
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-bold text-muted-foreground">{label}</span>
        <Badge variant={variant}>{evidenceIds.length}</Badge>
      </div>
      {evidenceIds.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {evidenceIds.slice(0, 4).map((evidenceId) => (
            <span
              className="max-w-full break-words rounded-full border border-border bg-background px-2 py-1 text-[11px] font-bold text-muted-foreground"
              key={evidenceId}
            >
              {evidenceId}
            </span>
          ))}
          {evidenceIds.length > 4 ? (
            <span className="rounded-full border border-border bg-background px-2 py-1 text-[11px] font-bold text-muted-foreground">
              +{evidenceIds.length - 4}
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
