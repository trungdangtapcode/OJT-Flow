import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalQualitySummary } from "../../../types";
import type {
  SearchPlanPreviewAnalysis,
  SearchPlanPreviewProfile,
} from "../model/search-plan-preview-types";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export function SearchPlanRouteDecisionPanel({
  analysis,
  formatCount,
  planSummary,
  profile,
  qualitySummary,
  qualitySummaryBadgeVariant,
}: {
  analysis: SearchPlanPreviewAnalysis;
  formatCount: (count: number, singular: string) => string;
  planSummary: string | null;
  profile: SearchPlanPreviewProfile | null;
  qualitySummary: RetrievalQualitySummary | null;
  qualitySummaryBadgeVariant: (summary: RetrievalQualitySummary) => BadgeVariant;
}) {
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Route decision
        </span>
        {qualitySummary ? (
          <Badge variant={qualitySummaryBadgeVariant(qualitySummary)}>
            {humanize(qualitySummary.status)} {qualitySummary.score}/100
          </Badge>
        ) : (
          <Badge variant="muted">plan only</Badge>
        )}
      </div>
      <div className="break-words text-base font-black">
        {profile?.label ?? humanize(analysis.strategy)}
      </div>
      <div className="break-words text-sm leading-6 text-muted-foreground">
        {planSummary ??
          profile?.description ??
          "The backend used the default retrieval route because no stronger query profile matched."}
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant="muted">{humanize(analysis.strategy)}</Badge>
        {profile ? (
          <>
            <Badge variant="muted">{humanize(profile.route)}</Badge>
            <Badge variant="muted">{humanize(profile.retrievalMode)}</Badge>
            <Badge variant={profile.complexity === "high" ? "warning" : "success"}>
              {humanize(profile.complexity)}
            </Badge>
          </>
        ) : null}
        <Badge variant={analysis.standards.length ? "success" : "muted"}>
          {formatCount(analysis.standards.length, "standard")}
        </Badge>
        <Badge variant={analysis.queryAspects.length ? "success" : "muted"}>
          {formatCount(analysis.queryAspects.length, "aspect")}
        </Badge>
      </div>
    </div>
  );
}
