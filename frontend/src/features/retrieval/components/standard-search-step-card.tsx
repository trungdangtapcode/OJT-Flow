import { ListFilter } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import {
  filterFieldLabel,
  routeLabel,
  standardRouteBadgeVariant,
} from "./strategy-standard-format";
import { StandardSearchGovernanceNotes } from "./standard-search-governance-notes";
import { StandardSearchMatchReasons } from "./standard-search-match-reasons";
import type { StandardSearchStepCardProps } from "./standard-search-plan-types";

export function StandardSearchStepCard({
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  step,
}: StandardSearchStepCardProps) {
  const filterAction = getSuggestedFilterAction(step.suggested_filters);
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      <div className="grid min-w-0 gap-2 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
        <div className="min-w-0">
          <div className="break-words font-black">{step.label}</div>
          <div className="mt-1 flex min-w-0 flex-wrap items-center gap-1.5">
            <Badge variant="muted">P{step.priority}</Badge>
            <Badge variant="success">{step.standard_system}</Badge>
            <Badge variant={standardRouteBadgeVariant(step.route_type)}>
              {routeLabel(step.route_type)}
            </Badge>
          </div>
        </div>
        {filterAction ? (
          <Button
            disabled={isSearchPending}
            onClick={() => onApplyFilter(filterAction.field, filterAction.value)}
            size="sm"
            type="button"
            variant="outline"
          >
            <ListFilter className="h-4 w-4" />
            Apply {filterFieldLabel(filterAction.field)}
          </Button>
        ) : null}
      </div>
      <div className="break-words text-xs leading-5 text-muted-foreground">
        {step.rationale}
      </div>
      <StandardSearchMatchReasons metadata={step.metadata} />
      <div className="break-words rounded-md border border-border bg-card px-3 py-2 font-mono text-xs leading-5 text-foreground">
        {step.query}
      </div>
      <StandardSearchGovernanceNotes notes={step.governance_notes} />
    </div>
  );
}
