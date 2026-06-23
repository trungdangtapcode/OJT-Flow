import { Badge } from "../../../components/ui/badge";
import type { EvidenceInterpretationCard as EvidenceInterpretationCardView } from "../model/evidence-interpretation";

export function EvidenceInterpretationCard({
  card,
}: {
  card: EvidenceInterpretationCardView;
}) {
  return (
    <div className="grid min-w-0 gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
      <div className="text-xs font-black uppercase text-muted-foreground">
        {card.label}
      </div>
      <div className="break-words text-sm font-black">{card.title}</div>
      <p className="break-words text-sm leading-6 text-muted-foreground">
        {card.detail}
      </p>
      {card.items.length ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {card.items.map((item) => (
            <Badge
              className="max-w-full whitespace-normal break-words leading-4"
              key={item}
              variant="muted"
            >
              {item}
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}
