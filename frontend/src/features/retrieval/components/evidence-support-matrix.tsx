import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { EvidenceSupportMatrixCard } from "./evidence-support-matrix-card";
import { EvidenceSupportMatrixTable } from "./evidence-support-matrix-table";
import type {
  BadgeVariant,
  EvidenceSupportMatrixRowView,
} from "./evidence-support-matrix-types";
import type { RelevanceJudgmentValue } from "../model/retrieval-judgment-types";
import { SectionHelpText } from "./section-help-text";

export type { EvidenceSupportMatrixRowView } from "./evidence-support-matrix-types";

export function EvidenceSupportMatrix({
  formatCount,
  formatScore,
  humanize,
  judgmentBadgeVariant,
  judgmentLabel,
  rows,
  supportStatusBadgeVariant,
}: {
  formatCount: (count: number, singular: string) => string;
  formatScore: (score: number) => string;
  humanize: (value: string) => string;
  judgmentBadgeVariant: (value: RelevanceJudgmentValue) => BadgeVariant;
  judgmentLabel: (value: RelevanceJudgmentValue) => string;
  rows: EvidenceSupportMatrixRowView[];
  supportStatusBadgeVariant: (
    status: EvidenceSupportMatrixRowView["supportStatus"],
  ) => BadgeVariant;
}) {
  if (!rows.length) return null;
  return (
    <section className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            <span>Evidence support matrix</span>
            <HelpTooltip label="Evidence support matrix help">
              Fast scan of whether each ranked hit has terms, provenance, concept grounding, query-aspect support, judgment state, and enough score support to trust for review.
            </HelpTooltip>
          </div>
          <div className="mt-1 text-sm font-semibold text-muted-foreground">
            Coverage, grounding, provenance, and review state for selected evidence.
          </div>
        </div>
        <Badge variant={rows.some((row) => row.supportStatus === "weak") ? "warning" : "success"}>
          {formatCount(rows.length, "evidence row")}
        </Badge>
      </div>
      <SectionHelpText>
        Weak rows need inspection before use. Missing provenance means the source locator is thin; missing concepts or aspects means the hit may match words without enough medical grounding.
      </SectionHelpText>
      <div className="grid gap-2 md:hidden">
        {rows.map((row) => (
          <EvidenceSupportMatrixCard
            formatScore={formatScore}
            humanize={humanize}
            judgmentBadgeVariant={judgmentBadgeVariant}
            judgmentLabel={judgmentLabel}
            key={row.evidenceId}
            row={row}
            supportStatusBadgeVariant={supportStatusBadgeVariant}
          />
        ))}
      </div>
      <EvidenceSupportMatrixTable
        formatScore={formatScore}
        humanize={humanize}
        judgmentBadgeVariant={judgmentBadgeVariant}
        judgmentLabel={judgmentLabel}
        rows={rows}
        supportStatusBadgeVariant={supportStatusBadgeVariant}
      />
    </section>
  );
}
