import type { RetrievalStandardSearchPlan } from "../../../types";
import {
  StandardSearchPlanGuardrails,
} from "./standard-search-governance-notes";
import { StandardSearchPlanHeader } from "./standard-search-plan-header";
import { StandardSearchStepCard } from "./standard-search-step-card";
import type { SearchPlanFilterAction, SearchPlanFilterField } from "./strategy-standard-types";

export function StandardSearchPlanPanel({
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  plan,
}: {
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  plan: RetrievalStandardSearchPlan | null;
}) {
  if (!plan || !plan.steps.length) {
    return null;
  }
  return (
    <div className="grid gap-3 rounded-lg border border-border/60 bg-card p-3">
      <StandardSearchPlanHeader plan={plan} />
      <div className="grid gap-2 lg:grid-cols-2">
        {plan.steps.slice(0, 4).map((step) => (
          <StandardSearchStepCard
            getSuggestedFilterAction={getSuggestedFilterAction}
            isSearchPending={isSearchPending}
            key={step.step_id}
            onApplyFilter={onApplyFilter}
            step={step}
          />
        ))}
      </div>
      <StandardSearchPlanGuardrails notes={plan.governance_notes} />
    </div>
  );
}
