import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";
import { TokenList } from "./token-list";
import { QueryProfileFilterActions } from "./query-profile-filter-actions";
import { QueryProfileRuleList } from "./query-profile-rule-list";
import type {
  QueryProfileCardView,
  QueryProfileFilterEntryView,
} from "./query-profile-card-types";
export type {
  QueryProfileCardView,
  QueryProfileFilterEntryView,
} from "./query-profile-card-types";

export function QueryProfileCard({
  filterEntries,
  isSearchPending,
  onApplyFilter,
  profile,
  routeHelpText,
}: {
  filterEntries: QueryProfileFilterEntryView[];
  isSearchPending: boolean;
  onApplyFilter: (suggestion: FilterSuggestionStack) => void;
  profile: QueryProfileCardView | null;
  routeHelpText: string;
}) {
  if (!profile) {
    return <TokenList items={[]} title="Query profile" />;
  }
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-card p-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="break-words font-bold">{profile.label}</span>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant="default">{humanize(profile.complexity)}</Badge>
          <Badge title={routeHelpText} variant="muted">
            {humanize(profile.route)}
          </Badge>
        </div>
      </div>
      <div className="break-words text-muted-foreground">{profile.description}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant="muted">{humanize(profile.retrievalMode)}</Badge>
        {filterEntries.map((entry) => (
          <Badge
            key={`${entry.field}-${entry.value}`}
            variant={entry.applied ? "success" : "muted"}
          >
            {entry.label}={entry.displayValue}
          </Badge>
        ))}
      </div>
      <QueryProfileFilterActions
        filterEntries={filterEntries}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        profile={profile}
      />
      <QueryProfileRuleList ruleIds={profile.ruleIds} />
    </div>
  );
}
