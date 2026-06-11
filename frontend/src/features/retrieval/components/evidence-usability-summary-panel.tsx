import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { supportStatusBadgeVariant } from "./evidence-support-status";
import type { EvidenceUsabilitySummaryView } from "./evidence-interpretation-guidance-types";

export function EvidenceUsabilitySummaryPanel({
  summary,
}: {
  summary: EvidenceUsabilitySummaryView;
}) {
  return (
    <section
      aria-label="Evidence usability summary"
      className="grid gap-2 rounded-md border border-border bg-muted/20 p-2 text-sm"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="grid min-w-0 gap-1">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Usability summary
          </div>
          <div className="break-words font-semibold">{summary.headline}</div>
        </div>
        <Badge variant={supportStatusBadgeVariant(summary.status)}>
          {humanize(summary.status)}
        </Badge>
      </div>
      <div className="grid gap-1.5 sm:grid-cols-2">
        <div className="rounded-md border border-border bg-card/70 px-2 py-1.5">
          <div className="text-[11px] font-black uppercase text-muted-foreground">
            Recommendation
          </div>
          <div className="mt-1 break-words font-semibold">
            {summary.recommendation}
          </div>
        </div>
        <div className="rounded-md border border-border bg-card/70 px-2 py-1.5">
          <div className="text-[11px] font-black uppercase text-muted-foreground">
            Limitation
          </div>
          <div className="mt-1 break-words text-muted-foreground">
            {summary.limitation}
          </div>
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {summary.checks.map((check) => (
          <Badge className="max-w-full break-words" key={check} variant="muted">
            {check}
          </Badge>
        ))}
      </div>
    </section>
  );
}
