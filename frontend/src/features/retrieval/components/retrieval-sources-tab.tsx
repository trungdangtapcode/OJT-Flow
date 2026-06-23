import type * as React from "react";

import { RetrievalFreshnessPanel } from "./retrieval-freshness-panel";
import { IntegrityPanel } from "./retrieval-runtime-status";
import { SourceInventoryPanel } from "./source-inventory-panel";
import type { RetrievalResultsColumn } from "./retrieval-results-column";

export function RetrievalSourcesTab({
  resultsColumn,
}: {
  resultsColumn: React.ComponentProps<typeof RetrievalResultsColumn>;
}) {
  return (
    <div className="grid min-w-0 gap-6">
      <SourceInventoryPanel {...resultsColumn.sourceInventory} />
      <RetrievalFreshnessPanel {...resultsColumn.freshness} />
      <IntegrityPanel {...resultsColumn.integrity} />
    </div>
  );
}
