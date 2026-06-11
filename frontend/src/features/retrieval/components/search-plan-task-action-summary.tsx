import { Badge } from "../../../components/ui/badge";
import type { RetrievalSearchTask } from "../../../types";
import {
  retrievalTaskActionDescription,
  retrievalTaskActionLabel,
} from "../model/search-plan-tasks";

export function SearchPlanTaskActionSummary({ task }: { task: RetrievalSearchTask }) {
  return (
    <div className="grid gap-1 rounded-md border border-border bg-background px-2 py-1.5">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-black uppercase text-muted-foreground">What happens</span>
        <Badge variant={task.action_type === "run_local_search" ? "success" : "muted"}>
          {retrievalTaskActionLabel(task)}
        </Badge>
      </div>
      <div className="break-words text-muted-foreground">
        {retrievalTaskActionDescription(task)}
      </div>
    </div>
  );
}
