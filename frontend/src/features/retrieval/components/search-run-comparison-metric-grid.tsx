import {
  RunComparisonMetric,
} from "./run-comparison-summary-panels";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export function SearchRunComparisonMetricGrid({
  candidateDelta,
  deltaBadgeVariant,
  formatSignedDelta,
  hitDelta,
  qualityWarningDelta,
  warningDelta,
}: {
  candidateDelta: number;
  deltaBadgeVariant: (delta: number, positiveIsGood: boolean) => BadgeVariant;
  formatSignedDelta: (delta: number) => string;
  hitDelta: number;
  qualityWarningDelta: number;
  warningDelta: number;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      <RunComparisonMetric
        delta={hitDelta}
        deltaBadgeVariant={deltaBadgeVariant}
        formatSignedDelta={formatSignedDelta}
        label="Hits"
        positiveIsGood
      />
      <RunComparisonMetric
        delta={candidateDelta}
        deltaBadgeVariant={deltaBadgeVariant}
        formatSignedDelta={formatSignedDelta}
        label="Candidates"
        positiveIsGood
      />
      <RunComparisonMetric
        delta={warningDelta}
        deltaBadgeVariant={deltaBadgeVariant}
        formatSignedDelta={formatSignedDelta}
        label="Warnings"
        positiveIsGood={false}
      />
      <RunComparisonMetric
        delta={qualityWarningDelta}
        deltaBadgeVariant={deltaBadgeVariant}
        formatSignedDelta={formatSignedDelta}
        label="Quality issues"
        positiveIsGood={false}
      />
    </div>
  );
}
