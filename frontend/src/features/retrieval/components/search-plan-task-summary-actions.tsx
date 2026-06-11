import { CheckCircle2, Clipboard, FileSearch } from "lucide-react";

import { Button } from "../../../components/ui/button";
import type { RetrievalSearchTask } from "../../../types";
import { retrievalTaskClipboardText } from "../model/search-plan-tasks";

export function SearchPlanTaskSummaryActions({
  copiedKey,
  copyTextToClipboard,
  externalTasks,
  firstRequiredTask,
  isSearchPending,
  markCopied,
  onRunTask,
}: {
  copiedKey: string | null;
  copyTextToClipboard: (text: string) => Promise<void>;
  externalTasks: RetrievalSearchTask[];
  firstRequiredTask: RetrievalSearchTask | null;
  isSearchPending: boolean;
  markCopied: (key: string) => void;
  onRunTask: (task: RetrievalSearchTask) => void;
}) {
  const copyExternalQueries = async () => {
    await copyTextToClipboard(
      externalTasks.map((task) => retrievalTaskClipboardText(task)).join("\n\n"),
    );
    markCopied("plan-external-followups");
  };

  return (
    <div className="flex min-w-0 flex-wrap gap-2">
      {firstRequiredTask ? (
        <Button
          disabled={isSearchPending}
          onClick={() => onRunTask(firstRequiredTask)}
          size="sm"
          type="button"
          variant="outline"
        >
          <FileSearch className="h-4 w-4" />
          Run first local task
        </Button>
      ) : null}
      {externalTasks.length ? (
        <Button
          onClick={() => void copyExternalQueries()}
          size="sm"
          type="button"
          variant="outline"
        >
          {copiedKey === "plan-external-followups" ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <Clipboard className="h-4 w-4" />
          )}
          {copiedKey === "plan-external-followups"
            ? "Copied follow-ups"
            : "Copy external follow-ups"}
        </Button>
      ) : null}
    </div>
  );
}
