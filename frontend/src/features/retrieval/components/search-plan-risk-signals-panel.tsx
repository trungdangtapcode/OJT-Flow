import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalPlanRiskSignal } from "../../../types";
import { formatCount } from "../model/retrieval-format";

export function SearchPlanRiskSignalsPanel({
  signals,
}: {
  signals: RetrievalPlanRiskSignal[];
}) {
  if (!signals.length) return null;
  return (
    <div className="grid min-w-0 gap-2 rounded-lg border border-border/60 bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Plan risks
        </span>
        <Badge variant={riskSignalListBadgeVariant(signals)}>
          {formatCount(signals.length, "signal")}
        </Badge>
      </div>
      <div className="grid gap-2">
        {signals.slice(0, 4).map((signal) => (
          <div className="grid gap-1 rounded-lg border border-border/60 bg-muted/20 p-2 text-xs" key={signal.code}>
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge variant={diagnosticBadgeVariant(signal.severity)}>
                {humanize(signal.severity)}
              </Badge>
              <Badge variant="muted">{humanize(signal.source)}</Badge>
              <span className="break-words font-black">{humanize(signal.code)}</span>
            </div>
            <div className="break-words text-muted-foreground">{signal.message}</div>
            <div className="break-words font-semibold">{signal.suggested_action}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function diagnosticBadgeVariant(
  severity: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (severity === "warning") return "warning";
  if (severity === "error") return "destructive";
  if (severity === "info") return "muted";
  return "default";
}

function riskSignalListBadgeVariant(
  signals: RetrievalPlanRiskSignal[],
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (signals.some((signal) => ["destructive", "error"].includes(signal.severity))) {
    return "destructive";
  }
  if (signals.some((signal) => signal.severity === "warning")) return "warning";
  return "muted";
}
