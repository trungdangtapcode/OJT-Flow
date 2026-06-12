import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalSearchCockpitView } from "../model/retrieval-cockpit-view-model";
import {
  coverageGapBadgeView,
  requiredBucketBadgeView,
} from "./search-cockpit-status-badge-view";

export function SearchCockpitStatusBadges({
  view,
}: {
  view: RetrievalSearchCockpitView;
}) {
  const requiredBucketBadge = requiredBucketBadgeView(view);
  const coverageGapBadge = coverageGapBadgeView(view);

  return (
    <>
      {view.qualitySummary ? (
        <Badge variant={view.qualitySummary.variant}>
          {humanize(view.qualitySummary.status)} {view.qualitySummary.score}/100
        </Badge>
      ) : null}
      <Badge variant={requiredBucketBadge.variant}>{requiredBucketBadge.label}</Badge>
      <Badge variant={coverageGapBadge.variant}>{coverageGapBadge.label}</Badge>
    </>
  );
}
