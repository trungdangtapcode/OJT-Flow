import { HelpTooltip } from "../../../components/ui/help-tooltip";

export function SearchPlanRunOrder() {
  return (
    <div className="grid gap-1.5 rounded-md border border-border bg-background px-2 py-1.5 text-xs">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-black uppercase text-muted-foreground">Run order</span>
        <HelpTooltip label="Retrieval task order help">
          Start with required local OJTFlow searches because those can produce audited evidence. External medical-index tasks are follow-up links or copied queries for manual source review.
        </HelpTooltip>
      </div>
      <ol className="grid gap-1 pl-4 text-muted-foreground">
        <li className="list-decimal break-words">
          Run required local corpus tasks to collect trusted evidence inside OJTFlow.
        </li>
        <li className="list-decimal break-words">
          Apply supported filters if the plan suggests a narrower source, standard, or trust scope.
        </li>
        <li className="list-decimal break-words">
          Review external medical-index follow-ups only as manual context; they are not imported evidence until indexed.
        </li>
      </ol>
    </div>
  );
}
