import { X } from "lucide-react";

import { Button } from "../../../components/ui/button";
import {
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { formatCount } from "../model/retrieval-format";

export function SourceInventoryHeader({
  hasSourceFilters,
  isLoading,
  onClearFilters,
  shownCount,
  sourceCount,
}: {
  hasSourceFilters: boolean;
  isLoading: boolean;
  onClearFilters: () => void;
  shownCount: number;
  sourceCount: number;
}) {
  return (
    <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70">
      <div className="min-w-0">
        <CardTitle className="flex items-center gap-2">
          Trusted sources
          <HelpTooltip label="Trusted sources help">
            Source inventory shows what the retrieval system can search. The Use source action applies exact source scope to the query builder.
          </HelpTooltip>
        </CardTitle>
        <CardDescription>
          {isLoading
            ? "Loading inventory"
            : `${formatCount(shownCount, "source")} shown from ${sourceCount}`}
        </CardDescription>
      </div>
      {hasSourceFilters ? (
        <Button onClick={onClearFilters} size="sm" type="button" variant="outline">
          <X className="h-4 w-4" />
          Clear filters
        </Button>
      ) : null}
    </CardHeader>
  );
}
