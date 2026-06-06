import { ListFilter, Loader2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { RetrievalCoverage, RetrievalCoverageItem } from "../../../types";
import { SectionHelpText } from "./section-help-text";
import { TokenList } from "./token-list";

export type CoverageDiagnosticsFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type CoverageDiagnosticsFilterAction = {
  field: CoverageDiagnosticsFilterField;
  value: string;
};

export function CoverageDiagnosticsPanel({
  coverage,
  filterFieldLabel,
  formatFilterValue,
  getCoverageSuggestedAction,
  getCoverageSuggestedFilter,
  isSearchPending,
  onApplyCoverageFilter,
}: {
  coverage: RetrievalCoverage | null | undefined;
  filterFieldLabel: (field: CoverageDiagnosticsFilterField) => string;
  formatFilterValue: (field: CoverageDiagnosticsFilterField, value: string) => string;
  getCoverageSuggestedAction: (item: RetrievalCoverageItem) => string;
  getCoverageSuggestedFilter: (
    item: RetrievalCoverageItem,
  ) => CoverageDiagnosticsFilterAction | null;
  isSearchPending: boolean;
  onApplyCoverageFilter: (field: CoverageDiagnosticsFilterField, value: string) => void;
}) {
  const standardItems = coverage?.standard_system ?? [];
  const aspectItems = coverage?.query_aspects ?? [];
  const warningCount = coverage?.warnings.length ?? 0;
  if (!standardItems.length && !aspectItems.length) {
    return (
      <TokenList
        description="No missing standard or search-aspect coverage was reported."
        items={[]}
        title="Coverage diagnostics"
      />
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Coverage diagnostics
        </div>
        <Badge variant={warningCount ? "warning" : "success"}>
          {warningCount ? `${warningCount} gap` : "covered"}
        </Badge>
      </div>
      <SectionHelpText>
        Coverage diagnostics show missing standards or query aspects and offer backend-supported filters when available.
      </SectionHelpText>
      <CoverageItemList
        filterFieldLabel={filterFieldLabel}
        formatFilterValue={formatFilterValue}
        getCoverageSuggestedAction={getCoverageSuggestedAction}
        getCoverageSuggestedFilter={getCoverageSuggestedFilter}
        isSearchPending={isSearchPending}
        items={standardItems}
        label="Standard coverage"
        onApplyCoverageFilter={onApplyCoverageFilter}
      />
      <CoverageItemList
        filterFieldLabel={filterFieldLabel}
        formatFilterValue={formatFilterValue}
        getCoverageSuggestedAction={getCoverageSuggestedAction}
        getCoverageSuggestedFilter={getCoverageSuggestedFilter}
        isSearchPending={isSearchPending}
        items={aspectItems}
        label="Aspect coverage"
        onApplyCoverageFilter={onApplyCoverageFilter}
      />
    </div>
  );
}

function CoverageItemList({
  filterFieldLabel,
  formatFilterValue,
  getCoverageSuggestedAction,
  getCoverageSuggestedFilter,
  isSearchPending,
  items,
  label,
  onApplyCoverageFilter,
}: {
  filterFieldLabel: (field: CoverageDiagnosticsFilterField) => string;
  formatFilterValue: (field: CoverageDiagnosticsFilterField, value: string) => string;
  getCoverageSuggestedAction: (item: RetrievalCoverageItem) => string;
  getCoverageSuggestedFilter: (
    item: RetrievalCoverageItem,
  ) => CoverageDiagnosticsFilterAction | null;
  isSearchPending: boolean;
  items: RetrievalCoverageItem[];
  label: string;
  onApplyCoverageFilter: (field: CoverageDiagnosticsFilterField, value: string) => void;
}) {
  if (!items.length) return null;
  return (
    <div className="grid gap-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        {label}
      </div>
      {items.map((item) => {
        const suggestedFilter = getCoverageSuggestedFilter(item);
        const actionable = item.status !== "covered" && suggestedFilter !== null;
        return (
          <div
            className="grid gap-2 rounded-md border border-border bg-card p-2 text-xs"
            key={`${label}-${item.field}-${item.value}`}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{humanize(item.value)}</span>
              <Badge variant={item.status === "covered" ? "success" : "warning"}>
                {item.status} / {item.selected_count}
              </Badge>
            </div>
            <div className="break-words text-muted-foreground">{item.reason}</div>
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md bg-muted/40 px-2 py-1.5">
              <span className="min-w-0 flex-1 break-words font-semibold text-foreground">
                {getCoverageSuggestedAction(item)}
              </span>
              {actionable ? (
                <Button
                  disabled={isSearchPending}
                  onClick={() =>
                    onApplyCoverageFilter(suggestedFilter.field, suggestedFilter.value)
                  }
                  size="sm"
                  title={`Apply ${filterFieldLabel(suggestedFilter.field)}=${formatFilterValue(
                    suggestedFilter.field,
                    suggestedFilter.value,
                  )}`}
                  type="button"
                  variant="outline"
                >
                  {isSearchPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ListFilter className="h-4 w-4" />
                  )}
                  Apply {filterFieldLabel(suggestedFilter.field)}
                </Button>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}
