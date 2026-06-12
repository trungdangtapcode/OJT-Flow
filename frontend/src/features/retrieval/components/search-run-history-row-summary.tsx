import { Badge } from "../../../components/ui/badge";
import { SearchRunHistoryMetadataBadges } from "./search-run-history-row-badges";
import { SearchRunHistoryDetailLines } from "./search-run-history-row-details";
import {
  formatCount,
  searchRunSummaryVariant,
} from "./search-run-history-format";
import type { SearchRunHistoryRun } from "./search-run-history-types";

export function SearchRunHistoryRowSummary<TRun extends SearchRunHistoryRun>({
  baseline,
  run,
}: {
  baseline: boolean;
  run: TRun;
}) {
  return (
    <>
      <span className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="min-w-0 break-words font-black">{run.payload.query}</span>
        <span className="flex min-w-0 flex-wrap justify-end gap-1.5">
          {baseline ? <Badge variant="default">baseline</Badge> : null}
          <Badge variant={searchRunSummaryVariant(run.summary)}>
            {run.summary.qualityWarningCount
              ? formatCount(run.summary.qualityWarningCount, "issue")
              : "ready"}
          </Badge>
        </span>
      </span>
      <SearchRunHistoryMetadataBadges run={run} />
      <SearchRunHistoryDetailLines run={run} />
    </>
  );
}
