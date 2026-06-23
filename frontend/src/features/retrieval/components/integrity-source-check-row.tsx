import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalIntegrityItem } from "../../../types";
import { IntegrityFact } from "./metric-primitives";
import type { IntegrityPanelProps } from "./integrity-panel-types";

export function IntegritySourceCheckRow({
  check,
  formatHash,
  integrityBadgeVariant,
}: {
  check: RetrievalIntegrityItem;
  formatHash: IntegrityPanelProps["formatHash"];
  integrityBadgeVariant: IntegrityPanelProps["integrityBadgeVariant"];
}) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3 text-sm">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="break-all font-mono text-xs font-bold">
            {check.source_id}
          </div>
          <div className="mt-1 break-words text-xs text-muted-foreground">
            {check.message}
          </div>
        </div>
        <Badge variant={integrityBadgeVariant(check.status)}>
          {humanize(check.status)}
        </Badge>
      </div>
      <div className="grid gap-2 text-xs sm:grid-cols-4">
        <IntegrityFact label="Expected" value={`${check.expected_chunk_count}`} />
        <IntegrityFact label="Indexed" value={`${check.indexed_chunk_count}`} />
        <IntegrityFact label="Expected hash" value={formatHash(check.expected_hash)} />
        <IntegrityFact label="Indexed hash" value={formatHash(check.indexed_hash)} />
      </div>
    </div>
  );
}
