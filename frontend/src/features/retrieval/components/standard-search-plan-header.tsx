import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { RetrievalStandardSearchPlan } from "../../../types";
import {
  formatCount,
  routeLabel,
  standardRouteBadgeVariant,
} from "./strategy-standard-format";

export function StandardSearchPlanHeader({
  plan,
}: {
  plan: RetrievalStandardSearchPlan;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
      <div className="min-w-0">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
          Healthcare search plan
          <HelpTooltip label="Healthcare search plan help">
            Backend-selected playbook for the next standards-aware search. It maps the query to FHIR, terminology, privacy, or external medical-search routes before downstream use.
          </HelpTooltip>
        </div>
        <div className="mt-1 break-words text-sm leading-6 text-muted-foreground">
          {plan.summary}
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
        <Badge variant={standardRouteBadgeVariant(plan.primary_route)}>
          {routeLabel(plan.primary_route)}
        </Badge>
        <Badge variant="muted">{formatCount(plan.steps.length, "step")}</Badge>
        {plan.missing_routes.length ? (
          <Badge variant="warning">
            {formatCount(plan.missing_routes.length, "missing route")}
          </Badge>
        ) : null}
      </div>
    </div>
  );
}
