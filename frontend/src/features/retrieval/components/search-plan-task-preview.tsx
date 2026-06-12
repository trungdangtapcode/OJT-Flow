import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { RetrievalSearchTask } from "../../../types";
import { formatCount } from "../model/retrieval-format";
import { SearchPlanTaskGroup } from "./search-plan-task-group";
import { SectionHelpText } from "./section-help-text";

export type SearchPlanTaskCopyFeedback = {
  copiedKey: string | null;
  markCopied: (key: string) => void;
};

export type SearchPlanTaskPreviewCallbacks = {
  copyTextToClipboard: (text: string) => Promise<void>;
  isSearchPending: boolean;
  onRunTask: (task: RetrievalSearchTask) => void;
  useCopyFeedback: () => SearchPlanTaskCopyFeedback;
};

export function SearchPlanTaskPreview({
  copyTextToClipboard,
  isSearchPending,
  onRunTask,
  tasks,
  useCopyFeedback,
}: SearchPlanTaskPreviewCallbacks & {
  tasks: RetrievalSearchTask[];
}) {
  if (!tasks.length) {
    return (
      <div className="rounded-md border border-border bg-card p-3">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Execution tasks
        </div>
        <SectionHelpText>
          No executable task plan was returned. Run full search or refine the query to generate task-level routing.
        </SectionHelpText>
      </div>
    );
  }
  const localTasks = tasks.filter((task) => task.target === "local_corpus");
  const externalTasks = tasks.filter((task) => task.target === "external_medical_index");

  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
          Execution tasks
          <HelpTooltip label="Execution task help">
            Local corpus tasks run OJTFlow retrieval. Medical-index tasks open or copy external follow-up searches for manual review.
          </HelpTooltip>
        </span>
        <Badge variant="success">{formatCount(tasks.length, "task")}</Badge>
      </div>
      <SearchPlanTaskGroup
        badgeVariant="success"
        copyTextToClipboard={copyTextToClipboard}
        description="These tasks run against governed OJTFlow evidence and can refresh the ranked package."
        emptyText="No local OJTFlow search task was generated for this plan."
        isSearchPending={isSearchPending}
        label="Local OJTFlow searches"
        onRunTask={onRunTask}
        tasks={localTasks}
        useCopyFeedback={useCopyFeedback}
      />
      <SearchPlanTaskGroup
        badgeVariant="warning"
        copyTextToClipboard={copyTextToClipboard}
        description="These follow-ups open or copy external medical searches for manual review."
        emptyText="No external medical-index follow-up was generated for this plan."
        isSearchPending={isSearchPending}
        label="External follow-ups"
        onRunTask={onRunTask}
        tasks={externalTasks}
        useCopyFeedback={useCopyFeedback}
      />
    </div>
  );
}
