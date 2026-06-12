import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { cn, humanize } from "../../../lib/utils";
import { SourceReadinessMetric } from "./metric-primitives";
import { formatCount } from "../model/retrieval-format";
import {
  sourceInventoryReadinessMessage,
  sourceInventoryReadinessVariant,
  type SourceInventoryReadiness,
} from "../model/retrieval-source-inventory-model";

export function SourceInventoryReadinessPanel({
  hasSourceFilters,
  readiness,
}: {
  hasSourceFilters: boolean;
  readiness: SourceInventoryReadiness;
}) {
  const blocked = readiness.readiness === "blocked";
  const review = readiness.readiness === "review";
  return (
    <div
      aria-label="Source inventory readiness"
      className={cn(
        "grid gap-2 rounded-md border p-3",
        blocked
          ? "border-red-200 bg-red-50 text-red-950"
          : review
            ? "border-amber-200 bg-amber-50 text-amber-950"
            : "border-emerald-200 bg-emerald-50 text-emerald-950",
      )}
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase">
          Source readiness
          <HelpTooltip label="Source readiness help">
            Summarizes whether the trusted corpus has searchable sources, chunks, domains, and standards before you apply exact source scope.
          </HelpTooltip>
        </div>
        <Badge variant={sourceInventoryReadinessVariant(readiness.readiness)}>
          {humanize(readiness.readiness)}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <SourceReadinessMetric
          label="Sources"
          value={`${readiness.filteredCount}/${readiness.sourceCount}`}
        />
        <SourceReadinessMetric
          label="Chunks"
          value={formatCount(readiness.chunkCount, "chunk")}
        />
        <SourceReadinessMetric
          label="Domains"
          value={formatCount(readiness.domainCount, "domain")}
        />
        <SourceReadinessMetric
          label="Standards"
          value={formatCount(readiness.standardCount, "standard")}
        />
      </div>
      <div className="break-words text-sm font-semibold leading-6">
        {sourceInventoryReadinessMessage(readiness, hasSourceFilters)}
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant={readiness.sourceTypeCount ? "success" : "warning"}>
          {formatCount(readiness.sourceTypeCount, "source type")}
        </Badge>
        <Badge variant={readiness.emptySourceCount ? "warning" : "success"}>
          {readiness.emptySourceCount
            ? formatCount(readiness.emptySourceCount, "empty source")
            : "all shown sources have chunks"}
        </Badge>
        {hasSourceFilters ? <Badge variant="warning">filtered inventory</Badge> : null}
      </div>
    </div>
  );
}
