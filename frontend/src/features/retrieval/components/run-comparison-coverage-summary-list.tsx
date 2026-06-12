import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalCoverageSummaryView } from "./run-comparison-detail-types";
import { coverageComparisonKey } from "./run-comparison-coverage-key";

export function CoverageSummaryList({
  items,
  label,
  variant,
}: {
  items: RetrievalCoverageSummaryView[];
  label: string;
  variant: "warning" | "muted";
}) {
  if (!items.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5">
      <span className="font-semibold text-muted-foreground">{label}:</span>
      {items.slice(0, 4).map((item) => (
        <Badge key={`${label}-${coverageComparisonKey(item)}`} variant={variant}>
          {item.label} / {humanize(item.status)}
        </Badge>
      ))}
      {items.length > 4 ? <Badge variant="muted">+{items.length - 4}</Badge> : null}
    </div>
  );
}
