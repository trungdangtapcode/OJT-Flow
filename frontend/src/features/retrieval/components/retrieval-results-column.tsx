import type * as React from "react";

import {
  GraphPanel,
  IntegrityPanel,
  RetrievalRuntimeStatusStrip,
} from "./retrieval-runtime-status";
import { RetrievalTracePanel } from "./retrieval-trace-panel";
import { SearchResults } from "./search-results-panel";
import { SourceInventoryPanel } from "./source-inventory-panel";

export function RetrievalResultsColumn({
  graph,
  integrity,
  runtimeStatus,
  searchResults,
  sourceInventory,
  trace,
}: {
  graph: React.ComponentProps<typeof GraphPanel>;
  integrity: React.ComponentProps<typeof IntegrityPanel>;
  runtimeStatus: React.ComponentProps<typeof RetrievalRuntimeStatusStrip> | null;
  searchResults: React.ComponentProps<typeof SearchResults>;
  sourceInventory: React.ComponentProps<typeof SourceInventoryPanel>;
  trace: React.ComponentProps<typeof RetrievalTracePanel>;
}) {
  return (
    <div className="grid min-w-0 gap-5">
      {runtimeStatus ? <RetrievalRuntimeStatusStrip {...runtimeStatus} /> : null}
      <SearchResults {...searchResults} />
      <div className="grid min-w-0 gap-5 2xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.9fr)]">
        <RetrievalTracePanel {...trace} />
        <GraphPanel {...graph} />
      </div>
      <IntegrityPanel {...integrity} />
      <SourceInventoryPanel {...sourceInventory} />
    </div>
  );
}
