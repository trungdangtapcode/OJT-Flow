import { ShieldCheck } from "lucide-react";

export function StandardSearchGovernanceNotes({ notes }: { notes: string[] }) {
  const visibleNotes = notes.slice(0, 2);
  if (!visibleNotes.length) {
    return null;
  }
  return (
    <div className="grid gap-1 text-xs leading-5 text-muted-foreground">
      {visibleNotes.map((note) => (
        <div className="grid grid-cols-[14px_minmax(0,1fr)] gap-2" key={note}>
          <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-700" />
          <span className="min-w-0 break-words">{note}</span>
        </div>
      ))}
    </div>
  );
}

export function StandardSearchPlanGuardrails({ notes }: { notes: string[] }) {
  const visibleNotes = notes.slice(0, 3);
  if (!visibleNotes.length) {
    return null;
  }
  return (
    <div className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-950">
      <div className="font-black uppercase">Governance guardrails</div>
      <ul className="grid gap-1">
        {visibleNotes.map((note) => (
          <li className="grid grid-cols-[12px_minmax(0,1fr)] gap-2" key={note}>
            <span aria-hidden="true" className="pt-0.5 font-black">
              -
            </span>
            <span className="min-w-0 break-words">{note}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
