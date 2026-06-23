import { ExternalLink, ShieldCheck } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import type { EvidenceProvenanceEntryView } from "./evidence-provenance-types";

export function EvidenceProvenanceSummary({
  entries,
  formatCount,
}: {
  entries: EvidenceProvenanceEntryView[];
  formatCount: (count: number, singular: string) => string;
}) {
  if (!entries.length) return null;
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
          <span>Evidence provenance</span>
        </div>
        <Badge variant="muted">{formatCount(entries.length, "field")}</Badge>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {entries.map((entry) => (
          <span
            className="inline-flex max-w-full items-center gap-1 rounded-full border border-border bg-card/70 px-2 py-1 text-xs font-semibold text-muted-foreground"
            key={`${entry.label}-${entry.value}`}
          >
            <span className="shrink-0 font-bold text-foreground">{entry.label}:</span>
            {entry.href ? (
              <a
                className="inline-flex min-w-0 items-center gap-1 break-words text-primary underline-offset-2 hover:underline"
                href={entry.href}
                rel="noopener noreferrer"
                target="_blank"
              >
                <span className="min-w-0 break-words">{entry.value}</span>
                <ExternalLink className="h-3 w-3 shrink-0" />
              </a>
            ) : (
              <span className="min-w-0 break-words">{entry.value}</span>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
