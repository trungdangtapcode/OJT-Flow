import { Badge } from "../../../components/ui/badge";
import type {
  EvidenceSupportMatrixFormatters,
  EvidenceSupportMatrixRowView,
} from "./evidence-support-matrix-types";

export function EvidenceSupportMatrixCardHeader({
  formatScore,
  humanize,
  row,
  supportStatusBadgeVariant,
}: Pick<
  EvidenceSupportMatrixFormatters,
  "formatScore" | "humanize" | "supportStatusBadgeVariant"
> & {
  row: EvidenceSupportMatrixRowView;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
      <div className="min-w-0">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Rank {row.rank}
        </div>
        <div className="mt-1 break-words font-black">{row.sourceId}</div>
        <div className="mt-1 text-xs font-semibold text-muted-foreground">
          {humanize(row.sourceType)} / {row.confidenceLabel}
        </div>
      </div>
      <div className="flex shrink-0 flex-wrap justify-end gap-1">
        <Badge variant={supportStatusBadgeVariant(row.supportStatus)}>
          {humanize(row.supportStatus)}
        </Badge>
        <Badge variant="muted">{formatScore(row.score)}</Badge>
      </div>
    </div>
  );
}
