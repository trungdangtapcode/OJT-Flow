import { Badge } from "../../../components/ui/badge";
import type { SearchPlanCoverageSummaryView } from "../model/search-plan-summary-types";
import { MetricMiniCard } from "./search-plan-metric-mini-card";
import { SectionHelpText } from "./section-help-text";

export function SearchPlanCoverageSummaryPanel({
  summary,
}: {
  summary: SearchPlanCoverageSummaryView;
}) {
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Plan coverage
        </span>
        <Badge variant={summary.ready ? "success" : "warning"}>
          {summary.ready ? "coverage planned" : "needs detail"}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <MetricMiniCard
          label="Required local tasks"
          supporting="Trusted corpus coverage"
          value={`${summary.requiredLocalTaskCount}/${summary.localTaskCount}`}
        />
        <MetricMiniCard
          label="External follow-ups"
          supporting="Medical index checks"
          value={summary.externalTaskCount}
        />
        <MetricMiniCard
          label="Standards"
          supporting={summary.standards.slice(0, 3).join(", ") || "No standard inferred"}
          value={summary.standards.length}
        />
        <MetricMiniCard
          label="Filters"
          supporting="Suggested scope controls"
          value={summary.filterCount}
        />
      </div>
      <div className="rounded-md border border-border bg-muted/20 px-2 py-1.5 text-xs">
        <div className="font-black uppercase text-muted-foreground">Next action</div>
        <div className="mt-1 break-words font-semibold">{summary.nextAction}</div>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {summary.standards.slice(0, 6).map((standard) => (
          <Badge key={standard} variant="muted">
            {standard}
          </Badge>
        ))}
        {summary.warnings.slice(0, 3).map((warning) => (
          <Badge key={warning} variant="warning">
            {warning}
          </Badge>
        ))}
      </div>
      <SectionHelpText>{summary.summary}</SectionHelpText>
      {!summary.ready ? (
        <SectionHelpText>
          Add a more specific standard, data field, resource type, or clinical domain before relying on this search for review.
        </SectionHelpText>
      ) : null}
    </div>
  );
}
