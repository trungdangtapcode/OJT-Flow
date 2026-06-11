import type * as React from "react";

import { QueryBuilderPanel } from "./query-builder-panel";
import { SearchPlanPreviewPanel } from "./search-plan-preview-panel";
import { SearchRunHistoryPanel } from "./search-run-history-panel";

export function RetrievalQueryColumn({
  queryBuilder,
  searchPlanPreview,
  searchRunHistory,
}: {
  queryBuilder: React.ComponentProps<typeof QueryBuilderPanel>;
  searchPlanPreview: React.ComponentProps<typeof SearchPlanPreviewPanel>;
  searchRunHistory: React.ComponentProps<typeof SearchRunHistoryPanel>;
}) {
  return (
    <div className="grid min-w-0 gap-5">
      <QueryBuilderPanel {...queryBuilder} />
      <SearchPlanPreviewPanel {...searchPlanPreview} />
      <SearchRunHistoryPanel {...searchRunHistory} />
    </div>
  );
}
