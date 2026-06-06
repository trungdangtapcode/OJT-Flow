import { ListFilter, X } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { humanize } from "../../../lib/utils";
import { SectionHelpText } from "./section-help-text";

export type QueryHealthItem = {
  code: string;
  description: string;
  label: string;
  status: "ok" | "review" | "blocked" | "info";
};

export type SearchReadinessChecklistItem = {
  code: string;
  detail: string;
  label: string;
  status: QueryHealthItem["status"];
};

export type QueryHealthFilterEntry = {
  field: string;
};

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
  const sourceFilter = activeFilters.find((filter) => filter.field === "source_id");
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
          <div
            className="grid gap-1 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm"
            key={item.code}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-black">{item.label}</span>
              <Badge variant={queryHealthBadgeVariant(item.status)}>
                {humanize(item.status)}
              </Badge>
            </div>
            <div className="break-words text-xs leading-5 text-muted-foreground">
              {item.description}
            </div>
            {item.code === "diagnostic_overconstrained_metadata_filters" ? (
              <div className="flex min-w-0 flex-wrap gap-1.5 pt-1">
                {sourceFilter ? (
                  <Button
                    disabled={isSearchPending}
                    onClick={onClearSourceScope}
                    size="sm"
                    title="Clear exact source scope and rerun search"
                    type="button"
                    variant="outline"
                  >
                    <X className="h-4 w-4" />
                    Clear source scope
                  </Button>
                ) : null}
                <Button
                  disabled={isSearchPending || !activeFilters.length}
                  onClick={onClearAllFilters}
                  size="sm"
                  title="Clear all active metadata filters and rerun search"
                  type="button"
                  variant="outline"
                >
                  <ListFilter className="h-4 w-4" />
                  Broaden search
                </Button>
              </div>
            ) : null}
          </div>
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
      className="grid gap-2 rounded-md border border-border bg-card p-3"
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
            className="grid min-w-0 gap-1 rounded-md border border-border bg-muted/25 px-3 py-2"
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

export function CockpitMetricCard({
  helpText,
  label,
  supporting,
  tone,
  value,
}: {
  helpText: string;
  label: string;
  supporting: string;
  tone: "success" | "warning" | "info";
  value: string;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2">
      <span className="inline-flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
        {label}
        <HelpTooltip label={`${label} help`}>{helpText}</HelpTooltip>
      </span>
      <Badge variant={tone === "info" ? "default" : tone}>{value}</Badge>
      <span className="break-words text-xs leading-5 text-muted-foreground">
        {supporting}
      </span>
    </div>
  );
}

function queryHealthBadgeVariant(
  status: QueryHealthItem["status"],
): "success" | "warning" | "destructive" | "muted" {
  if (status === "ok") return "success";
  if (status === "blocked") return "destructive";
  if (status === "review") return "warning";
  return "muted";
}

function queryHealthOverallVariant(
  items: Array<{ status: QueryHealthItem["status"] }>,
): "success" | "warning" | "destructive" | "muted" {
  if (items.some((item) => item.status === "blocked")) return "destructive";
  if (items.some((item) => item.status === "review")) return "warning";
  if (items.some((item) => item.status === "ok")) return "success";
  return "muted";
}

function queryHealthOverallLabel(
  items: Array<{ status: QueryHealthItem["status"] }>,
): string {
  if (items.some((item) => item.status === "blocked")) return "blocked";
  if (items.some((item) => item.status === "review")) return "review";
  if (items.some((item) => item.status === "ok")) return "healthy";
  return "unscored";
}
