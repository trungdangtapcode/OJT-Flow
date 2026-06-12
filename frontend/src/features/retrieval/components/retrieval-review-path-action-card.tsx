import { ListFilter } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import type { RetrievalReviewPath } from "../model/retrieval-review-path";
import { formatReviewPathCount } from "./retrieval-review-path-format";

export function RetrievalReviewPathActionCard({
  reviewPath,
}: {
  reviewPath: RetrievalReviewPath;
}) {
  return (
    <div className="grid content-start gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex items-center gap-2 text-sm font-black">
        <ListFilter className="h-4 w-4 text-primary" />
        Next operator action
      </div>
      <div className="break-words text-sm font-black">
        {reviewPath.primaryAction?.title ?? reviewPath.guidance.actionTitle}
      </div>
      <p className="break-words text-sm leading-6 text-muted-foreground">
        {reviewPath.primaryAction?.description ?? reviewPath.guidance.actionDetail}
      </p>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {reviewPath.topSourceId ? (
          <Badge className="max-w-full whitespace-normal break-words" variant="muted">
            top source: {reviewPath.topSourceId}
          </Badge>
        ) : null}
        <Badge variant="muted">
          {formatReviewPathCount(reviewPath.hitCount, "hit")}
        </Badge>
        <Badge variant="muted">
          {formatReviewPathCount(reviewPath.candidateCount, "candidate")}
        </Badge>
      </div>
    </div>
  );
}
