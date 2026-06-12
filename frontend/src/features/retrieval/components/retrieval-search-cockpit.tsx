import type {
  RetrievalSearchCockpitView,
} from "../model/retrieval-cockpit-view-model";
import { SearchCockpitHeader } from "./search-cockpit-header";
import {
  SearchCockpitSectionStack,
  type SearchCockpitSectionStackProps,
} from "./search-cockpit-section-stack";

type RetrievalSearchCockpitProps = Pick<
  SearchCockpitSectionStackProps,
  | "filterFieldLabel"
  | "getSuggestedFilterAction"
  | "isSearchPending"
  | "onApplyFilter"
  | "onClearAllFilters"
  | "onClearSourceScope"
> & {
  copyTextToClipboard: (text: string) => Promise<void>;
  reportJson: string;
  view: RetrievalSearchCockpitView;
};

export function RetrievalSearchCockpit({
  copyTextToClipboard,
  filterFieldLabel,
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  onClearAllFilters,
  onClearSourceScope,
  reportJson,
  view,
}: RetrievalSearchCockpitProps) {
  return (
    <section
      aria-label="Retrieval cockpit"
      className="grid gap-3 rounded-md border border-border bg-muted/20 p-3"
    >
      <SearchCockpitHeader
        copyTextToClipboard={copyTextToClipboard}
        reportJson={reportJson}
        view={view}
      />

      <SearchCockpitSectionStack
        filterFieldLabel={filterFieldLabel}
        getSuggestedFilterAction={getSuggestedFilterAction}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        onClearAllFilters={onClearAllFilters}
        onClearSourceScope={onClearSourceScope}
        view={view}
      />
    </section>
  );
}
