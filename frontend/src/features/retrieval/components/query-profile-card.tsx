import { CheckCircle2, ListFilter, Loader2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";
import { TokenList } from "./token-list";

export type QueryProfileCardView = {
  complexity: string;
  description: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
  ruleIds: string[];
};

export type QueryProfileFilterEntryView = {
  applied: boolean;
  displayValue: string;
  field: string;
  label: string;
  supported: boolean;
  value: string;
};

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
    <div className="grid gap-2 rounded-md border border-border bg-card p-2 text-xs">
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
      {filterEntries.length ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {filterEntries.map((entry) =>
            entry.supported ? (
              <Button
                disabled={isSearchPending || entry.applied}
                key={`${entry.field}-${entry.value}-apply`}
                onClick={() =>
                  onApplyFilter({
                    applied: false,
                    confidence: 1,
                    field: entry.field,
                    reason: `Suggested by query profile ${profile.profileId}.`,
                    value: entry.value,
                  })
                }
                size="sm"
                title={`Apply ${entry.label}=${entry.displayValue}`}
                type="button"
                variant={entry.applied ? "secondary" : "outline"}
              >
                {entry.applied ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : isSearchPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ListFilter className="h-4 w-4" />
                )}
                {entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`}
              </Button>
            ) : (
              <Badge key={`${entry.field}-${entry.value}-unsupported`} variant="warning">
                unsupported {humanize(entry.field)}
              </Badge>
            ),
          )}
        </div>
      ) : null}
      {profile.ruleIds.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {profile.ruleIds.map((ruleId) => (
            <code
              className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px]"
              key={ruleId}
            >
              {ruleId}
            </code>
          ))}
        </div>
      ) : null}
    </div>
  );
}
