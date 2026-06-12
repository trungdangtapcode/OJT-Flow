import { Gauge } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import type { EvidenceRankingBoostSignal } from "../model/retrieval-evidence-types";

export function HitRankingSignals({
  formatScore,
  signals,
}: {
  formatScore: (score: number) => string;
  signals: EvidenceRankingBoostSignal[];
}) {
  if (!signals.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Gauge className="h-3.5 w-3.5 shrink-0" />
        <span>Ranking signals</span>
      </div>
      <div className="grid gap-1.5">
        {signals.map((signal) => (
          <div
            className="flex min-w-0 flex-wrap items-center gap-1.5 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs"
            key={signal.ruleId}
          >
            <Badge className="max-w-full break-words" variant="muted">
              {signal.label}
            </Badge>
            {signal.weight !== null ? (
              <span className="font-mono font-semibold text-muted-foreground">
                +{formatScore(signal.weight)}
              </span>
            ) : null}
            <span className="min-w-0 flex-1 break-words font-semibold text-muted-foreground">
              {signal.reason}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
