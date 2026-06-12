import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";

export function SearchPresetHeader({
  filteredCount,
  totalCount,
}: {
  filteredCount: number;
  totalCount: number;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
      <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
        Search presets
        <HelpTooltip label="Search presets help">
          Data-driven examples loaded from trusted knowledge configuration. Applying one fills the query builder but does not run search until you submit.
        </HelpTooltip>
      </div>
      <Badge variant="muted">
        {filteredCount}/{totalCount} data-driven
      </Badge>
    </div>
  );
}
