import { X } from "lucide-react";

import { Button } from "../../../components/ui/button";

export type ActiveFilterBarEntry<TField extends string = string> = {
  field: TField;
  label: string;
  displayValue: string;
};

export function ActiveFilterBar<TField extends string>({
  filters,
  isSearchPending,
  onClearAll,
  onRemove,
}: {
  filters: ActiveFilterBarEntry<TField>[];
  isSearchPending: boolean;
  onClearAll: () => void;
  onRemove: (field: TField) => void;
}) {
  if (!filters.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">Active filters</div>
        <Button
          disabled={isSearchPending}
          onClick={onClearAll}
          size="sm"
          type="button"
          variant="ghost"
        >
          Clear all
        </Button>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {filters.map((filter) => (
          <span
            className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-primary/25 bg-primary/10 px-2 py-1 text-xs font-bold text-foreground"
            key={filter.field}
          >
            <span className="min-w-0 break-words">
              {filter.label}: {filter.displayValue}
            </span>
            <button
              aria-label={`Remove ${filter.label} filter`}
              className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-card hover:text-foreground focus-ring disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSearchPending}
              onClick={() => onRemove(filter.field)}
              title={`Remove ${filter.label} filter`}
              type="button"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}
