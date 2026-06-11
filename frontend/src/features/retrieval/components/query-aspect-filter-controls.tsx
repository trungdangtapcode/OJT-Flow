export { QueryAspectFilterBadges } from "./query-aspect-filter-badges";
import { QueryAspectFilterAction } from "./query-aspect-filter-action";
import type {
  QueryAspectFilterApplyHandler,
  QueryAspectFilterEntryView,
} from "./query-aspect-plan-types";

export function QueryAspectFilterControls({
  aspectId,
  entries,
  isSearchPending,
  onApplyFilter,
}: {
  aspectId: string;
  entries: QueryAspectFilterEntryView[];
  isSearchPending: boolean;
  onApplyFilter: QueryAspectFilterApplyHandler;
}) {
  if (!entries.length) {
    return null;
  }

  return (
    <div className="flex min-w-0 flex-wrap gap-1.5">
      {entries.map((entry) => (
        <QueryAspectFilterAction
          aspectId={aspectId}
          entry={entry}
          isSearchPending={isSearchPending}
          key={`${aspectId}-${entry.field}-${entry.value}`}
          onApplyFilter={onApplyFilter}
        />
      ))}
    </div>
  );
}
