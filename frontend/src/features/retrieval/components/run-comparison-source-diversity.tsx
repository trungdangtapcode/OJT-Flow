import { Badge } from "../../../components/ui/badge";
import type { RetrievalSourceDiversityComparisonView } from "../model/retrieval-source-diversity-types";
import { RunComparisonMetricCard } from "./run-comparison-summary-panels";
import { SourceListDelta } from "./source-list-delta";

export function RunComparisonSourceDiversity({
  comparison,
  formatPercent,
  formatSignedDelta,
}: {
  comparison: RetrievalSourceDiversityComparisonView;
  formatPercent: (value: number) => string;
  formatSignedDelta: (delta: number) => string;
}) {
  return (
    <div
      aria-label="Source diversity comparison"
      className="grid gap-2 rounded-lg border border-border/60 bg-card px-3 py-2 text-xs"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">
          Source diversity
        </span>
        <span className="flex flex-wrap justify-end gap-1.5">
          <Badge
            variant={
              comparison.duplicateSelectedSourceDelta > 0 ? "warning" : "success"
            }
          >
            duplicates {formatSignedDelta(comparison.duplicateSelectedSourceDelta)}
          </Badge>
          <Badge variant="muted">
            overlap {formatPercent(comparison.sourceOverlapRatio)}
          </Badge>
        </span>
      </div>
      <div className="break-words leading-5 text-muted-foreground">
        Shows whether tuning changed selected-source coverage after hybrid retrieval and reranking. More selected sources is useful when evidence must come from independent standards or source families; more duplicate selected sources needs review.
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        <RunComparisonMetricCard
          label="Selected sources"
          tone={comparison.selectedSourceDelta >= 0 ? "success" : "warning"}
          value={`${comparison.baseline.selectedSourceCount} -> ${comparison.active.selectedSourceCount}`}
        />
        <RunComparisonMetricCard
          label="Candidate sources"
          tone={comparison.candidateSourceDelta >= 0 ? "success" : "warning"}
          value={`${comparison.baseline.candidateSourceCount} -> ${comparison.active.candidateSourceCount}`}
        />
        <RunComparisonMetricCard
          label="Policy"
          tone={
            comparison.selectionModeChanged || comparison.lambdaChanged
              ? "warning"
              : "success"
          }
          value={comparison.selectionModeChanged ? "changed" : "stable"}
        />
      </div>
      <div className="grid gap-1">
        <SourceListDelta
          label="Added sources"
          sourceIds={comparison.addedSourceIds}
          variant="success"
        />
        <SourceListDelta
          label="Removed sources"
          sourceIds={comparison.removedSourceIds}
          variant="warning"
        />
        <SourceListDelta
          label="Retained sources"
          sourceIds={comparison.retainedSourceIds}
          variant="muted"
        />
      </div>
    </div>
  );
}
