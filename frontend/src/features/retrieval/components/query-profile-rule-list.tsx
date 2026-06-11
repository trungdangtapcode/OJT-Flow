export function QueryProfileRuleList({ ruleIds }: { ruleIds: string[] }) {
  if (!ruleIds.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap gap-1">
      {ruleIds.map((ruleId) => (
        <code
          className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px]"
          key={ruleId}
        >
          {ruleId}
        </code>
      ))}
    </div>
  );
}
