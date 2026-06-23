import { Badge } from "../../../components/ui/badge";
import type { BadgeVariant } from "./run-comparison-summary-types";

export function RunComparisonMetric({
  delta,
  deltaBadgeVariant,
  formatSignedDelta,
  label,
  positiveIsGood,
}: {
  delta: number;
  deltaBadgeVariant: (delta: number, positiveIsGood: boolean) => BadgeVariant;
  formatSignedDelta: (delta: number) => string;
  label: string;
  positiveIsGood: boolean;
}) {
  return (
    <div className="flex min-w-0 items-center justify-between gap-2 rounded-lg border border-border/60 bg-card px-3 py-2">
      <span className="text-xs font-bold text-muted-foreground">{label}</span>
      <Badge variant={deltaBadgeVariant(delta, positiveIsGood)}>
        {formatSignedDelta(delta)}
      </Badge>
    </div>
  );
}
