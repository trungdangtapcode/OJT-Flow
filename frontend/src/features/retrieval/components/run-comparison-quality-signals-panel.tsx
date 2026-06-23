import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type {
  BadgeVariant,
  RetrievalQualitySignalComparisonView,
  RetrievalQualitySignalSummaryView,
} from "./run-comparison-detail-types";

export function RunComparisonQualitySignals({
  comparison,
  formatCount,
}: {
  comparison: RetrievalQualitySignalComparisonView;
  formatCount: (count: number, singular: string) => string;
}) {
  const changed = comparison.added.length + comparison.removed.length;
  const total = changed + comparison.retained.length;
  if (!total) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Quality signals</span>
        <Badge variant="success">none</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Quality signals</span>
        <Badge variant={changed ? "warning" : "success"}>
          {changed ? formatCount(changed, "changed signal") : "stable"}
        </Badge>
      </div>
      <QualitySignalChangeList
        label="Added"
        signals={comparison.added}
        variant="warning"
      />
      <QualitySignalChangeList
        label="Removed"
        signals={comparison.removed}
        variant="success"
      />
      <QualitySignalChangeList
        label="Retained"
        signals={comparison.retained}
        variant="muted"
      />
    </div>
  );
}

function QualitySignalChangeList({
  label,
  signals,
  variant,
}: {
  label: string;
  signals: RetrievalQualitySignalSummaryView[];
  variant: BadgeVariant;
}) {
  if (!signals.length) return null;
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-semibold text-muted-foreground">{label}:</span>
        {signals.slice(0, 4).map((signal) => (
          <Badge key={`${label}-${signal.code}`} variant={variant}>
            {humanize(signal.code)}
          </Badge>
        ))}
        {signals.length > 4 ? <Badge variant="muted">+{signals.length - 4}</Badge> : null}
      </div>
      <div className="grid gap-1">
        {signals.slice(0, 2).map((signal) => (
          <div className="break-words text-muted-foreground" key={`${label}-${signal.code}-message`}>
            {humanize(signal.severity)}: {signal.message}
          </div>
        ))}
      </div>
    </div>
  );
}
