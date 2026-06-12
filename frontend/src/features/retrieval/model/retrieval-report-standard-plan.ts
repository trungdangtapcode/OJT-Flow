import type { RetrievalPackage } from "../../../types";

export function retrievalStandardSearchPlanReport(packageData: RetrievalPackage) {
  const plan = packageData.standard_search_plan ?? null;
  if (!plan) {
    return null;
  }
  return {
    plan_id: plan.plan_id,
    summary: plan.summary,
    primary_route: plan.primary_route,
    missing_routes: plan.missing_routes,
    governance_notes: plan.governance_notes,
    steps: plan.steps.map((step) => ({
      step_id: step.step_id,
      label: step.label,
      standard_system: step.standard_system,
      route_type: step.route_type,
      priority: step.priority,
      query: step.query,
      rationale: step.rationale,
      suggested_filters: step.suggested_filters,
      governance_notes: step.governance_notes,
      metadata: step.metadata,
    })),
  };
}
