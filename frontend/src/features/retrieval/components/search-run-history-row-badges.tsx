import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { CorrectiveActionTypeCountChips } from "./corrective-action-type-count-chips";
import {
  formatCount,
  formatRunTime,
  formatShortSignature,
} from "./search-run-history-format";
import type { SearchRunHistoryRun } from "./search-run-history-types";

export function SearchRunHistoryMetadataBadges<TRun extends SearchRunHistoryRun>({
  run,
}: {
  run: TRun;
}) {
  return (
    <span className="flex min-w-0 flex-wrap gap-1.5">
      <Badge variant="muted">{formatRunTime(run.submittedAt)}</Badge>
      <Badge variant="muted">top {run.payload.top_k}</Badge>
      <Badge variant="muted">{formatCount(run.summary.hitCount, "hit")}</Badge>
      <Badge variant="muted">
        {formatCount(run.summary.candidateCount, "candidate")}
      </Badge>
      <Badge variant="muted">
        {formatCount(run.summary.rulePackCount, "rule pack")}
      </Badge>
      {run.summary.serverSignature ? (
        <Badge variant="muted">
          {formatShortSignature(run.summary.serverSignature)}
        </Badge>
      ) : null}
      {run.summary.queryProfile ? (
        <Badge variant="muted">{humanize(run.summary.queryProfile.route)}</Badge>
      ) : null}
      {run.summary.warningCount ? (
        <Badge variant="warning">
          {formatCount(run.summary.warningCount, "warning")}
        </Badge>
      ) : null}
      {run.summary.correctiveActionSummary.count ? (
        <Badge variant="warning">
          {formatCount(run.summary.correctiveActionSummary.count, "action")}
        </Badge>
      ) : null}
      <CorrectiveActionTypeCountChips
        counts={run.summary.correctiveActionSummary.actionTypeCounts}
      />
    </span>
  );
}
