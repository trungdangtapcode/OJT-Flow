import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalSearchTask } from "../../../types";

export function SearchPlanTaskFilterChips({ task }: { task: RetrievalSearchTask }) {
  if (!Object.keys(task.suggested_filters).length) return null;
  return (
    <div className="flex min-w-0 flex-wrap gap-1">
      {Object.entries(task.suggested_filters).slice(0, 4).map(([field, value]) => (
        <Badge key={`${task.task_id}-${field}-${value}`} variant="muted">
          {humanize(field)}: {humanize(value)}
        </Badge>
      ))}
    </div>
  );
}
