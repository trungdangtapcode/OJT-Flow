import { Badge } from "../../../components/ui/badge";
import type { RetrievalHit } from "../../../types";
import { formatTermCount, uniqueMatchedTerms } from "./evidence-highlight-utils";
import { HighlightedText } from "./highlighted-text";

export function SnippetBlock({
  formatClaim,
  snippet,
}: {
  formatClaim: (claim: string) => string;
  snippet: NonNullable<RetrievalHit["snippet"]>;
}) {
  const matchedTerms = uniqueMatchedTerms(snippet.matched_terms);
  return (
    <div className="grid gap-2 rounded-md border border-primary/20 bg-primary/5 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-bold uppercase text-primary">Best snippet</span>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          {matchedTerms.length ? (
            <Badge variant="success">{formatTermCount(matchedTerms.length)}</Badge>
          ) : null}
          <Badge variant="muted">
            chars {snippet.start_char}-{snippet.end_char}
          </Badge>
        </div>
      </div>
      <p className="break-words text-sm leading-6">
        <HighlightedText terms={matchedTerms} text={formatClaim(snippet.text)} />
      </p>
      {matchedTerms.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {matchedTerms.slice(0, 8).map((term) => (
            <span
              className="max-w-full break-words rounded-full bg-background px-2 py-1 text-[11px] font-bold text-primary"
              key={term}
            >
              {term}
            </span>
          ))}
          {matchedTerms.length > 8 ? (
            <span className="rounded-full bg-background px-2 py-1 text-[11px] font-bold text-muted-foreground">
              +{matchedTerms.length - 8} more
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
