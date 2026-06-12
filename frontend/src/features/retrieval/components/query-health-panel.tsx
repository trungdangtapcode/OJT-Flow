import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { QueryHealthItemCard } from "./query-health-item-card";
import { queryHealthOverallLabel, queryHealthOverallVariant } from "./query-health-status";
import { SectionHelpText } from "./section-help-text";
import type { QueryHealthFilterEntry, QueryHealthItem } from "./search-cockpit-panel-types";

export function QueryHealthPanel({
  activeFilters,
  isSearchPending,
  items,
  onClearAllFilters,
  onClearSourceScope,
}: {
  activeFilters: QueryHealthFilterEntry[];
  isSearchPending: boolean;
  items: QueryHealthItem[];
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
}) {
  const overconstrained = items.some(
    (item) => item.code === "diagnostic_overconstrained_metadata_filters",
  );

  return (
    <div
      aria-label="Query health checklist"
      className="grid gap-2 rounded-md border border-border bg-card p-3"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
          Query health
          <HelpTooltip label="Query health help">
            Data-derived checklist for search scope and interpretation risk. Review warnings before trusting the ranked evidence.
          </HelpTooltip>
        </div>
        <Badge variant={queryHealthOverallVariant(items)}>
          {queryHealthOverallLabel(items)}
        </Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <QueryHealthItemCard
            activeFilters={activeFilters}
            isSearchPending={isSearchPending}
            item={item}
            key={item.code}
            onClearAllFilters={onClearAllFilters}
            onClearSourceScope={onClearSourceScope}
          />
        ))}
      </div>
      {overconstrained ? (
        <SectionHelpText>
          These actions broaden the submitted search and rerun retrieval. Use them before deciding the corpus lacks evidence.
        </SectionHelpText>
      ) : null}
    </div>
  );
}
