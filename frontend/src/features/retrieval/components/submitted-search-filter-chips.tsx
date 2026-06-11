import type { ActiveFilterBarEntry } from "./active-filter-bar";

export function SubmittedSearchFilterChips({ filters }: { filters: ActiveFilterBarEntry[] }) {
  if (!filters.length) {
    return null;
  }

  return (
    <div className="flex min-w-0 flex-wrap gap-1.5">
      {filters.map((filter) => (
        <span
          className="max-w-full break-words rounded-full border border-primary/20 bg-primary/10 px-2 py-1 text-xs font-bold text-foreground"
          key={filter.field}
        >
          {filter.label}: {filter.displayValue}
        </span>
      ))}
    </div>
  );
}
