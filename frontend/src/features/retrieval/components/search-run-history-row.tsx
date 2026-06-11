import { cn } from "../../../lib/utils";
import { SearchRunEvidenceSummary } from "./search-run-evidence-summary";
import { SearchRunHistoryRowActions } from "./search-run-history-row-actions";
import { SearchRunHistoryRowSummary } from "./search-run-history-row-summary";
import type { SearchRunHistoryRun } from "./search-run-history-types";

export function SearchRunHistoryRow<TRun extends SearchRunHistoryRun>({
  active,
  baseline,
  isSearchPending,
  onRestore,
  onSetComparisonBaseline,
  run,
}: {
  active: boolean;
  baseline: boolean;
  isSearchPending: boolean;
  onRestore: (run: TRun) => void;
  onSetComparisonBaseline: (runId: string | null) => void;
  run: TRun;
}) {
  const canSetBaseline = !active && !isSearchPending;
  return (
    <div
      className={cn(
        "grid min-w-0 gap-2 rounded-md border px-3 py-2 text-sm transition-colors",
        active
          ? "border-primary bg-primary/10 text-foreground"
          : "border-border bg-card hover:bg-muted",
      )}
      title={run.payload.query}
    >
      <button
        aria-label={`Restore search run ${run.payload.query}`}
        aria-pressed={active}
        className="grid w-full min-w-0 gap-2 text-left focus-ring disabled:cursor-not-allowed disabled:opacity-70"
        disabled={isSearchPending}
        onClick={() => onRestore(run)}
        type="button"
      >
        <SearchRunHistoryRowSummary baseline={baseline} run={run} />
        <SearchRunEvidenceSummary run={run} />
      </button>
      <SearchRunHistoryRowActions
        baseline={baseline}
        canSetBaseline={canSetBaseline}
        onSetComparisonBaseline={onSetComparisonBaseline}
        run={run}
      />
    </div>
  );
}
