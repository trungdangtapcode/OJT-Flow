export type RetrievalRuntimeStatusView = {
  graphEdgeCount: number | null;
  graphNodeCount: number | null;
  graphTripleCount: number | null;
  integrityStatus: string;
  rerankerEnabled: boolean;
  retrievalMode: string;
  sourceCoverageLabel: string;
  sourceDiversityEnabled: boolean;
};
