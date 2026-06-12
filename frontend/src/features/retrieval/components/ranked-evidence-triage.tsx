import { Badge } from "../../../components/ui/badge";
import { RankedEvidenceTriageFacts } from "./ranked-evidence-triage-facts";
import { rankedEvidenceTriageGuidance } from "./ranked-evidence-triage-guidance";
import type { RankedEvidenceTriageView } from "./ranked-evidence-triage-types";

export type { RankedEvidenceTriageView } from "./ranked-evidence-triage-types";

export function RankedEvidenceTriage({ view }: { view: RankedEvidenceTriageView }) {
  const guidance = rankedEvidenceTriageGuidance(view);
  const Icon = guidance.icon;
  return (
    <section
      aria-label="Ranked evidence triage"
      className="grid gap-3 rounded-md border border-border bg-card/80 p-3"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-2">
          <span className="mt-0.5 rounded-md bg-primary/10 p-1.5 text-primary">
            <Icon className="h-4 w-4" />
          </span>
          <div className="grid min-w-0 gap-1">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Inspect first
            </div>
            <div className="break-words text-sm font-black leading-6">
              {guidance.headline}
            </div>
            <div className="break-words text-sm leading-6 text-muted-foreground">
              {guidance.detail}
            </div>
          </div>
        </div>
        <Badge variant={guidance.variant}>{guidance.state}</Badge>
      </div>
      <RankedEvidenceTriageFacts view={view} />
    </section>
  );
}
