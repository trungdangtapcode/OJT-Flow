import { Badge } from "../../../components/ui/badge";
import { IntegritySourceCheckRow } from "./integrity-source-check-row";
import type { IntegrityPanelProps } from "./integrity-panel-types";

export function IntegritySourceChecks({
  checks,
  formatCount,
  formatHash,
  integrityBadgeVariant,
  report,
}: Pick<
  IntegrityPanelProps,
  "checks" | "formatCount" | "formatHash" | "integrityBadgeVariant" | "report"
>) {
  if (!report) return null;
  return (
    <div className="grid gap-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Source checks
        </div>
        <Badge variant={report.extra_count ? "warning" : "muted"}>
          {formatCount(report.extra_count, "extra source")}
        </Badge>
      </div>
      <div className="grid gap-2">
        {checks.map((check) => (
          <IntegritySourceCheckRow
            check={check}
            formatHash={formatHash}
            integrityBadgeVariant={integrityBadgeVariant}
            key={check.source_id}
          />
        ))}
        {!checks.length ? (
          <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
            No source checks returned.
          </div>
        ) : null}
      </div>
    </div>
  );
}
