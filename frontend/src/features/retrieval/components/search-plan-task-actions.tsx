import { CheckCircle2, Clipboard, ExternalLink, FileSearch } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import type { RetrievalSearchTask } from "../../../types";
import { retrievalTaskExternalUrl } from "../model/search-plan-tasks";

export function SearchPlanTaskActions({
  copied,
  isSearchPending,
  onCopyQuery,
  onRunTask,
  task,
}: {
  copied: boolean;
  isSearchPending: boolean;
  onCopyQuery: () => void;
  onRunTask: (task: RetrievalSearchTask) => void;
  task: RetrievalSearchTask;
}) {
  const externalUrl = retrievalTaskExternalUrl(task);
  return (
    <div className="flex min-w-0 flex-wrap justify-start gap-1.5 sm:justify-end">
      <Button onClick={onCopyQuery} size="sm" type="button" variant="outline">
        {copied ? <CheckCircle2 className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
        {copied ? "Copied" : "Copy query"}
      </Button>
      {task.action_type === "run_local_search" ? (
        <Button
          disabled={isSearchPending}
          onClick={() => onRunTask(task)}
          size="sm"
          type="button"
          variant="outline"
        >
          <FileSearch className="h-4 w-4" />
          Run task
        </Button>
      ) : task.action_type === "open_external_url" && externalUrl ? (
        <Button asChild size="sm" type="button" variant="outline">
          <a href={externalUrl} rel="noopener noreferrer" target="_blank">
            <ExternalLink className="h-4 w-4" />
            Open follow-up
          </a>
        </Button>
      ) : (
        <Badge variant="muted">{task.action_type === "copy_query" ? "copy query" : "syntax only"}</Badge>
      )}
    </div>
  );
}
