export type DiversitySelectionStack = {
  evidenceId: string;
  originalRank: number;
  reason: string;
  redundancyScore: number;
  relevanceScore: number;
  selectedRank: number;
  selectionScore: number;
  sourceId: string;
};

export type DiversityStack = {
  candidateSourceCount: number;
  duplicateSelectedSourceCount: number;
  enabled: boolean;
  lambda: number | null;
  selectedHits: DiversitySelectionStack[];
  selectedSourceCount: number;
  selectionMode: string;
};

export type RetrievalSourceDiversityComparisonView = {
  active: DiversityStack;
  activeSelectedSourceIds: string[];
  addedSourceIds: string[];
  baseline: DiversityStack;
  baselineSelectedSourceIds: string[];
  candidateSourceDelta: number;
  duplicateSelectedSourceDelta: number;
  lambdaChanged: boolean;
  removedSourceIds: string[];
  retainedSourceIds: string[];
  selectedSourceDelta: number;
  selectionModeChanged: boolean;
  sourceOverlapRatio: number;
};
