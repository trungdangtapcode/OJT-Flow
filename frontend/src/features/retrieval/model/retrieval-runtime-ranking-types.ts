export type RetrievalRankingStack = {
  embedding: {
    dimensions: number | null;
    model: string;
    provider: string;
  };
  framework: {
    bm25Enabled: boolean | null;
    bm25Weight: number | null;
    candidateTopK: number | null;
    filteredNodeCount: number | null;
    metadataFilterCount: number | null;
    name: string;
    nodeCount: number | null;
    vectorWeight: number | null;
  };
  reranker: {
    device: string | null;
    enabled: boolean;
    model: string;
    provider: string;
  };
};

export type RetrievalFusionDiagnosticsView = {
  interpretation: string;
  label: string;
  tone: "success" | "warning" | "info";
};
