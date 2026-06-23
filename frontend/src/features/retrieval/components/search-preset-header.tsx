import { Badge } from "../../../components/ui/badge";

export function SearchPresetHeader({
  filteredCount,
  totalCount,
}: {
  filteredCount: number;
  totalCount: number;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
      <span className="text-xs font-semibold text-muted-foreground">Presets</span>
      <Badge variant="muted">
        {filteredCount}/{totalCount}
      </Badge>
    </div>
  );
}
