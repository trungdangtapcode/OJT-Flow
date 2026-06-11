import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { SectionHelpText } from "./section-help-text";
import type { RetrievalRankChangeView } from "./run-comparison-detail-types";

export function RunComparisonRankChanges({
  formatCount,
  rankChanges,
}: {
  formatCount: (count: number, singular: string) => string;
  rankChanges: RetrievalRankChangeView[];
}) {
  if (!rankChanges.length) {
    return (
      <div className="grid gap-1 rounded-md border border-border bg-card px-3 py-2">
        <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
          <span className="text-xs font-bold text-muted-foreground">Rank movement</span>
          <Badge variant="success">stable</Badge>
        </div>
        <SectionHelpText>
          Stable rank means retained evidence kept the same ordering between baseline and active runs.
        </SectionHelpText>
      </div>
    );
  }
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
          Rank movement
          <HelpTooltip label="Rank movement help">
            Rank movement only compares evidence retained in both runs. An item moving up means it ranked closer to the top in the active run.
          </HelpTooltip>
        </span>
        <Badge variant="warning">{formatCount(rankChanges.length, "changed rank")}</Badge>
      </div>
      <SectionHelpText>
        Use rank movement to debug relevance tuning. Large movements can come from query wording, filters, reranking, or rule-pack changes.
      </SectionHelpText>
      <div className="grid gap-1">
        {rankChanges.slice(0, 4).map((change) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2 text-xs"
            key={change.evidenceId}
          >
            <span className="break-words font-bold">{change.evidenceId}</span>
            <span className="flex min-w-0 flex-wrap gap-1.5 text-muted-foreground">
              <Badge variant={change.rankDelta < 0 ? "success" : "warning"}>
                {change.rankDelta < 0 ? "up" : "down"} {Math.abs(change.rankDelta)}
              </Badge>
              <span>
                #{change.fromRank} to #{change.toRank}
              </span>
            </span>
          </div>
        ))}
        {rankChanges.length > 4 ? (
          <div className="text-xs font-semibold text-muted-foreground">
            +{formatCount(rankChanges.length - 4, "more changed rank")}
          </div>
        ) : null}
      </div>
    </div>
  );
}
