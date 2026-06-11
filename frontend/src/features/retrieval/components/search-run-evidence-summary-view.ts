import type { ComponentProps } from "react";

import type { Badge } from "../../../components/ui/badge";
import { formatCount } from "../model/retrieval-format";

type SearchRunEvidenceSummaryBadgeVariant = ComponentProps<typeof Badge>["variant"];

export type SearchRunEvidenceSummaryBadgeView = {
  label: string;
  variant: SearchRunEvidenceSummaryBadgeVariant;
};

export function coverageGapSummaryBadgeView(
  coverageGapCount: number,
): SearchRunEvidenceSummaryBadgeView {
  return {
    label: formatCount(coverageGapCount, "coverage gap"),
    variant: coverageGapCount ? "warning" : "muted",
  };
}

export function groundedConceptSummaryBadgeView(
  groundedConceptCount: number,
): SearchRunEvidenceSummaryBadgeView {
  return {
    label: formatCount(groundedConceptCount, "grounded concept"),
    variant: groundedConceptCount ? "success" : "warning",
  };
}

export function searchAspectSummaryBadgeView(
  searchAspectCount: number,
): SearchRunEvidenceSummaryBadgeView {
  return {
    label: formatCount(searchAspectCount, "search aspect"),
    variant: searchAspectCount ? "success" : "muted",
  };
}
