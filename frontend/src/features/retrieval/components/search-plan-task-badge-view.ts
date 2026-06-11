import type { ComponentProps } from "react";

import type { Badge } from "../../../components/ui/badge";
import type { RetrievalSearchTask } from "../../../types";

type SearchPlanTaskBadgeVariant = ComponentProps<typeof Badge>["variant"];

export type SearchPlanTaskBadgeView = {
  label: string;
  variant: SearchPlanTaskBadgeVariant;
};

export function searchPlanTaskTargetBadgeView(
  task: RetrievalSearchTask,
): SearchPlanTaskBadgeView {
  if (task.target === "local_corpus") {
    return {
      label: "local corpus",
      variant: "success",
    };
  }

  return {
    label: "medical index",
    variant: "warning",
  };
}

export function searchPlanTaskRequirementBadgeView(
  task: RetrievalSearchTask,
): SearchPlanTaskBadgeView {
  if (task.required) {
    return {
      label: "required",
      variant: "warning",
    };
  }

  return {
    label: "optional",
    variant: "muted",
  };
}
