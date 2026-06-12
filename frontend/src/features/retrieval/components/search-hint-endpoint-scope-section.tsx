export function SearchHintEndpointScopeSection({
  endpoints,
}: {
  endpoints: string[];
}) {
  if (!endpoints.length) return null;
  return (
    <div className="grid gap-1.5">
      <div className="font-black uppercase text-muted-foreground">Endpoint scope</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {endpoints.slice(0, 6).map((endpoint) => (
          <code
            className="rounded border border-border bg-card px-1.5 py-0.5 font-mono text-[11px]"
            key={endpoint}
          >
            {endpoint}
          </code>
        ))}
      </div>
    </div>
  );
}
