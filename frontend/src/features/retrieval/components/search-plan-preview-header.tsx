import { BrainCircuit } from "lucide-react";

import {
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { SearchPlanCopyAction } from "./search-plan-copy-action";

export function SearchPlanPreviewHeader({
  copied,
  onCopyPlan,
}: {
  copied: boolean;
  onCopyPlan: () => void;
}) {
  return (
    <CardHeader className="border-b border-border bg-card/70">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <CardTitle className="flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-primary" />
            Search plan
            <HelpTooltip label="Search plan help">
              Backend-generated plan for this evidence search. It explains the route, query rewrites, medical standards, external search hints, and suggested filters.
            </HelpTooltip>
          </CardTitle>
          <CardDescription>
            Route, aspects, rewrites, and medical follow-up searches.
          </CardDescription>
        </div>
        <SearchPlanCopyAction copied={copied} onCopyPlan={onCopyPlan} />
      </div>
    </CardHeader>
  );
}
