import { History } from "lucide-react";

import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { formatCount } from "./search-run-history-format";
import { SearchRunHistoryRow } from "./search-run-history-row";
import type {
  SearchRunHistoryProps,
  SearchRunHistoryRun,
} from "./search-run-history-types";

export function SearchRunHistory<TRun extends SearchRunHistoryRun>({
  activeRunId,
  comparisonBaselineRunId,
  comparisonNode,
  isSearchPending,
  onClear,
  onRestore,
  onSetComparisonBaseline,
  runs,
}: SearchRunHistoryProps<TRun>) {
  if (!runs.length) return null;
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3 border-b border-border/60 bg-muted/30">
        <div>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            Search runs
          </CardTitle>
          <CardDescription>{formatCount(runs.length, "recent run")}</CardDescription>
        </div>
        <Button
          aria-label="Clear recent search runs"
          disabled={isSearchPending}
          onClick={onClear}
          size="sm"
          type="button"
          variant="ghost"
        >
          Clear
        </Button>
      </CardHeader>
      <CardContent className="grid gap-2 pt-4">
        {runs.map((run) => {
          const active = run.runId === activeRunId;
          const baseline = run.runId === comparisonBaselineRunId;
          return (
            <SearchRunHistoryRow
              active={active}
              baseline={baseline}
              isSearchPending={isSearchPending}
              key={run.runId}
              onRestore={onRestore}
              onSetComparisonBaseline={onSetComparisonBaseline}
              run={run}
            />
          );
        })}
        {comparisonNode ?? null}
      </CardContent>
    </Card>
  );
}
