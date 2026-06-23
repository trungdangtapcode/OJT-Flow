import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { queryHealthBadgeVariant, queryHealthOverallLabel, queryHealthOverallVariant } from "./query-health-status";
import type { SearchReadinessChecklistItem } from "./search-cockpit-panel-types";

export function SearchReadinessChecklist({
  items,
}: {
  items: SearchReadinessChecklistItem[];
}) {
  const overallVariant = queryHealthOverallVariant(items);
  const overallLabel = queryHealthOverallLabel(items);

  return (
    <section
      aria-label="Search readiness checklist"
      className="grid gap-2 rounded-lg border border-border/60 bg-card p-3"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Search readiness checklist
          </div>
          <div className="mt-1 break-words text-sm font-semibold text-muted-foreground">
            Fast review of whether this search package is ready to inspect,
            needs human review, or should be remediated before downstream use.
          </div>
        </div>
        <Badge variant={overallVariant}>{humanize(overallLabel)}</Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => (
          <div
            className="grid min-w-0 gap-1 rounded-lg border border-border/60 bg-muted/25 px-3 py-2"
            key={item.code}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-1.5">
              <span className="break-words text-xs font-black text-muted-foreground">
                {item.label}
              </span>
              <Badge variant={queryHealthBadgeVariant(item.status)}>
                {humanize(item.status)}
              </Badge>
            </div>
            <div className="break-words text-xs leading-5 text-muted-foreground">
              {item.detail}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
