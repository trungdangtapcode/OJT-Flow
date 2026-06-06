import {
  AlertTriangle,
  CheckCircle2,
  Database,
  FileSearch,
  ListFilter,
  ShieldCheck,
} from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { cn } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";
import {
  buildRetrievalReviewPath,
  type RetrievalReviewCheck,
  type RetrievalReviewCheckStatus,
} from "../model/retrieval-review-path";

const checkIcons: Record<RetrievalReviewCheck["code"], typeof CheckCircle2> = {
  readiness: ShieldCheck,
  required_support: Database,
  top_hit_support: FileSearch,
  warnings: AlertTriangle,
};

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
        <div className="grid gap-2 sm:grid-cols-2">
          {reviewPath.checks.map((item) => (
            <ReviewPathCheckCard item={item} key={item.code} />
          ))}
        </div>
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
              {formatCount(reviewPath.hitCount, "hit")}
            </Badge>
            <Badge variant="muted">
              {formatCount(reviewPath.candidateCount, "candidate")}
            </Badge>
          </div>
        </div>
      </div>
    </section>
  );
}

function ReviewPathCheckCard({ item }: { item: RetrievalReviewCheck }) {
  const Icon = checkIcons[item.code];
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 items-start gap-2">
        <Icon
          className={cn(
            "mt-0.5 h-4 w-4 shrink-0",
            item.status === "ok"
              ? "text-emerald-600"
              : item.status === "blocked"
                ? "text-destructive"
                : "text-amber-600",
          )}
        />
        <div className="min-w-0">
          <div className="break-words text-sm font-black">{item.label}</div>
          <p className="mt-1 break-words text-sm leading-6 text-muted-foreground">
            {item.detail}
          </p>
        </div>
      </div>
    </div>
  );
}

function reviewStatusBadgeVariant(
  status: RetrievalReviewCheckStatus,
): "success" | "warning" | "destructive" {
  if (status === "ok") return "success";
  if (status === "blocked") return "destructive";
  return "warning";
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
