import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { RetrievalPackage } from "../../../types";
import {
  buildEvidenceInterpretationViewModel,
  evidenceSupportBadgeVariant,
} from "../model/evidence-interpretation";
import { EvidenceInterpretationCard } from "./evidence-interpretation-card";

export function EvidenceInterpretationPanel({
  packageData,
}: {
  packageData: RetrievalPackage;
}) {
  const interpretation = buildEvidenceInterpretationViewModel(packageData);
  return (
    <section className="grid gap-3 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Evidence interpretation
            </div>
            <Badge
              variant={
                interpretation.supportStatus
                  ? evidenceSupportBadgeVariant(interpretation.supportStatus)
                  : "muted"
              }
            >
              {interpretation.status}
            </Badge>
            {interpretation.supportStatus ? (
              <Badge variant={evidenceSupportBadgeVariant(interpretation.supportStatus)}>
                {interpretation.supportStatus} support
              </Badge>
            ) : null}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-muted-foreground">
            {interpretation.summary}
          </p>
        </div>
        <HelpTooltip label="Evidence interpretation help">
          This panel summarizes the search package using backend trace data, evidence buckets, score drivers, matched terms, and recommended actions. It is for workflow evidence review, not clinical advice.
        </HelpTooltip>
      </div>

      <div className="grid gap-2 lg:grid-cols-3">
        {interpretation.cards.map((card) => (
          <EvidenceInterpretationCard card={card} key={card.label} />
        ))}
      </div>
    </section>
  );
}
