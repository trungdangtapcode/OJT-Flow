import { Gauge } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import type { RetrievalScoreComponent } from "../../../types";

export function ScoreMeter({
  formatScore,
  label,
  value,
}: {
  formatScore: (value: number) => string;
  label: string;
  value: number;
}) {
  const normalized = Math.max(0, Math.min(100, Math.abs(value) * 100));
  return (
    <div className="grid gap-1 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex items-center justify-between gap-2 text-xs font-bold">
        <span>{label}</span>
        <span className="tabular-nums text-muted-foreground">{formatScore(value)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-border">
        <div className="h-full rounded-full bg-primary" style={{ width: `${normalized}%` }} />
      </div>
    </div>
  );
}

export function ScoreExplanation({
  components,
  formatScore,
}: {
  components: RetrievalScoreComponent[];
  formatScore: (value: number) => string;
}) {
  if (!components.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Gauge className="h-3.5 w-3.5 shrink-0" />
        <span>Score explanation</span>
      </div>
      <div className="grid gap-1.5">
        {components.map((component) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs md:grid-cols-[10rem_5rem_minmax(0,1fr)] md:items-center"
            key={component.component}
          >
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <span className="min-w-0 break-words font-bold">{component.label}</span>
              {component.rank ? <Badge variant="muted">rank {component.rank}</Badge> : null}
            </div>
            <span className="font-mono font-semibold tabular-nums text-muted-foreground">
              {formatScore(component.value)}
            </span>
            <span className="min-w-0 break-words font-semibold text-muted-foreground">
              {component.description}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
