import type { RetrievalReviewCheckStatus } from "../model/retrieval-review-path";

export function reviewStatusBadgeVariant(
  status: RetrievalReviewCheckStatus,
): "success" | "warning" | "destructive" {
  if (status === "ok") return "success";
  if (status === "blocked") return "destructive";
  return "warning";
}

export function formatReviewPathCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
