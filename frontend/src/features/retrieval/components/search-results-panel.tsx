import { Card } from "../../../components/ui/card";
import { buildAssistantRetrievalContextHref } from "../../../lib/assistant-context-links";
import { useHashTargetScroll } from "../../../lib/use-hash-target-scroll";
import { searchResultsViewModel } from "../model/search-results-view-model";
import { searchResultsContentProps } from "./search-results-content-props";
import { SearchResultsContent } from "./search-results-content";
import { EmptySearchResults, SearchResultsHeader } from "./search-results-header";
import type { SearchResultsProps } from "./search-results-panel-types";

export function SearchResults(props: SearchResultsProps) {
  const { packageData } = props;
  useHashTargetScroll([packageData?.trace.final_hit_ids.join("|") ?? ""]);
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
  const assistantHref = props.submittedSearchPayload?.query
    ? buildAssistantRetrievalContextHref({
        hitCount: packageData.hits.length,
        query: props.submittedSearchPayload.query,
        runId: props.runId,
        strategy: packageData.trace.strategy,
      })
    : null;

  return (
    <Card className="min-w-0 overflow-hidden">
      <SearchResultsHeader
        assistantHref={assistantHref}
        isStale={props.isStale}
        packageData={packageData}
      />
      <SearchResultsContent {...contentProps} />
    </Card>
  );
}
