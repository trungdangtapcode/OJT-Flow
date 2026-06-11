import type { ComponentProps } from "react";

import type { Badge } from "../../../components/ui/badge";
import { formatCount } from "../model/retrieval-format";

export type SearchPlanTaskGroupBadgeVariant = ComponentProps<typeof Badge>["variant"];

export type SearchPlanTaskGroupCountView = {
  label: string;
  variant: SearchPlanTaskGroupBadgeVariant;
};

export function requiredTaskCountView(requiredTaskCount: number): SearchPlanTaskGroupCountView {
  return {
    label: formatCount(requiredTaskCount, "required task"),
    variant: requiredTaskCount ? "warning" : "muted",
  };
}

export function optionalTaskCountView(optionalTaskCount: number): SearchPlanTaskGroupCountView {
  return {
    label: formatCount(optionalTaskCount, "optional task"),
    variant: optionalTaskCount ? "muted" : "success",
  };
}

export function taskGroupCountGuidance(requiredTaskCount: number): string {
  if (requiredTaskCount) {
    return "Prioritize required tasks before optional follow-ups.";
  }

  return "No required task in this group.";
}
