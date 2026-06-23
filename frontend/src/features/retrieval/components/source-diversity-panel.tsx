import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { DiversityStack } from "../model/retrieval-source-diversity-types";
import { SourceDiversityMetricCard } from "./source-diversity-metric-card";
import {
  sourceDiversityBalanceWeightLabel,
  sourceDiversityDescription,
  sourceDiversityDuplicateBadgeView,
  sourceDiversityModeLabel,
  sourceDiversityStateBadgeView,
  visibleSourceDiversitySelections,
} from "./source-diversity-panel-view";
import { SourceDiversityRationale } from "./source-diversity-rationale";
export { RunComparisonSourceDiversity } from "./run-comparison-source-diversity";

export function SourceDiversityPanel({
  diversity,
  isSearchPending,
}: {
  diversity: DiversityStack;
  isSearchPending: boolean;
}) {
  const stateBadge = sourceDiversityStateBadgeView(diversity.enabled);
  const duplicateBadge = sourceDiversityDuplicateBadgeView(
    diversity.duplicateSelectedSourceCount,
  );

  return (
    <div className="grid gap-3 rounded-lg border border-border/60 bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            Source diversity
            <HelpTooltip label="Source diversity help">
              Shows how the backend selected a balanced evidence set after hybrid retrieval and reranking. This helps detect over-reliance on one source before the package is used downstream.
            </HelpTooltip>
          </div>
          <div className="mt-1 break-words text-sm leading-6 text-muted-foreground">
            {sourceDiversityDescription(diversity.enabled)}
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={stateBadge.variant}>{stateBadge.label}</Badge>
          <Badge variant="muted">{sourceDiversityModeLabel(diversity)}</Badge>
          <Badge variant={duplicateBadge.variant}>{duplicateBadge.label}</Badge>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        <SourceDiversityMetricCard
          label="Candidate sources"
          value={diversity.candidateSourceCount}
        />
        <SourceDiversityMetricCard
          label="Selected sources"
          value={diversity.selectedSourceCount}
        />
        <SourceDiversityMetricCard
          label="Balance weight"
          value={sourceDiversityBalanceWeightLabel(diversity)}
        />
      </div>
      <SourceDiversityRationale
        isSearchPending={isSearchPending}
        selections={visibleSourceDiversitySelections(diversity)}
      />
    </div>
  );
}
