import { ExternalLink } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import { SectionHelpText } from "./section-help-text";
import { formatSearchPlanDetailCount } from "./search-plan-detail-format";
import type { SearchHintStack } from "./search-plan-detail-types";

export function SearchPlanHintPreview({ hints }: { hints: SearchHintStack[] }) {
  if (!hints.length) {
    return (
      <div className="rounded-md border border-border bg-card p-3">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Medical search hints
        </div>
        <SectionHelpText>
          No external medical search target matched. Queries about PubMed, trials, FHIR, LOINC, UCUM, or openFDA will show scoped syntax here.
        </SectionHelpText>
      </div>
    );
  }

  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Medical search hints
        </span>
        <Badge variant="success">
          {formatSearchPlanDetailCount(hints.length, "target")}
        </Badge>
      </div>
      {hints.slice(0, 3).map((hint) => (
        <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-1.5 text-xs" key={`${hint.target}-${hint.query}`}>
          <div className="flex min-w-0 flex-wrap items-center justify-start gap-1.5 sm:justify-between">
            <span className="break-words font-black">{humanize(hint.target)}</span>
            {hint.url ? (
              <Button asChild size="sm" title="Open medical search hint" variant="outline">
                <a href={hint.url} rel="noopener noreferrer" target="_blank">
                  <ExternalLink className="h-4 w-4" />
                  Open
                </a>
              </Button>
            ) : null}
          </div>
          <code className="block max-w-full overflow-hidden break-words rounded bg-muted px-2 py-1 font-mono">
            {hint.query}
          </code>
        </div>
      ))}
    </div>
  );
}
