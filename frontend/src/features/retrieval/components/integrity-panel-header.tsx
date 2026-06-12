import { AlertTriangle, CheckCircle2, Database, Loader2, RefreshCw } from "lucide-react";

import { Button } from "../../../components/ui/button";
import {
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { cn } from "../../../lib/utils";
import type { IntegrityPanelProps } from "./integrity-panel-types";

export function IntegrityPanelHeader({
  includeCorpus,
  isFetching,
  onRefresh,
  onToggleCorpus,
  report,
}: Pick<
  IntegrityPanelProps,
  "includeCorpus" | "isFetching" | "onRefresh" | "onToggleCorpus" | "report"
>) {
  const status = report?.status ?? "loading";
  const StatusIcon = status === "ok" ? CheckCircle2 : AlertTriangle;

  return (
    <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70">
      <div className="min-w-0">
        <CardTitle className="flex items-center gap-2">
          <StatusIcon
            className={cn(
              "h-5 w-5",
              status === "ok" ? "text-emerald-700" : "text-amber-700",
            )}
          />
          Index integrity
        </CardTitle>
        <CardDescription>
          {report
            ? `${report.repository} / ${report.checked_scope}`
            : "Checking indexed knowledge consistency"}
        </CardDescription>
      </div>
      <div className="flex flex-wrap justify-end gap-2">
        <Button onClick={onToggleCorpus} size="sm" type="button" variant="outline">
          <Database className="h-4 w-4" />
          {includeCorpus ? "Corpus on" : "Seeded only"}
        </Button>
        <Button disabled={isFetching} onClick={onRefresh} size="sm" type="button" variant="outline">
          {isFetching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>
    </CardHeader>
  );
}
