import { Network } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { ConceptMatchExplanationView } from "./hit-explanation-types";

export function ConceptMatchExplanation({
  matches,
}: {
  matches: ConceptMatchExplanationView[];
}) {
  if (!matches.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Network className="h-3.5 w-3.5 shrink-0" />
        <span>Concept grounding</span>
      </div>
      <div className="grid gap-1.5">
        {matches.map((match) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs"
            key={`${match.standardSystem}-${match.conceptId}`}
          >
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge className="max-w-full break-words" variant="success">
                {match.standardSystem}
                {match.code ? ` ${match.code}` : ""}
              </Badge>
              <span className="min-w-0 break-words font-bold">{match.displayName}</span>
              <span className="font-mono font-semibold text-muted-foreground">
                {Math.round(match.confidence * 100)}%
              </span>
            </div>
            <div className="break-words font-semibold text-muted-foreground">
              {match.reason}
            </div>
            <div className="flex min-w-0 flex-wrap gap-1">
              {match.matchedFields.map((field) => (
                <span
                  className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                  key={`${match.conceptId}-${field}`}
                >
                  {humanize(field)}
                </span>
              ))}
              {match.matchedAliases.slice(0, 3).map((alias) => (
                <span
                  className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                  key={`${match.conceptId}-${alias}`}
                >
                  {alias}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
