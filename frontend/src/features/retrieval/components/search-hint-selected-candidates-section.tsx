import { Badge } from "../../../components/ui/badge";

export function SearchHintSelectedCandidatesSection({
  candidates,
  title,
}: {
  candidates: string[];
  title: string;
}) {
  if (!candidates.length) return null;
  return (
    <div className="grid gap-1.5">
      <div className="font-black uppercase text-muted-foreground">{title}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {candidates.slice(0, 8).map((candidate) => (
          <Badge key={candidate} variant="success">
            {candidate}
          </Badge>
        ))}
      </div>
    </div>
  );
}
