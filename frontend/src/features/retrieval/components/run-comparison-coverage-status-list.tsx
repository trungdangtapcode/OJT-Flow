import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalCoverageStatusChangeView } from "./run-comparison-detail-types";
import { coverageComparisonKey } from "./run-comparison-coverage-key";

export function CoverageStatusChangeList({
  changes,
  label,
  variant,
}: {
  changes: RetrievalCoverageStatusChangeView[];
  label: string;
  variant: "success" | "warning";
}) {
  if (!changes.length) return null;
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-semibold text-muted-foreground">{label}:</span>
        {changes.slice(0, 4).map((change) => (
          <Badge key={`${label}-${coverageComparisonKey(change.active)}`} variant={variant}>
            {change.active.label}
          </Badge>
        ))}
        {changes.length > 4 ? <Badge variant="muted">+{changes.length - 4}</Badge> : null}
      </div>
      <div className="grid gap-1">
        {changes.slice(0, 2).map((change) => (
          <div
            className="break-words text-muted-foreground"
            key={`${label}-${coverageComparisonKey(change.active)}-detail`}
          >
            {humanize(change.baseline.status)} to {humanize(change.active.status)} /{" "}
            {change.baseline.selectedCount} to {change.active.selectedCount}
          </div>
        ))}
      </div>
    </div>
  );
}
