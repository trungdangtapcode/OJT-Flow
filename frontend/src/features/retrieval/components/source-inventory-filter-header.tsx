import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";

export function SourceInventoryFilterHeader({
  sourceCount,
  shownCount,
}: {
  sourceCount: number;
  shownCount: number;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
      <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
        Source inventory filters
        <HelpTooltip label="Source inventory filters help">
          Inventory filters inspect available trusted sources. Use source scope only when you intentionally want evidence from one exact source.
        </HelpTooltip>
      </div>
      <Badge variant="muted">
        {shownCount}/{sourceCount}
      </Badge>
    </div>
  );
}
