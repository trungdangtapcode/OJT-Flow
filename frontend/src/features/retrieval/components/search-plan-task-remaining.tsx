import { ChevronDown } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import type { RetrievalSearchTask } from "../../../types";
import { formatCount } from "../model/retrieval-format";
import type { SearchPlanTaskPreviewCallbacks } from "./search-plan-task-preview";
import { SearchPlanTaskRow } from "./search-plan-task-row";

export function SearchPlanTaskRemaining({
  copyTextToClipboard,
  isSearchPending,
  label,
  onRunTask,
  remainingTasks,
  useCopyFeedback,
}: SearchPlanTaskPreviewCallbacks & {
  label: string;
  remainingTasks: RetrievalSearchTask[];
}) {
  if (!remainingTasks.length) return null;

  return (
    <details className="group rounded-md border border-border bg-background">
      <summary
        aria-label={`Show remaining ${label.toLowerCase()}`}
        className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-2 px-2 py-1.5 text-xs font-black uppercase text-muted-foreground"
      >
        <span className="flex min-w-0 items-center gap-1.5">
          <ChevronDown className="h-4 w-4 shrink-0 transition-transform group-open:rotate-180" />
          <span className="break-words">Show remaining {label.toLowerCase()}</span>
        </span>
        <Badge variant="muted">{formatCount(remainingTasks.length, "task")}</Badge>
      </summary>
      <div className="grid gap-2 border-t border-border p-2">
        {remainingTasks.map((task) => (
          <SearchPlanTaskRow
            copyTextToClipboard={copyTextToClipboard}
            isSearchPending={isSearchPending}
            key={task.task_id}
            onRunTask={onRunTask}
            task={task}
            useCopyFeedback={useCopyFeedback}
          />
        ))}
      </div>
    </details>
  );
}
