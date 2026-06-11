import { Badge } from "../../../components/ui/badge";
import type { TriageTone } from "./ranked-evidence-triage-types";

export function RankedEvidenceTriageFact({
  label,
  tone = "muted",
  value,
}: {
  label: string;
  tone?: TriageTone;
  value: string;
}) {
  return (
    <div className="flex min-w-0 items-center justify-between gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-xs">
      <span className="font-bold uppercase text-muted-foreground">{label}</span>
      <Badge variant={tone}>{value}</Badge>
    </div>
  );
}
