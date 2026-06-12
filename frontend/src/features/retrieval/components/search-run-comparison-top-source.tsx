import type { SearchRunComparisonPanelView } from "./search-run-comparison-types";

export function SearchRunComparisonTopSource({
  comparison,
}: {
  comparison: Pick<SearchRunComparisonPanelView, "topSourceAfter" | "topSourceBefore">;
}) {
  return (
    <div className="break-words text-xs font-semibold text-muted-foreground">
      Top source: {comparison.topSourceBefore ?? "none"} to{" "}
      {comparison.topSourceAfter ?? "none"}
    </div>
  );
}
