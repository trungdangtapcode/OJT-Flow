import { Badge } from "../../../components/ui/badge";
import type { RetrievalQualitySignal } from "../../../types";
import { QualitySignalListItem } from "./quality-signal-list-item";
import {
  qualitySignalBadgeVariant,
  qualitySignalSummaryVariant,
} from "./quality-signal-variants";
import { SectionHelpText } from "./section-help-text";
import { TokenList } from "./token-list";

export { qualitySignalBadgeVariant } from "./quality-signal-variants";

export function QualitySignalList({ signals }: { signals: RetrievalQualitySignal[] }) {
  if (!signals.length) {
    return (
      <TokenList
        description="Backend quality checks did not return warnings or blockers."
        items={[]}
        title="Retrieval quality"
      />
    );
  }
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Retrieval quality
        </div>
        <Badge variant={qualitySignalSummaryVariant(signals)}>
          {formatCount(signals.length, "signal")}
        </Badge>
      </div>
      <SectionHelpText>
        Quality signals explain why the evidence package is ready, needs review, or is blocked.
      </SectionHelpText>
      <div className="grid gap-2">
        {signals.map((signal) => (
          <QualitySignalListItem key={signal.code} signal={signal} />
        ))}
      </div>
    </div>
  );
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
