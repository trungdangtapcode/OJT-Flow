import type { RetrievalCoverage, RetrievalCoverageItem } from "../../../types";
import { CoverageDiagnosticsEmptyState } from "./coverage-diagnostics-empty-state";
import { CoverageDiagnosticsHeader } from "./coverage-diagnostics-header";
import { CoverageDiagnosticsItemList } from "./coverage-diagnostics-item-list";
import type {
  CoverageDiagnosticsActionHelpers,
  CoverageDiagnosticsFilterAction,
  CoverageDiagnosticsFilterField,
} from "./coverage-diagnostics-types";

export type {
  CoverageDiagnosticsFilterAction,
  CoverageDiagnosticsFilterField,
} from "./coverage-diagnostics-types";

export function CoverageDiagnosticsPanel({
  coverage,
  filterFieldLabel,
  formatFilterValue,
  getCoverageSuggestedAction,
  getCoverageSuggestedFilter,
  isSearchPending,
  onApplyCoverageFilter,
}: {
  coverage: RetrievalCoverage | null | undefined;
  filterFieldLabel: (field: CoverageDiagnosticsFilterField) => string;
  formatFilterValue: (field: CoverageDiagnosticsFilterField, value: string) => string;
  getCoverageSuggestedAction: (item: RetrievalCoverageItem) => string;
  getCoverageSuggestedFilter: (
    item: RetrievalCoverageItem,
  ) => CoverageDiagnosticsFilterAction | null;
  isSearchPending: boolean;
  onApplyCoverageFilter: (field: CoverageDiagnosticsFilterField, value: string) => void;
}) {
  const standardItems = coverage?.standard_system ?? [];
  const aspectItems = coverage?.query_aspects ?? [];
  const warningCount = coverage?.warnings.length ?? 0;
  if (!standardItems.length && !aspectItems.length) {
    return <CoverageDiagnosticsEmptyState />;
  }
  const actionHelpers: CoverageDiagnosticsActionHelpers = {
    filterFieldLabel,
    formatFilterValue,
    getCoverageSuggestedAction,
    getCoverageSuggestedFilter,
    isSearchPending,
    onApplyCoverageFilter,
  };
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <CoverageDiagnosticsHeader warningCount={warningCount} />
      <CoverageDiagnosticsItemList
        actionHelpers={actionHelpers}
        items={standardItems}
        label="Standard coverage"
      />
      <CoverageDiagnosticsItemList
        actionHelpers={actionHelpers}
        items={aspectItems}
        label="Aspect coverage"
      />
    </div>
  );
}
