import { ListFilter, Loader2 } from "lucide-react";

import { cn, humanize } from "../../../lib/utils";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";
import { TokenList } from "./token-list";

export function FilterSuggestionList({
  isSearchPending,
  isSuggestionSupported,
  onApplySuggestion,
  suggestions,
}: {
  isSearchPending: boolean;
  isSuggestionSupported: (field: string) => boolean;
  onApplySuggestion: (suggestion: FilterSuggestionStack) => void;
  suggestions: FilterSuggestionStack[];
}) {
  if (!suggestions.length) {
    return <TokenList items={[]} title="Suggested filters" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Suggested filters
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {suggestions.map((suggestion) => {
          const actionable = !suggestion.applied && isSuggestionSupported(suggestion.field);
          return (
            <span
              className={cn(
                "inline-flex max-w-full items-center gap-1.5 rounded-full px-2 py-1 text-xs font-bold",
                suggestion.applied
                  ? "bg-emerald-100 text-emerald-900"
                  : "bg-card text-muted-foreground",
              )}
              key={`${suggestion.field}-${suggestion.value}`}
              title={suggestion.reason}
            >
              <span className="break-words">
                {humanize(suggestion.field)}={humanize(suggestion.value)}
              </span>
              <span className="tabular-nums">
                {Math.round(suggestion.confidence * 100)}%
              </span>
              {suggestion.applied ? <span>applied</span> : null}
              {actionable ? (
                <button
                  aria-label={`Apply ${humanize(suggestion.field)} ${humanize(suggestion.value)} filter`}
                  className="inline-flex h-6 shrink-0 items-center gap-1 rounded-full border border-border bg-muted px-2 text-[11px] font-black text-foreground hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isSearchPending}
                  onClick={() => onApplySuggestion(suggestion)}
                  title={`Apply ${humanize(suggestion.field)}=${humanize(suggestion.value)}`}
                  type="button"
                >
                  {isSearchPending ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <ListFilter className="h-3 w-3" />
                  )}
                  Apply
                </button>
              ) : null}
            </span>
          );
        })}
      </div>
    </div>
  );
}
