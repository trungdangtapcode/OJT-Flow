import type { HighlightedTextPart } from "./evidence-provenance-types";

export function highlightedParts(text: string, terms: string[]): HighlightedTextPart[] {
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

export function uniqueMatchedTerms(terms: string[]) {
  return Array.from(
    new Map(
      terms
        .map((term) => term.trim())
        .filter((term) => term.length > 1)
        .map((term) => [term.toLowerCase(), term] as const),
    ).values(),
  );
}

export function formatTermCount(count: number) {
  return count === 1 ? "1 matched term" : `${count} matched terms`;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
