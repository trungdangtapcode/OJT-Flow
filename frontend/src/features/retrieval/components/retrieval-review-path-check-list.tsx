import type { RetrievalReviewCheck } from "../model/retrieval-review-path";
import { RetrievalReviewPathCheckCard } from "./retrieval-review-path-check-card";

export function RetrievalReviewPathCheckList({
  checks,
}: {
  checks: RetrievalReviewCheck[];
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {checks.map((item) => (
        <RetrievalReviewPathCheckCard item={item} key={item.code} />
      ))}
    </div>
  );
}
