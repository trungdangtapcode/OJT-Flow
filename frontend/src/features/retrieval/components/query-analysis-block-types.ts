import type { ConceptCandidateListItem } from "./concept-candidate-list";
import type { QueryAspectPlanItemView } from "./query-aspect-plan";
import type { QueryDiagnosticListItem } from "./query-diagnostic-list";
import type {
  QueryProfileCardView,
  QueryProfileFilterEntryView,
} from "./query-profile-card";
import type {
  FilterSuggestionStack,
  SearchHintStack,
} from "./search-plan-detail-panels";

export type QueryAnalysisBlockView = {
  conceptCandidates: ConceptCandidateListItem[];
  detectedConcepts: string[];
  diagnostics: QueryDiagnosticListItem[];
  expandedTerms: string[];
  filterSuggestions: FilterSuggestionStack[];
  queryAspects: QueryAspectPlanItemView[];
  queryProfile: QueryProfileCardView | null;
  queryProfileFilterEntries: QueryProfileFilterEntryView[];
  queryProfileRouteHelpText: string;
  ruleIds: string[];
  searchHints: SearchHintStack[];
  standards: string[];
  strategy: string;
  variantCount: number;
};
