import type {
  RetrievalRecommendedAction,
  RetrievalStandardSearchPlan,
  RetrievalStrategyRecommendation,
} from "../../../types";
import type {
  RetrievalCockpitDiversityStack,
  RetrievalCockpitQueryAnalysisStack,
} from "./retrieval-cockpit-runtime";
import type {
  RetrievalCockpitFilterAction,
  RetrievalCockpitQueryHealthItem,
  RetrievalCockpitReadinessChecklistItem,
  RetrievalSearchCockpitActiveFilter,
} from "./retrieval-cockpit-signals";

export type { RetrievalSearchCockpitActiveFilter };

export type RetrievalSearchCockpitView = {
  activeFilters: RetrievalSearchCockpitActiveFilter[];
  bm25Enabled: boolean | null;
  candidateCount: number;
  conceptGroundingCount: number;
  correctiveActionCount: number | null;
  coveredRequiredBucketCount: number;
  coverageGapCount: number;
  detectedConcepts: string[];
  diversity: RetrievalCockpitDiversityStack;
  expandedTerms: string[];
  fusionDiagnostics: {
    interpretation: string;
    label: string;
    tone: "success" | "warning" | "info";
  };
  hitCount: number;
  hybridStackValue: string;
  qualitySummary: {
    score: number;
    status: string;
    topAction: string;
    variant: "success" | "warning" | "destructive" | "muted";
  } | null;
  queryAspectCount: number;
  queryAspects: RetrievalCockpitQueryAnalysisStack["queryAspects"];
  queryHealth: RetrievalCockpitQueryHealthItem[];
  queryProfile: RetrievalCockpitQueryAnalysisStack["queryProfile"];
  rankingSupporting: string;
  readinessChecklist: RetrievalCockpitReadinessChecklistItem[];
  rerankerEnabled: boolean;
  requiredBucketCount: number;
  routeLabel: string;
  standardSearchPlan: RetrievalStandardSearchPlan | null;
  standards: string[];
  strategy: string;
  strategyRecommendations: RetrievalStrategyRecommendation[];
  topAction: RetrievalRecommendedAction | null;
  topBroadeningAction: boolean;
  topFilterAction: RetrievalCockpitFilterAction | null;
  variantCount: number;
};
