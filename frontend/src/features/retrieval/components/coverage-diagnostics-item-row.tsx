import { ListFilter, Loader2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { RetrievalCoverageItem } from "../../../types";
import type { CoverageDiagnosticsActionHelpers } from "./coverage-diagnostics-types";

export function CoverageDiagnosticsItemRow({
  actionHelpers,
  item,
  label,
}: {
  actionHelpers: CoverageDiagnosticsActionHelpers;
  item: RetrievalCoverageItem;
  label: string;
}) {
  const suggestedFilter = actionHelpers.getCoverageSuggestedFilter(item);
  const actionable = item.status !== "covered" && suggestedFilter !== null;
  return (
    <div
      className="grid gap-2 rounded-lg border border-border/60 bg-card p-2 text-xs"
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
          {actionHelpers.getCoverageSuggestedAction(item)}
        </span>
        {actionable ? (
          <Button
            disabled={actionHelpers.isSearchPending}
            onClick={() =>
              actionHelpers.onApplyCoverageFilter(suggestedFilter.field, suggestedFilter.value)
            }
            size="sm"
            title={`Apply ${actionHelpers.filterFieldLabel(
              suggestedFilter.field,
            )}=${actionHelpers.formatFilterValue(
              suggestedFilter.field,
              suggestedFilter.value,
            )}`}
            type="button"
            variant="outline"
          >
            {actionHelpers.isSearchPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ListFilter className="h-4 w-4" />
            )}
            Apply {actionHelpers.filterFieldLabel(suggestedFilter.field)}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
