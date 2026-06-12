import { Network } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import type { DiversitySelectionExplanationView } from "./hit-explanation-types";

export function DiversitySelectionExplanation({
  formatScore,
  selection,
}: {
  formatScore: (value: number) => string;
  selection: DiversitySelectionExplanationView | null;
}) {
  if (!selection) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Network className="h-3.5 w-3.5 shrink-0" />
        <span>Diversity selection</span>
      </div>
      <div className="grid gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <Badge variant="muted">selected #{selection.selectedRank}</Badge>
          <Badge variant="muted">original #{selection.originalRank}</Badge>
          <span className="font-mono font-semibold text-muted-foreground">
            relevance {formatScore(selection.relevanceScore)}
          </span>
          <span className="font-mono font-semibold text-muted-foreground">
            redundancy {formatScore(selection.redundancyScore)}
          </span>
          <span className="font-mono font-semibold text-muted-foreground">
            MMR {formatScore(selection.selectionScore)}
          </span>
        </div>
        <div className="break-words font-semibold text-muted-foreground">
          {selection.reason}
        </div>
      </div>
    </div>
  );
}
