import { Badge } from "../../../components/ui/badge";
import type { RetrievalCoverageComparisonView } from "./run-comparison-detail-types";
import { CoverageStatusChangeList } from "./run-comparison-coverage-status-list";
import { CoverageSummaryList } from "./run-comparison-coverage-summary-list";

export function RunComparisonCoverage({
  comparison,
  formatCount,
}: {
  comparison: RetrievalCoverageComparisonView;
  formatCount: (count: number, singular: string) => string;
}) {
  const changed =
    comparison.added.length +
    comparison.removed.length +
    comparison.improved.length +
    comparison.regressed.length;
  const total = changed + comparison.retained.length;
  if (!total) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Coverage diagnostics</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Coverage diagnostics</span>
        <Badge variant={comparison.regressed.length || comparison.added.length ? "warning" : "success"}>
          {changed ? formatCount(changed, "changed item") : "stable"}
        </Badge>
      </div>
      <CoverageStatusChangeList
        changes={comparison.improved}
        label="Improved"
        variant="success"
      />
      <CoverageStatusChangeList
        changes={comparison.regressed}
        label="Regressed"
        variant="warning"
      />
      <CoverageSummaryList
        items={comparison.added}
        label="Added"
        variant="warning"
      />
      <CoverageSummaryList
        items={comparison.removed}
        label="Removed"
        variant="muted"
      />
      <CoverageSummaryList
        items={comparison.retained}
        label="Retained"
        variant="muted"
      />
    </div>
  );
}
