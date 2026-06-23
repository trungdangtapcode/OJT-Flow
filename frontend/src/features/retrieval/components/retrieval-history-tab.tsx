import type * as React from "react";

import { SearchRunHistoryPanel } from "./search-run-history-panel";
import { RetrievalRegressionDashboard } from "./retrieval-regression-dashboard";
import type { RetrievalQueryColumn } from "./retrieval-query-column";

export function RetrievalHistoryTab({
  queryColumn,
}: {
  queryColumn: React.ComponentProps<typeof RetrievalQueryColumn>;
}) {
  return (
    <div className="grid min-w-0 gap-6">
      <SearchRunHistoryPanel {...queryColumn.searchRunHistory} />
      <RetrievalRegressionDashboard {...queryColumn.regressionDashboard} />
    </div>
  );
}
