import { Badge } from "../../../components/ui/badge";
import type { DiversitySelectionStack } from "../model/retrieval-source-diversity-types";

export function SourceDiversityRationale({
  isSearchPending,
  selections,
}: {
  isSearchPending: boolean;
  selections: DiversitySelectionStack[];
}) {
  if (isSearchPending) {
    return (
      <div className="rounded-lg border border-border/60 bg-muted/25 px-3 py-2 text-sm font-semibold text-muted-foreground">
        Updating source-diversity trace...
      </div>
    );
  }

  if (!selections.length) {
    return (
      <div className="rounded-lg border border-border/60 bg-muted/25 px-3 py-2 text-sm font-semibold text-muted-foreground">
        No selected-hit diversity trace was returned for this run.
      </div>
    );
  }

  return (
    <div className="grid gap-2">
      <div className="text-xs font-black uppercase text-muted-foreground">
        Selected-hit rationale
      </div>
      {selections.map((selection) => (
        <SourceDiversityRationaleRow
          key={`${selection.selectedRank}:${selection.evidenceId}`}
          selection={selection}
        />
      ))}
    </div>
  );
}

function SourceDiversityRationaleRow({
  selection,
}: {
  selection: DiversitySelectionStack;
}) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <Badge variant="muted">#{selection.selectedRank}</Badge>
          <span className="min-w-0 break-words font-black">
            {selection.sourceId}
          </span>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant="muted">original #{selection.originalRank}</Badge>
          <Badge variant={selection.redundancyScore > 0 ? "warning" : "success"}>
            redundancy {selection.redundancyScore.toFixed(2)}
          </Badge>
          <Badge variant="muted">
            score {selection.selectionScore.toFixed(3)}
          </Badge>
        </div>
      </div>
      <div className="break-words leading-5 text-muted-foreground">
        {selection.reason}
      </div>
    </div>
  );
}
