import type { RetrievalSearchCockpitView } from "../model/retrieval-cockpit-view-model";
import { cockpitCountLabel } from "./search-cockpit-format";

type CockpitStatusBadgeVariant = "success" | "warning";

export type CockpitStatusBadgeView = {
  label: string;
  variant: CockpitStatusBadgeVariant;
};

export function requiredBucketBadgeView(
  view: RetrievalSearchCockpitView,
): CockpitStatusBadgeView {
  if (!view.requiredBucketCount) {
    return {
      label: "no required buckets",
      variant: "success",
    };
  }

  return {
    label: `${view.coveredRequiredBucketCount}/${view.requiredBucketCount} required buckets`,
    variant:
      view.coveredRequiredBucketCount < view.requiredBucketCount ? "warning" : "success",
  };
}

export function coverageGapBadgeView(
  view: RetrievalSearchCockpitView,
): CockpitStatusBadgeView {
  if (!view.coverageGapCount) {
    return {
      label: "coverage ok",
      variant: "success",
    };
  }

  return {
    label: cockpitCountLabel(view.coverageGapCount, "coverage gap"),
    variant: "warning",
  };
}
