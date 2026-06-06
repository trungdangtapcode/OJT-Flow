import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { SectionHelpText } from "./section-help-text";

export type RelevanceJudgmentValue = "relevant" | "partial" | "not_relevant";

export type RelevanceJudgmentControlValue = {
  value: RelevanceJudgmentValue;
} | null;

const relevanceJudgmentOptions: Array<{
  activeVariant: "default" | "secondary" | "destructive";
  description: string;
  label: string;
  value: RelevanceJudgmentValue;
}> = [
  {
    activeVariant: "default",
    description: "Mark this evidence as relevant for the submitted query.",
    label: "Relevant",
    value: "relevant",
  },
  {
    activeVariant: "secondary",
    description: "Mark this evidence as partially relevant for the submitted query.",
    label: "Partial",
    value: "partial",
  },
  {
    activeVariant: "destructive",
    description: "Mark this evidence as not relevant for the submitted query.",
    label: "Not relevant",
    value: "not_relevant",
  },
];

export function RelevanceJudgmentControl({
  judgment,
  onSetJudgment,
}: {
  judgment: RelevanceJudgmentControlValue;
  onSetJudgment: (value: RelevanceJudgmentValue) => void;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
          Relevance judgment
          <HelpTooltip label="Relevance judgment help">
            Mark whether this evidence actually answers the submitted search. These labels feed judgment metrics and comparison reports.
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
        Use relevant for direct support, partial for useful but incomplete support, and not relevant when the hit does not answer the query.
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

function judgmentLabel(value: RelevanceJudgmentValue): string {
  if (value === "relevant") return "Relevant";
  if (value === "partial") return "Partial";
  return "Not relevant";
}

function judgmentBadgeVariant(
  value: RelevanceJudgmentValue,
): "success" | "warning" | "destructive" {
  if (value === "relevant") return "success";
  if (value === "partial") return "warning";
  return "destructive";
}
