import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { TokenList } from "./token-list";

export type ConceptCandidateListItem = {
  clinicalDomain: string | null;
  code: string | null;
  conceptId: string;
  confidence: number;
  displayName: string;
  matchedAliases: string[];
  standardSystem: string;
};

export function ConceptCandidateList({
  candidates,
}: {
  candidates: ConceptCandidateListItem[];
}) {
  if (!candidates.length) {
    return <TokenList items={[]} title="Concept candidates" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Concept candidates
      </div>
      <div className="grid gap-2">
        {candidates.map((candidate) => (
          <div
            className="grid gap-1.5 rounded-lg border border-border/60 bg-card p-2 text-xs"
            key={`${candidate.standardSystem}-${candidate.code}-${candidate.conceptId}`}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{candidate.displayName}</span>
              <Badge variant="success">
                {candidate.standardSystem}
                {candidate.code ? ` ${candidate.code}` : ""}
              </Badge>
            </div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              <span className="rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground">
                {humanize(candidate.clinicalDomain ?? "unknown")}
              </span>
              <span className="rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground">
                {Math.round(candidate.confidence * 100)}%
              </span>
              {candidate.matchedAliases.slice(0, 4).map((alias) => (
                <span
                  className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                  key={`${candidate.conceptId}-${alias}`}
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
