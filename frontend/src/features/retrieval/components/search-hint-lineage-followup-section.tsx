import type { SearchHintLineageFollowup } from "./search-hint-metadata";

export function SearchHintLineageFollowupSection({
  items,
}: {
  items: SearchHintLineageFollowup[];
}) {
  if (!items.length) return null;
  return (
    <div className="grid gap-1.5">
      <div className="font-black uppercase text-muted-foreground">Lineage follow-up</div>
      {items.map((item) => (
        <div
          className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-1.5 text-amber-950"
          key={item.parameter}
        >
          <code className="break-words font-mono text-[11px]">{item.parameter}</code>
          <div className="break-words text-[11px] leading-5">{item.purpose}</div>
        </div>
      ))}
    </div>
  );
}
