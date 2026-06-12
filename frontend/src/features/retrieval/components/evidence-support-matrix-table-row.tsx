import { Badge } from "../../../components/ui/badge";
import { TD, TR } from "../../../components/ui/table";
import { EvidenceSupportSignalBadges } from "./evidence-support-signal-badges";
import type {
  EvidenceSupportMatrixFormatters,
  EvidenceSupportMatrixRowView,
} from "./evidence-support-matrix-types";

export function EvidenceSupportMatrixTableRow({
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
    <TR>
      <TD className="font-mono text-xs font-bold">#{row.rank}</TD>
      <TD>
        <div className="max-w-72 break-words font-bold">{row.sourceId}</div>
        <div className="mt-1 text-xs text-muted-foreground">
          {humanize(row.sourceType)} / {row.confidenceLabel}
        </div>
      </TD>
      <TD>
        {row.standardSystem ? (
          <Badge variant="muted">{row.standardSystem}</Badge>
        ) : (
          <span className="text-xs font-semibold text-muted-foreground">-</span>
        )}
      </TD>
      <TD>
        <div className="flex min-w-52 flex-wrap gap-1">
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
      </TD>
      <TD>
        <div className="min-w-44">
          <EvidenceSupportSignalBadges row={row} />
        </div>
      </TD>
      <TD>
        {row.judgment ? (
          <Badge variant={judgmentBadgeVariant(row.judgment.value)}>
            {judgmentLabel(row.judgment.value)}
          </Badge>
        ) : (
          <Badge variant="muted">Unjudged</Badge>
        )}
      </TD>
      <TD>
        <div className="font-mono text-xs font-bold">{formatScore(row.score)}</div>
        <Badge variant={supportStatusBadgeVariant(row.supportStatus)}>
          {humanize(row.supportStatus)}
        </Badge>
      </TD>
    </TR>
  );
}
