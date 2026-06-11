import type { LucideIcon } from "lucide-react";

import type { RetrievalQualitySummary } from "../../../types";

export type RankedEvidenceTriageView = {
  candidateCount: number;
  hitCount: number;
  isStale: boolean;
  judgedCount: number;
  qualitySummary: RetrievalQualitySummary | null;
  requiredBucketCount: number;
  coveredRequiredBucketCount: number;
};

export type TriageTone = "success" | "warning" | "muted" | "destructive";

export type RankedEvidenceTriageGuidance = {
  detail: string;
  headline: string;
  icon: LucideIcon;
  state: string;
  variant: TriageTone;
};
