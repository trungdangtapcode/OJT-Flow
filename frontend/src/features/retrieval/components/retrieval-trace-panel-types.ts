import type {
  RetrievalCoverage,
  RetrievalCoverageItem,
  RetrievalQualitySignal,
  RetrievalQueryVariant,
  RetrievalRecommendedAction,
} from "../../../types";
import type {
  CoverageDiagnosticsFilterAction,
  CoverageDiagnosticsFilterField,
} from "./coverage-diagnostics-panel";
import type { QueryAnalysisBlockView } from "./query-analysis-block-types";
import type {
  RecommendedActionFilter,
  RecommendedActionFilterField,
} from "./recommended-actions-panel";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";

export type RetrievalTracePanelView = {
  coverage: RetrievalCoverage | null | undefined;
  facts: { label: string; value: string }[];
  filtersApplied: Record<string, unknown>;
  qualitySignals: RetrievalQualitySignal[];
  queryAnalysis: QueryAnalysisBlockView | null;
  queryVariants: RetrievalQueryVariant[];
  recommendedActions: RetrievalRecommendedAction[];
  safetyFlags: string[];
  warnings: string[];
};

export type TracePanelActiveFilter = {
  field: RecommendedActionFilterField;
};

export type RetrievalTracePanelProps = {
  activeFilters: TracePanelActiveFilter[];
  filterFieldLabel: (field: RecommendedActionFilterField) => string;
  formatCount: (count: number, singular: string) => string;
  formatFilterValue: (field: RecommendedActionFilterField, value: string) => string;
  getActionFilter: (action: RetrievalRecommendedAction) => RecommendedActionFilter | null;
  getActionSourceLabel: (action: RetrievalRecommendedAction) => string | null;
  getCoverageSuggestedAction: (item: RetrievalCoverageItem) => string;
  getCoverageSuggestedFilter: (
    item: RetrievalCoverageItem,
  ) => CoverageDiagnosticsFilterAction | null;
  isSearchPending: boolean;
  isSuggestionSupported: (field: string) => boolean;
  onApplyCoverageFilter: (field: CoverageDiagnosticsFilterField, value: string) => void;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
  view: RetrievalTracePanelView | null;
};
