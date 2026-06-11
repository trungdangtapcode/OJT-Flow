import { humanize } from "../../../lib/utils";
import type { SearchRunHistoryRun } from "./search-run-history-types";

export function SearchRunHistoryDetailLines<TRun extends SearchRunHistoryRun>({
  run,
}: {
  run: TRun;
}) {
  return (
    <>
      {run.summary.topSourceId ? (
        <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
          Top source: {run.summary.topSourceId}
        </span>
      ) : null}
      {run.summary.queryProfile ? (
        <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
          Profile: {run.summary.queryProfile.label} /{" "}
          {humanize(run.summary.queryProfile.retrievalMode)}
        </span>
      ) : null}
      {run.summary.correctiveActionSummary.topActionTitle ? (
        <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
          Top action: {run.summary.correctiveActionSummary.topActionTitle}
          {run.summary.correctiveActionSummary.highestPriority
            ? ` / P${run.summary.correctiveActionSummary.highestPriority}`
            : ""}
        </span>
      ) : null}
    </>
  );
}
