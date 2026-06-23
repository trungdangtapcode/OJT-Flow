import type { RetrievalSearchTask } from "../../../types";
import { SearchPlanTaskActions } from "./search-plan-task-actions";
import { SearchPlanTaskActionSummary } from "./search-plan-task-action-summary";
import { SearchPlanTaskBadges } from "./search-plan-task-badges";
import { SearchPlanTaskFilterChips } from "./search-plan-task-filter-chips";
import type { SearchPlanTaskPreviewCallbacks } from "./search-plan-task-preview";

export function SearchPlanTaskRow({
  copyTextToClipboard,
  isSearchPending,
  onRunTask,
  task,
  useCopyFeedback,
}: SearchPlanTaskPreviewCallbacks & {
  task: RetrievalSearchTask;
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const copyKey = `task-query:${task.task_id}`;
  const copied = copiedKey === copyKey;
  const copyQuery = async () => {
    await copyTextToClipboard(task.query);
    markCopied(copyKey);
  };
  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-1.5 rounded-lg border border-border/60 bg-muted/20 p-2 text-xs">
      <SearchPlanTaskBadges task={task} />
      <div className="break-words text-muted-foreground">{task.rationale}</div>
      <SearchPlanTaskActionSummary task={task} />
      <code className="block max-w-full overflow-hidden break-words rounded bg-background px-2 py-1 font-mono">
        {task.query}
      </code>
      <SearchPlanTaskFilterChips task={task} />
      <SearchPlanTaskActions
        copied={copied}
        isSearchPending={isSearchPending}
        onCopyQuery={() => void copyQuery()}
        onRunTask={onRunTask}
        task={task}
      />
    </div>
  );
}
