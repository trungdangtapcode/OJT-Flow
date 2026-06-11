import type {
  RetrievalQualitySummary,
  RetrievalSearchPayload,
} from "../../../types";
import type { DiversityStack } from "./retrieval-source-diversity-types";

export type RetrievalSearchRun = {
  packageData: import("../../../types").RetrievalPackage;
  payload: RetrievalSearchPayload;
  runId: string;
  signature: string;
  submittedAt: string;
  summary: RetrievalRunSummary;
};

export type RetrievalRunSummary = {
  candidateCount: number;
  conceptGrounding: ConceptGroundingSummary[];
  correctiveActionSummary: CorrectiveActionSummary;
  coverage: RetrievalCoverageSummary[];
  diversity: DiversityStack;
  hitCount: number;
  qualitySummary: RetrievalQualitySummary | null;
  qualityWarningCount: number;
  queryAspects: QueryAspectSummary[];
  queryProfile: QueryProfileSummary | null;
  rulePackCount: number;
  rulePackFingerprint: string;
  serverSignature: string | null;
  remediationSummary: string | null;
  topSourceId: string | null;
  warningCount: number;
};

export type CorrectiveActionSummary = {
  count: number;
  highestPriority: number | null;
  highestSeverity: string | null;
  topActionTitle: string | null;
  applyFilterCount: number;
  broadenQueryCount: number;
  actionTypeCounts: Record<string, number>;
};

export type RetrievalCoverageSummary = {
  field: string;
  label: string;
  selectedCount: number;
  status: string;
  suggestedFilter: Record<string, string>;
  value: string;
};

export type QueryAspectSummary = {
  aspectId: string;
  label: string;
  priority: number;
  question: string;
  ruleId: string;
};

export type ConceptGroundingSummary = {
  code: string | null;
  conceptId: string;
  displayName: string;
  evidenceCount: number;
  standardSystem: string;
};

export type QueryProfileSummary = {
  complexity: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
};

export type ConceptMatchSignal = {
  code: string | null;
  conceptId: string;
  displayName: string;
  standardSystem: string;
};
