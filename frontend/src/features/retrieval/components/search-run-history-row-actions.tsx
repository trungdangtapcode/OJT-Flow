import { GitCompareArrows } from "lucide-react";

import { Button } from "../../../components/ui/button";
import type { SearchRunHistoryRun } from "./search-run-history-types";

export function SearchRunHistoryRowActions<TRun extends SearchRunHistoryRun>({
  baseline,
  canSetBaseline,
  onSetComparisonBaseline,
  run,
}: {
  baseline: boolean;
  canSetBaseline: boolean;
  onSetComparisonBaseline: (runId: string | null) => void;
  run: TRun;
}) {
  return (
    <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
      <Button
        aria-label={
          baseline
            ? `Clear comparison baseline ${run.payload.query}`
            : `Use ${run.payload.query} as comparison baseline`
        }
        disabled={!canSetBaseline}
        onClick={() => onSetComparisonBaseline(baseline ? null : run.runId)}
        size="sm"
        type="button"
        variant={baseline ? "secondary" : "outline"}
      >
        <GitCompareArrows className="h-4 w-4" />
        {baseline ? "Baseline" : "Set baseline"}
      </Button>
    </div>
  );
}
