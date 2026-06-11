export function HitMatchedTerms({ terms }: { terms: string[] }) {
  return (
    <div className="flex min-w-0 flex-wrap gap-1.5">
      {terms.slice(0, 12).map((term) => (
        <span
          className="max-w-full break-words rounded-full bg-muted px-2 py-1 text-xs font-bold text-muted-foreground"
          key={term}
        >
          {term}
        </span>
      ))}
      {!terms.length ? (
        <span className="text-xs font-semibold text-muted-foreground">No exact terms matched.</span>
      ) : null}
    </div>
  );
}
