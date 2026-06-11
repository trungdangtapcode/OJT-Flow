import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalQualitySignal } from "../../../types";
import { QualitySignalMetadataDetails } from "./quality-signal-metadata-details";
import { qualitySignalBadgeVariant } from "./quality-signal-variants";

export function QualitySignalListItem({
  signal,
}: {
  signal: RetrievalQualitySignal;
}) {
  const warning = signal.severity === "warning" || signal.severity === "destructive";
  return (
    <div className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5">
          {warning ? (
            <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600" />
          ) : (
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
          )}
          <span className="break-words font-bold">{humanize(signal.code)}</span>
        </span>
        <Badge variant={qualitySignalBadgeVariant(signal.severity)}>
          {humanize(signal.severity)}
        </Badge>
      </div>
      <div className="break-words text-muted-foreground">{signal.message}</div>
      <div className="break-words font-semibold text-foreground">
        {signal.suggested_action}
      </div>
      <QualitySignalMetadataDetails signal={signal} />
      {signal.evidence_ids.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {signal.evidence_ids.slice(0, 4).map((evidenceId) => (
            <code
              className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px]"
              key={`${signal.code}-${evidenceId}`}
            >
              {evidenceId}
            </code>
          ))}
          {signal.evidence_ids.length > 4 ? (
            <span className="rounded bg-muted px-1.5 py-1 font-bold text-muted-foreground">
              +{signal.evidence_ids.length - 4}
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
