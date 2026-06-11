import type {
  RetrievalEvidenceBucket,
  RetrievalQualitySummary,
} from "../../../types";

export type EvidenceReadinessFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type EvidenceReadinessFilterAction = {
  field: EvidenceReadinessFilterField;
  value: string;
};

export type EvidenceReadinessInterpretation = {
  badge: string;
  description: string;
  title: string;
  variant: "success" | "warning" | "destructive" | "muted";
};

export type EvidenceReadinessView = {
  bucketSignalAction: string | null;
  interpretation: EvidenceReadinessInterpretation;
  missingBuckets: RetrievalEvidenceBucket[];
  qualitySummary: RetrievalQualitySummary | null;
  ready: boolean;
};
