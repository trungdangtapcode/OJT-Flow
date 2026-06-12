import { ListFilter } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { QueryAspectMatchExplanationView } from "./hit-explanation-types";

export function QueryAspectMatchExplanation({
  matches,
}: {
  matches: QueryAspectMatchExplanationView[];
}) {
  if (!matches.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <ListFilter className="h-3.5 w-3.5 shrink-0" />
        <span>Aspect support</span>
      </div>
      <div className="grid gap-1.5">
        {matches.map((match) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs"
            key={`${match.aspectId}-${match.ruleId}`}
          >
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge className="max-w-full break-words" variant="success">
                {match.label}
              </Badge>
              <Badge variant="muted">priority {match.priority}</Badge>
              <span className="min-w-0 break-words font-semibold text-muted-foreground">
                {match.reason}
              </span>
            </div>
            {match.matchedTerms.length || Object.keys(match.matchedFilters).length ? (
              <div className="flex min-w-0 flex-wrap gap-1">
                {Object.entries(match.matchedFilters).map(([field, value]) => (
                  <span
                    className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                    key={`${match.aspectId}-${field}`}
                  >
                    {humanize(field)}: {value}
                  </span>
                ))}
                {match.matchedTerms.slice(0, 4).map((term) => (
                  <span
                    className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                    key={`${match.aspectId}-${term}`}
                  >
                    {term}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
