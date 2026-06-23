import type * as React from "react";

import { QueryBuilderPanel } from "./query-builder-panel";
import { SearchPlanPreviewPanel } from "./search-plan-preview-panel";
import {
  RetrievalRuntimeStatusStrip,
} from "./retrieval-runtime-status";
import { SearchResults } from "./search-results-panel";
import type { RetrievalQueryColumn } from "./retrieval-query-column";
import type { RetrievalResultsColumn } from "./retrieval-results-column";

export function RetrievalSearchTab({
  queryColumn,
  resultsColumn,
}: {
  queryColumn: React.ComponentProps<typeof RetrievalQueryColumn>;
  resultsColumn: React.ComponentProps<typeof RetrievalResultsColumn>;
}) {
  const hasResults = Boolean(resultsColumn.searchResults.packageData);

  return (
    <div className="grid gap-4">
      <QueryBuilderPanel {...queryColumn.queryBuilder} />

      {hasResults ? (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="grid min-w-0 gap-4">
            {resultsColumn.runtimeStatus ? (
              <RetrievalRuntimeStatusStrip {...resultsColumn.runtimeStatus} />
            ) : null}
            <SearchResults {...resultsColumn.searchResults} />
          </div>
          <aside className="grid min-w-0 content-start gap-4">
            <SearchPlanPreviewPanel {...queryColumn.searchPlanPreview} />
          </aside>
        </div>
      ) : (
        <SearchResults {...resultsColumn.searchResults} />
      )}
    </div>
  );
}
