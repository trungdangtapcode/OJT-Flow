import { Badge } from "../../../components/ui/badge";
import { EvidenceSupportMatrixCardHeader } from "./evidence-support-matrix-card-header";
import { EvidenceSupportMobileField } from "./evidence-support-mobile-field";
import { EvidenceSupportSignalBadges } from "./evidence-support-signal-badges";
import type {
  EvidenceSupportMatrixFormatters,
  EvidenceSupportMatrixRowView,
} from "./evidence-support-matrix-types";

export function EvidenceSupportMatrixCard({
  formatScore,
  humanize,
  judgmentBadgeVariant,
  judgmentLabel,
  row,
  supportStatusBadgeVariant,
}: EvidenceSupportMatrixFormatters & {
  row: EvidenceSupportMatrixRowView;
}) {
  return (
    <article className="grid min-w-0 gap-2 rounded-md border border-border bg-card p-3 text-sm">
      <EvidenceSupportMatrixCardHeader
        formatScore={formatScore}
        humanize={humanize}
        row={row}
        supportStatusBadgeVariant={supportStatusBadgeVariant}
      />
      <div className="grid gap-2">
        <EvidenceSupportMobileField label="Standard">
          {row.standardSystem ? (
            <Badge variant="muted">{row.standardSystem}</Badge>
          ) : (
            <span className="text-xs font-semibold text-muted-foreground">Not specified</span>
          )}
        </EvidenceSupportMobileField>
        <EvidenceSupportMobileField label="Evidence buckets">
          <div className="flex min-w-0 flex-wrap gap-1">
            {row.bucketLabels.length ? (
              row.bucketLabels.map((label) => (
                <Badge key={label} variant="muted">
                  {label}
                </Badge>
              ))
            ) : (
              <Badge variant="warning">No bucket</Badge>
            )}
          </div>
        </EvidenceSupportMobileField>
        <EvidenceSupportMobileField label="Support">
          <EvidenceSupportSignalBadges row={row} />
        </EvidenceSupportMobileField>
        <EvidenceSupportMobileField label="Judgment">
          {row.judgment ? (
            <Badge variant={judgmentBadgeVariant(row.judgment.value)}>
              {judgmentLabel(row.judgment.value)}
            </Badge>
          ) : (
            <Badge variant="muted">Unjudged</Badge>
          )}
        </EvidenceSupportMobileField>
      </div>
    </article>
  );
}
