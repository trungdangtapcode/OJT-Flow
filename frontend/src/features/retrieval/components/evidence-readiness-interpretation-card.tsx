import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalQualitySummary } from "../../../types";
import type { EvidenceReadinessInterpretation } from "../model/evidence-readiness-model";

export function EvidenceReadinessInterpretationCard({
  interpretation,
  qualitySummary,
}: {
  interpretation: EvidenceReadinessInterpretation;
  qualitySummary: RetrievalQualitySummary | null;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="break-words text-sm font-black">{interpretation.title}</div>
        <Badge variant={interpretation.variant}>{interpretation.badge}</Badge>
      </div>
      <p className="break-words text-sm leading-6 text-muted-foreground">
        {interpretation.description}
      </p>
      {qualitySummary ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {qualitySummary.blocker_codes.slice(0, 4).map((code) => (
            <Badge
              className="max-w-full break-words"
              key={`blocker-${code}`}
              variant="destructive"
            >
              {humanize(code)}
            </Badge>
          ))}
          {qualitySummary.warning_codes.slice(0, 4).map((code) => (
            <Badge
              className="max-w-full break-words"
              key={`warning-${code}`}
              variant="warning"
            >
              {humanize(code)}
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}
