import { CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import type { RetrievalSearchTask } from "../../../types";
import { retrievalTaskClipboardText } from "../model/search-plan-tasks";
import {
  optionalTaskCountView,
  requiredTaskCountView,
  taskGroupCountGuidance,
  type SearchPlanTaskGroupBadgeVariant,
} from "./search-plan-task-group-count-view";
import type { SearchPlanTaskPreviewCallbacks } from "./search-plan-task-preview";

export function SearchPlanTaskGroupToolbar({
  copyKey,
  copyTextToClipboard,
  copied,
  markCopied,
  orderedTasks,
  optionalTaskCount,
  requiredTaskCount,
}: Pick<SearchPlanTaskPreviewCallbacks, "copyTextToClipboard"> & {
  copyKey: string;
  copied: boolean;
  markCopied: (key: string) => void;
  orderedTasks: RetrievalSearchTask[];
  optionalTaskCount: number;
  requiredTaskCount: number;
}) {
  const copyGroupQueries = async () => {
    await copyTextToClipboard(
      orderedTasks.map((task) => retrievalTaskClipboardText(task)).join("\n\n"),
    );
    markCopied(copyKey);
  };

  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
      <SearchPlanTaskGroupCounts
        optionalTaskCount={optionalTaskCount}
        requiredTaskCount={requiredTaskCount}
      />
      <Button
        onClick={() => void copyGroupQueries()}
        size="sm"
        type="button"
        variant="outline"
      >
        {copied ? <CheckCircle2 className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
        {copied ? "Copied group" : "Copy group queries"}
      </Button>
    </div>
  );
}

function SearchPlanTaskGroupCounts({
  optionalTaskCount,
  requiredTaskCount,
}: {
  optionalTaskCount: number;
  requiredTaskCount: number;
}) {
  const requiredCount = requiredTaskCountView(requiredTaskCount);
  const optionalCount = optionalTaskCountView(optionalTaskCount);
  const guidance = taskGroupCountGuidance(requiredTaskCount);

  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5">
      <Badge variant={requiredCount.variant}>{requiredCount.label}</Badge>
      <Badge variant={optionalCount.variant}>{optionalCount.label}</Badge>
      <span className="break-words text-xs font-semibold text-muted-foreground">
        {guidance}
      </span>
    </div>
  );
}
export type { SearchPlanTaskGroupBadgeVariant };
