import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type {
  QueryProfileSummaryView,
  RunComparisonQueryProfileView,
} from "./run-comparison-detail-types";

export function RunComparisonQueryProfile({
  comparison,
}: {
  comparison: RunComparisonQueryProfileView;
}) {
  const before = comparison.baselineSummary.queryProfile;
  const after = comparison.activeSummary.queryProfile;
  if (!before && !after) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Query profile</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-1 rounded-lg border border-border/60 bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Query profile</span>
        <Badge variant={comparison.queryProfileChanged ? "warning" : "success"}>
          {comparison.queryProfileChanged ? "changed" : "stable"}
        </Badge>
      </div>
      <div className="grid gap-1 sm:grid-cols-2">
        <QueryProfileSummaryCard label="Baseline" profile={before} />
        <QueryProfileSummaryCard label="Active" profile={after} />
      </div>
    </div>
  );
}

function QueryProfileSummaryCard({
  label,
  profile,
}: {
  label: string;
  profile: QueryProfileSummaryView | null;
}) {
  if (!profile) {
    return (
      <div className="rounded-md bg-muted/40 px-2 py-1.5 text-muted-foreground">
        {label}: unavailable
      </div>
    );
  }
  return (
    <div className="grid gap-1 rounded-md bg-muted/40 px-2 py-1.5">
      <span className="font-bold">{label}</span>
      <span className="break-words">{profile.label}</span>
      <span className="break-words text-muted-foreground">
        {humanize(profile.route)} / {humanize(profile.retrievalMode)} /{" "}
        {humanize(profile.complexity)}
      </span>
    </div>
  );
}
