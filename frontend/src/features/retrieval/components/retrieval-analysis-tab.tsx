import type * as React from "react";

import { RetrievalTracePanel } from "./retrieval-trace-panel";
import { GraphPanel } from "./retrieval-runtime-status";
import { GraphQueryPanel } from "./graph-query-panel";
import type { RetrievalResultsColumn } from "./retrieval-results-column";

export function RetrievalAnalysisTab({
  resultsColumn,
}: {
  resultsColumn: React.ComponentProps<typeof RetrievalResultsColumn>;
}) {
  return (
    <div className="grid min-w-0 gap-6">
      <RetrievalTracePanel {...resultsColumn.trace} />
      <div className="grid min-w-0 gap-6 2xl:grid-cols-2">
        <GraphPanel {...resultsColumn.graph} />
        <GraphQueryPanel {...resultsColumn.graphQuery} />
      </div>
    </div>
  );
}
