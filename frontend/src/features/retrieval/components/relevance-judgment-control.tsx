import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import {
  judgmentBadgeVariant,
  judgmentLabel,
  relevanceJudgmentOptions,
  type RelevanceJudgmentValue,
} from "../model/retrieval-judgment-model";
import { SectionHelpText } from "./section-help-text";

export type RelevanceJudgmentControlValue = {
  value: RelevanceJudgmentValue;
} | null;

export function RelevanceJudgmentControl({
  judgment,
  onSetJudgment,
}: {
  judgment: RelevanceJudgmentControlValue;
  onSetJudgment: (value: RelevanceJudgmentValue) => void;
}) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
          Relevance judgment
          <HelpTooltip label="Relevance judgment help">
            Mark whether this evidence answers the search, is stale, is unsafe, or is blocked by source policy. These labels feed judgment metrics and comparison reports.
          </HelpTooltip>
        </div>
        {judgment ? (
          <Badge variant={judgmentBadgeVariant(judgment.value)}>
            {judgmentLabel(judgment.value)}
          </Badge>
        ) : (
          <Badge variant="muted">unjudged</Badge>
        )}
      </div>
      <SectionHelpText>
        Use relevant for direct support, partial for incomplete support, irrelevant when it misses the query, unsafe for risky content, stale for old guidance, and policy blocked when source governance forbids use.
      </SectionHelpText>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {relevanceJudgmentOptions.map((option) => {
          const active = judgment?.value === option.value;
          return (
            <Button
              aria-pressed={active}
              key={option.value}
              onClick={() => onSetJudgment(option.value)}
              size="sm"
              title={active ? "Clear this relevance judgment" : option.description}
              type="button"
              variant={active ? option.activeVariant : "outline"}
            >
              {option.label}
            </Button>
          );
        })}
      </div>
    </div>
  );
}
