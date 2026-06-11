import type {
  RetrievalPlanRiskSignal,
  RetrievalPlanTaskSummary,
  RetrievalQualitySummary,
  RetrievalQueryVariant,
  RetrievalSearchTask,
} from "../../../types";
import type {
  FilterSuggestionStack,
  QueryAspectStack,
  SearchHintStack,
} from "../components/search-plan-detail-panels";
import type { SearchPlanCoverageSummaryView } from "./search-plan-summary-types";

export type SearchPlanPreviewProfile = {
  complexity: string;
  description: string;
  label: string;
  retrievalMode: string;
  route: string;
};

export type SearchPlanPreviewAnalysis = {
  filterSuggestions: FilterSuggestionStack[];
  queryAspects: QueryAspectStack[];
  searchHints: SearchHintStack[];
  standards: string[];
  strategy: string;
  retrievalTasks: RetrievalSearchTask[];
};

export type SearchPlanPreviewView = {
  analysis: SearchPlanPreviewAnalysis;
  coverageSummary: SearchPlanCoverageSummaryView;
  planSummary: string | null;
  profile: SearchPlanPreviewProfile | null;
  qualitySummary: RetrievalQualitySummary | null;
  riskSignals: RetrievalPlanRiskSignal[];
  taskSummary: RetrievalPlanTaskSummary;
  variants: RetrievalQueryVariant[];
};
