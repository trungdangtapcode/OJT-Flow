import { Fragment } from "react";
import { ExternalLink, ShieldCheck } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import type { RetrievalHit } from "../../../types";

export type EvidenceProvenanceEntryView = {
  href: string | null;
  label: string;
  value: string;
};

export function EvidenceProvenanceSummary({
  entries,
  formatCount,
}: {
  entries: EvidenceProvenanceEntryView[];
  formatCount: (count: number, singular: string) => string;
}) {
  if (!entries.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
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

function HighlightedText({ text, terms }: { text: string; terms: string[] }) {
  const parts = highlightedParts(text, terms);
  return (
    <>
      {parts.map((part, index) =>
        part.highlight ? (
          <mark
            className="rounded bg-amber-100 px-0.5 font-bold text-amber-950"
            key={`${part.text}-${index}`}
          >
            {part.text}
          </mark>
        ) : (
          <Fragment key={`${part.text}-${index}`}>{part.text}</Fragment>
        ),
      )}
    </>
  );
}

function highlightedParts(text: string, terms: string[]) {
  const normalizedTerms = uniqueMatchedTerms(terms).sort(
    (left, right) => right.length - left.length,
  );
  if (!normalizedTerms.length) {
    return [{ text, highlight: false }];
  }
  const pattern = new RegExp(`(${normalizedTerms.map(escapeRegExp).join("|")})`, "gi");
  return text
    .split(pattern)
    .filter(Boolean)
    .map((part) => ({
      text: part,
      highlight: normalizedTerms.some((term) => part.toLowerCase() === term.toLowerCase()),
    }));
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function uniqueMatchedTerms(terms: string[]) {
  return Array.from(
    new Map(
      terms
        .map((term) => term.trim())
        .filter((term) => term.length > 1)
        .map((term) => [term.toLowerCase(), term] as const),
    ).values(),
  );
}

function formatTermCount(count: number) {
  return count === 1 ? "1 matched term" : `${count} matched terms`;
}
