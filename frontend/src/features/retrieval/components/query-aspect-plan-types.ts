import type {
  FilterSuggestionStack,
  QueryAspectStack,
} from "./search-plan-detail-panels";

export type QueryAspectFilterEntryView = {
  applied: boolean;
  displayValue: string;
  field: string;
  label: string;
  supported: boolean;
  value: string;
};

export type QueryAspectPlanItemView = QueryAspectStack & {
  filterEntries: QueryAspectFilterEntryView[];
};

export type QueryAspectFilterApplyHandler = (
  suggestion: FilterSuggestionStack,
) => void;
