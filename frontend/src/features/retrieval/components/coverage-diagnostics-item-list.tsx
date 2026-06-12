import type { RetrievalCoverageItem } from "../../../types";
import { CoverageDiagnosticsItemRow } from "./coverage-diagnostics-item-row";
import type { CoverageDiagnosticsActionHelpers } from "./coverage-diagnostics-types";

export function CoverageDiagnosticsItemList({
  actionHelpers,
  items,
  label,
}: {
  actionHelpers: CoverageDiagnosticsActionHelpers;
  items: RetrievalCoverageItem[];
  label: string;
}) {
  if (!items.length) return null;
  return (
    <div className="grid gap-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        {label}
      </div>
      {items.map((item) => (
        <CoverageDiagnosticsItemRow
          actionHelpers={actionHelpers}
          item={item}
          key={`${label}-${item.field}-${item.value}`}
          label={label}
        />
      ))}
    </div>
  );
}
