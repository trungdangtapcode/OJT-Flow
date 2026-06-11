import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { RetrievalPackage } from "../../../types";
import { buildRetrievalReviewPath } from "../model/retrieval-review-path";
import { RetrievalReviewPathActionCard } from "./retrieval-review-path-action-card";
import { RetrievalReviewPathCheckList } from "./retrieval-review-path-check-list";
import { reviewStatusBadgeVariant } from "./retrieval-review-path-format";

export function RetrievalReviewPathPanel({
  packageData,
}: {
  packageData: RetrievalPackage;
}) {
  const reviewPath = buildRetrievalReviewPath(packageData);
  return (
    <section
      aria-label="Guided retrieval review path"
      className="grid gap-3 rounded-md border border-border bg-card p-3"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Review path
            </div>
            <Badge variant={reviewStatusBadgeVariant(reviewPath.guidance.status)}>
              {reviewPath.guidance.badge}
            </Badge>
            {reviewPath.primaryAction ? (
              <Badge variant="muted">priority {reviewPath.primaryAction.priority}</Badge>
            ) : null}
          </div>
          <div className="mt-2 max-w-4xl break-words text-base font-black leading-7">
            {reviewPath.guidance.headline}
          </div>
          <p className="mt-1 max-w-4xl text-sm leading-6 text-muted-foreground">
            {reviewPath.guidance.description}
          </p>
        </div>
        <HelpTooltip label="Review path help">
          A plain-language checklist built from backend retrieval quality, evidence buckets, warnings, recommended actions, and the top ranked hit. Use it before reading individual evidence cards.
        </HelpTooltip>
      </div>

      <div className="grid gap-2 lg:grid-cols-[minmax(0,1fr)_minmax(260px,0.7fr)]">
        <RetrievalReviewPathCheckList checks={reviewPath.checks} />
        <RetrievalReviewPathActionCard reviewPath={reviewPath} />
      </div>
    </section>
  );
}
