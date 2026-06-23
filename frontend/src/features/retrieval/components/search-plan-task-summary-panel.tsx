import { Badge } from "../../../components/ui/badge";
import type { RetrievalPlanTaskSummary, RetrievalSearchTask } from "../../../types";
import {
  externalMedicalIndexTasks,
  firstRunnableLocalTask,
} from "../model/search-plan-task-summary-actions";
import { MetricMiniCard } from "./search-plan-metric-mini-card";
import { SearchPlanRunOrder } from "./search-plan-run-order";
import { SearchPlanTaskSummaryActions } from "./search-plan-task-summary-actions";
import { SectionHelpText } from "./section-help-text";

export function SearchPlanTaskSummaryPanel({
  copyTextToClipboard,
  isSearchPending,
  onRunTask,
  summary,
  tasks,
  useCopyFeedback,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  isSearchPending: boolean;
  onRunTask: (task: RetrievalSearchTask) => void;
  summary: RetrievalPlanTaskSummary;
  tasks: RetrievalSearchTask[];
  useCopyFeedback: () => {
    copiedKey: string | null;
    markCopied: (key: string) => void;
  };
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const firstRequiredTask = firstRunnableLocalTask(tasks);
  const externalTasks = externalMedicalIndexTasks(tasks);
  return (
    <div className="grid min-w-0 gap-2 rounded-lg border border-border/60 bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Execution summary
        </span>
        <Badge variant={summary.required_runnable_local_count ? "success" : "warning"}>
          {summary.required_runnable_local_count
            ? "ready to run"
            : summary.manual_followup_count
              ? "manual follow-up"
              : "needs query detail"}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        <MetricMiniCard
          label="Runnable local"
          supporting="Can execute inside OJTFlow"
          value={summary.runnable_local_count}
        />
        <MetricMiniCard
          label="Required local"
          supporting="Recommended first actions"
          value={summary.required_runnable_local_count}
        />
        <MetricMiniCard
          label="Manual follow-ups"
          supporting="External medical indexes"
          value={summary.manual_followup_count}
        />
      </div>
      <div className="rounded-lg border border-border/60 bg-muted/20 px-2 py-1.5 text-xs">
        <div className="font-black uppercase text-muted-foreground">Primary action</div>
        <div className="mt-1 break-words font-semibold">{summary.primary_action}</div>
      </div>
      <SearchPlanRunOrder />
      <SearchPlanTaskSummaryActions
        copiedKey={copiedKey}
        copyTextToClipboard={copyTextToClipboard}
        externalTasks={externalTasks}
        firstRequiredTask={firstRequiredTask}
        isSearchPending={isSearchPending}
        markCopied={markCopied}
        onRunTask={onRunTask}
      />
      <SectionHelpText>{summary.summary}</SectionHelpText>
    </div>
  );
}
