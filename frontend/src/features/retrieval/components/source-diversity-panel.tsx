import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { humanize } from "../../../lib/utils";

export type DiversityStack = {
  candidateSourceCount: number;
  duplicateSelectedSourceCount: number;
  enabled: boolean;
  lambda: number | null;
  selectedHits: DiversitySelectionStack[];
  selectedSourceCount: number;
  selectionMode: string;
};

export type DiversitySelectionStack = {
  evidenceId: string;
  originalRank: number;
  reason: string;
  redundancyScore: number;
  relevanceScore: number;
  selectedRank: number;
  selectionScore: number;
  sourceId: string;
};

export function SourceDiversityPanel({
  diversity,
  isSearchPending,
}: {
  diversity: DiversityStack;
  isSearchPending: boolean;
}) {
  const visibleSelections = diversity.selectedHits
    .filter((selection) => selection.evidenceId && selection.sourceId)
    .slice(0, 4);
  const duplicateTone =
    diversity.duplicateSelectedSourceCount > 0 ? "warning" : "success";
  const modeLabel = humanize(diversity.selectionMode);
  return (
    <div className="grid gap-3 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            Source diversity
            <HelpTooltip label="Source diversity help">
              Shows how the backend selected a balanced evidence set after hybrid retrieval and reranking. This helps detect over-reliance on one source before the package is used downstream.
            </HelpTooltip>
          </div>
          <div className="mt-1 break-words text-sm leading-6 text-muted-foreground">
            {diversity.enabled
              ? "Final evidence was selected with source-aware diversity scoring so strong matches from repeated sources do not hide independent standards or policy evidence."
              : "Source diversity selection is disabled for this retrieval run; evidence follows score order only."}
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={diversity.enabled ? "success" : "warning"}>
            {diversity.enabled ? "enabled" : "disabled"}
          </Badge>
          <Badge variant="muted">{modeLabel}</Badge>
          <Badge variant={duplicateTone}>
            {formatCount(diversity.duplicateSelectedSourceCount, "duplicate")}
          </Badge>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        <DiversityMetricCard
          label="Candidate sources"
          value={diversity.candidateSourceCount}
        />
        <DiversityMetricCard
          label="Selected sources"
          value={diversity.selectedSourceCount}
        />
        <DiversityMetricCard
          label="Balance weight"
          value={diversity.lambda === null ? "n/a" : diversity.lambda.toFixed(2)}
        />
      </div>
      {isSearchPending ? (
        <div className="rounded-md border border-border bg-muted/25 px-3 py-2 text-sm font-semibold text-muted-foreground">
          Updating source-diversity trace...
        </div>
      ) : visibleSelections.length ? (
        <div className="grid gap-2">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Selected-hit rationale
          </div>
          {visibleSelections.map((selection) => (
            <div
              className="grid gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-xs"
              key={`${selection.selectedRank}:${selection.evidenceId}`}
            >
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
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-border bg-muted/25 px-3 py-2 text-sm font-semibold text-muted-foreground">
          No selected-hit diversity trace was returned for this run.
        </div>
      )}
    </div>
  );
}

function DiversityMetricCard({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div className="rounded-md border border-border bg-muted/20 px-3 py-2">
      <div className="text-xs font-black uppercase text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-xl font-black tabular-nums">{value}</div>
    </div>
  );
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
