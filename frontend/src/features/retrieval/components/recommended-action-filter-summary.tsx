import type {
  RecommendedActionFilter,
  RecommendedActionFilterField,
} from "./recommended-actions-types";

export function RecommendedActionFilterSummary({
  filterAction,
  filterFieldLabel,
  formatFilterValue,
}: {
  filterAction: RecommendedActionFilter | null;
  filterFieldLabel: (field: RecommendedActionFilterField) => string;
  formatFilterValue: (field: RecommendedActionFilterField, value: string) => string;
}) {
  if (!filterAction) return null;
  return (
    <div className="break-words rounded-md bg-muted px-2 py-1 text-xs font-semibold text-muted-foreground">
      {filterFieldLabel(filterAction.field)}:{" "}
      {formatFilterValue(filterAction.field, filterAction.value)}
    </div>
  );
}
