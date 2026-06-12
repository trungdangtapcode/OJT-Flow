import type { RetrievalRecommendedAction } from "../../../types";
import type {
  RetrievalCockpitFilterAction,
  RetrievalCockpitFilterField,
} from "./retrieval-cockpit-filter-signals";

export function recommendedActionFilter(
  action: RetrievalRecommendedAction,
): RetrievalCockpitFilterAction | null {
  if (action.action_type !== "apply_filter") return null;
  return suggestedFilterAction(action.suggested_filter);
}

export function firstSupportedRecommendedAction(
  actions: RetrievalRecommendedAction[],
): RetrievalCockpitFilterAction | null {
  for (const action of actions) {
    const filterAction = recommendedActionFilter(action);
    if (filterAction) return filterAction;
  }
  return null;
}

function suggestedFilterAction(value: unknown): RetrievalCockpitFilterAction | null {
  const suggestedFilter = recordValue(value);
  for (const field of supportedFilterFields) {
    const filterValue = optionalStringValue(suggestedFilter[field]);
    if (filterValue) return { field, value: filterValue };
  }
  return null;
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

const supportedFilterFields: RetrievalCockpitFilterField[] = [
  "clinical_domain",
  "standard_system",
  "source_type",
  "trust_level",
  "source_id",
];
