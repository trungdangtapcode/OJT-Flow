import { BrainCircuit } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { supportStatusBadgeVariant } from "./evidence-support-status";
import type { HitMatchExplanationView } from "./evidence-interpretation-guidance-types";
import { HitMatchExplanationMetric } from "./hit-match-explanation-metric";

export function HitMatchExplanationPanel({
  explanation,
  formatCount,
}: {
  explanation: HitMatchExplanationView;
  formatCount: (count: number, singular: string) => string;
}) {
  return (
    <div
      aria-label="Why this evidence matched"
      className="grid gap-2 rounded-md border border-border bg-muted/20 p-2"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
          <BrainCircuit className="h-3.5 w-3.5 shrink-0" />
          <span>Why this matched</span>
        </div>
        <Badge variant={supportStatusBadgeVariant(explanation.supportStatus)}>
          {humanize(explanation.supportStatus)}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <HitMatchExplanationMetric
          label="Top driver"
          value={explanation.topScoreDriver ?? "not reported"}
        />
        <HitMatchExplanationMetric
          label="Evidence pack"
          value={
            explanation.bucketLabels.length
              ? explanation.bucketLabels.join(", ")
              : "unbucketed"
            }
        />
        <HitMatchExplanationMetric
          label="Terms"
          value={
            explanation.matchedTerms.length
              ? explanation.matchedTerms.join(", ")
              : "no exact terms"
            }
        />
        <HitMatchExplanationMetric
          label="Traceability"
          value={`${formatCount(explanation.provenanceCount, "provenance field")}, ${formatCount(
            explanation.rankingSignalCount,
            "ranking signal",
          )}`}
        />
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {explanation.conceptLabels.map((label) => (
          <Badge className="max-w-full break-words" key={`concept-${label}`} variant="muted">
            {label}
          </Badge>
        ))}
        {explanation.aspectLabels.map((label) => (
          <Badge className="max-w-full break-words" key={`aspect-${label}`} variant="muted">
            {label}
          </Badge>
        ))}
        {!explanation.conceptLabels.length && !explanation.aspectLabels.length ? (
          <span className="text-xs font-semibold text-muted-foreground">
            No concept or query-aspect grounding was reported for this hit.
          </span>
        ) : null}
      </div>
    </div>
  );
}
