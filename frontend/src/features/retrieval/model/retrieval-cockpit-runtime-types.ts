export type RetrievalCockpitDiversitySelection = {
  evidenceId: string;
  originalRank: number;
  reason: string;
  redundancyScore: number;
  relevanceScore: number;
  selectedRank: number;
  selectionScore: number;
  sourceId: string;
};

export type RetrievalCockpitDiversityStack = {
  candidateSourceCount: number;
  duplicateSelectedSourceCount: number;
  enabled: boolean;
  lambda: number | null;
  selectedHits: RetrievalCockpitDiversitySelection[];
  selectedSourceCount: number;
  selectionMode: string;
};

export type RetrievalCockpitRankingStack = {
  embedding: {
    model: string;
    provider: string;
  };
  framework: {
    bm25Enabled: boolean | null;
  };
  reranker: {
    enabled: boolean;
  };
};

export type RetrievalCockpitQueryAnalysisStack = {
  detectedConcepts: string[];
  diagnostics: RetrievalCockpitQueryDiagnostic[];
  expandedTerms: string[];
  queryAspects: {
    aspectId: string;
    label: string;
    priority: number;
    question: string;
  }[];
  queryProfile: {
    complexity: string;
    label: string;
    retrievalMode: string;
    route: string;
  } | null;
  standards: string[];
  strategy: string;
  variantCount: number;
};

export type RetrievalCockpitQueryDiagnostic = {
  code: string;
  message: string;
  severity: string;
  suggestedAction: string;
};
