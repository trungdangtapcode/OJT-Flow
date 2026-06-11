import type { RetrievalRecommendedAction } from "../../../types";

export type RetrievalReviewCheckStatus = "ok" | "review" | "blocked";

export type RetrievalReviewCheck = {
  code: "readiness" | "required_support" | "top_hit_support" | "warnings";
  detail: string;
  label: string;
  status: RetrievalReviewCheckStatus;
};

export type RetrievalReviewGuidance = {
  actionDetail: string;
  actionTitle: string;
  badge: "ready" | "review" | "blocked";
  description: string;
  headline: string;
  status: RetrievalReviewCheckStatus;
};

export type RetrievalReviewPath = {
  candidateCount: number;
  checks: RetrievalReviewCheck[];
  guidance: RetrievalReviewGuidance;
  hitCount: number;
  primaryAction: RetrievalRecommendedAction | null;
  topSourceId: string | null;
};
