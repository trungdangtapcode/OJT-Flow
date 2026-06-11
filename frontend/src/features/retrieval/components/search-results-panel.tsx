import { Card } from "../../../components/ui/card";
import { searchResultsViewModel } from "../model/search-results-view-model";
import { searchResultsContentProps } from "./search-results-content-props";
import { SearchResultsContent } from "./search-results-content";
import { EmptySearchResults, SearchResultsHeader } from "./search-results-header";
import type { SearchResultsProps } from "./search-results-panel-types";

export function SearchResults(props: SearchResultsProps) {
  const { packageData } = props;
  if (!packageData) {
    return <EmptySearchResults />;
  }

  const view = searchResultsViewModel({
    activeFilters: props.activeFilters,
    packageData,
    relevanceJudgments: props.relevanceJudgments,
    runId: props.runId,
    submittedSearchPayload: props.submittedSearchPayload,
  });
  const contentProps = searchResultsContentProps({ packageData, props, view });

  return (
    <Card className="min-w-0 overflow-hidden">
      <SearchResultsHeader isStale={props.isStale} packageData={packageData} />
      <SearchResultsContent {...contentProps} />
    </Card>
  );
}
