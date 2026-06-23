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
    <div className="flex min-w-0 flex-wrap items-center gap-1.5">
      {filters.map((filter) => (
        <span
          className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/5 px-2 py-0.5 text-[11px] font-medium text-foreground"
          key={filter.field}
        >
          {filter.label}: {filter.displayValue}
          <button
            aria-label={`Remove ${filter.label}`}
            className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:text-foreground disabled:opacity-50"
            disabled={isSearchPending}
            onClick={() => onRemove(filter.field)}
            type="button"
          >
            <X className="h-2.5 w-2.5" />
          </button>
        </span>
      ))}
      <button
        className="text-[11px] font-medium text-muted-foreground hover:text-foreground disabled:opacity-50"
        disabled={isSearchPending}
        onClick={onClearAll}
        type="button"
      >
        Clear
      </button>
    </div>
  );
}
