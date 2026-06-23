import { Badge } from "../../../components/ui/badge";
import type { RetrievalSearchTask } from "../../../types";
import { formatCount } from "../model/retrieval-format";
import { searchPlanTaskGroupView } from "../model/search-plan-task-group-view";
import type { SearchPlanTaskPreviewCallbacks } from "./search-plan-task-preview";
import { SearchPlanTaskGroupToolbar } from "./search-plan-task-group-toolbar";
import type { SearchPlanTaskGroupBadgeVariant } from "./search-plan-task-group-count-view";
import { SearchPlanTaskRemaining } from "./search-plan-task-remaining";
import { SearchPlanTaskRow } from "./search-plan-task-row";
import { SectionHelpText } from "./section-help-text";

export function SearchPlanTaskGroup({
  badgeVariant,
  copyTextToClipboard,
  description,
  emptyText,
  isSearchPending,
  label,
  onRunTask,
  tasks,
  useCopyFeedback,
}: SearchPlanTaskPreviewCallbacks & {
  badgeVariant: SearchPlanTaskGroupBadgeVariant;
  description: string;
  emptyText: string;
  label: string;
  tasks: RetrievalSearchTask[];
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const {
    optionalTaskCount,
    orderedTasks,
    remainingTasks,
    requiredTaskCount,
    visibleTasks,
  } = searchPlanTaskGroupView(tasks);
  const copyKey = `task-group:${label}`;
  const copied = copiedKey === copyKey;
  return (
    <div className="grid min-w-0 gap-2 rounded-lg border border-border/60 bg-muted/20 p-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="break-words text-xs font-black uppercase text-muted-foreground">
            {label}
          </div>
          <div className="break-words text-xs text-muted-foreground">{description}</div>
        </div>
        <Badge variant={tasks.length ? badgeVariant : "muted"}>
          {formatCount(tasks.length, "task")}
        </Badge>
      </div>
      {tasks.length ? (
        <div className="grid gap-2">
          <SearchPlanTaskGroupToolbar
            copied={copied}
            copyKey={copyKey}
            copyTextToClipboard={copyTextToClipboard}
            markCopied={markCopied}
            optionalTaskCount={optionalTaskCount}
            orderedTasks={orderedTasks}
            requiredTaskCount={requiredTaskCount}
          />
          {visibleTasks.map((task) => (
            <SearchPlanTaskRow
              copyTextToClipboard={copyTextToClipboard}
              isSearchPending={isSearchPending}
              key={task.task_id}
              onRunTask={onRunTask}
              task={task}
              useCopyFeedback={useCopyFeedback}
            />
          ))}
          <SearchPlanTaskRemaining
            copyTextToClipboard={copyTextToClipboard}
            isSearchPending={isSearchPending}
            label={label}
            onRunTask={onRunTask}
            remainingTasks={remainingTasks}
            useCopyFeedback={useCopyFeedback}
          />
        </div>
      ) : (
        <SectionHelpText>{emptyText}</SectionHelpText>
      )}
    </div>
  );
}
