import { Badge } from "../../../components/ui/badge";
import type { RetrievalSearchTask } from "../../../types";
import {
  searchPlanTaskRequirementBadgeView,
  searchPlanTaskTargetBadgeView,
} from "./search-plan-task-badge-view";

export function SearchPlanTaskBadges({ task }: { task: RetrievalSearchTask }) {
  const targetBadge = searchPlanTaskTargetBadgeView(task);
  const requirementBadge = searchPlanTaskRequirementBadgeView(task);

  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5">
      <Badge variant="muted">P{task.priority}</Badge>
      <Badge variant={targetBadge.variant}>{targetBadge.label}</Badge>
      <Badge variant={requirementBadge.variant}>{requirementBadge.label}</Badge>
      <span className="break-words font-black">{task.label}</span>
    </div>
  );
}
