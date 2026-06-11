import type {
  RetrievalPlanRiskSignal,
  RetrievalPlanTaskSummary,
  RetrievalQueryVariant,
  RetrievalSearchTask,
} from "../../../types";
import type {
  FilterSuggestionStack,
  QueryAspectStack,
  SearchHintStack,
} from "../components/search-plan-detail-panels";
import type { SearchPlanCoverageSummaryView } from "./search-plan-summary-types";

export type QueryAnalysisStack = {
  conceptCandidates: ConceptCandidateStack[];
  detectedConcepts: string[];
  diagnostics: QueryDiagnosticStack[];
  expandedTerms: string[];
  filterSuggestions: FilterSuggestionStack[];
  queryAspects: QueryAspectStack[];
  queryProfile: QueryProfileStack | null;
  queryVariantTexts: string[];
  queryVariants: RetrievalQueryVariant[];
  planCoverageSummary: SearchPlanCoverageStack | null;
  planRiskSignals: RetrievalPlanRiskSignal[];
  planTaskSummary: RetrievalPlanTaskSummary | null;
  retrievalTasks: RetrievalSearchTask[];
  ruleIds: string[];
  searchHints: SearchHintStack[];
  standards: string[];
  strategy: string;
  variantCount: number;
};

export type SearchPlanCoverageStack = SearchPlanCoverageSummaryView;

export type QueryProfileStack = {
  complexity: string;
  description: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
  ruleIds: string[];
  suggestedFilters: Record<string, string>;
};

export type ConceptCandidateStack = {
  clinicalDomain: string | null;
  code: string | null;
  conceptId: string;
  confidence: number;
  displayName: string;
  matchedAliases: string[];
  standardSystem: string;
};

export type QueryDiagnosticStack = {
  code: string;
  metadata: Record<string, unknown>;
  message: string;
  severity: string;
  suggestedAction: string;
};
