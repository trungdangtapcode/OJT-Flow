import { Badge } from "../../../components/ui/badge";
import { SectionHelpText } from "./section-help-text";
import { formatSearchPlanDetailCount } from "./search-plan-detail-format";
import type { QueryAspectStack } from "./search-plan-detail-types";

export function SearchPlanAspectPreview({ aspects }: { aspects: QueryAspectStack[] }) {
  if (!aspects.length) {
    return (
      <div className="rounded-md border border-border bg-card p-3">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Search aspects
        </div>
        <SectionHelpText>
          No decomposed medical search aspects matched. Add fields, standards, or a more specific operation to improve planning.
        </SectionHelpText>
      </div>
    );
  }

  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Search aspects
        </span>
        <Badge variant="muted">
          {formatSearchPlanDetailCount(aspects.length, "aspect")}
        </Badge>
      </div>
      {aspects.slice(0, 4).map((aspect) => (
        <div className="grid gap-1 text-xs" key={aspect.aspectId}>
          <div className="flex min-w-0 flex-wrap items-center gap-1.5">
            <Badge variant="muted">P{aspect.priority}</Badge>
            <span className="break-words font-black">{aspect.label}</span>
          </div>
          <div className="break-words text-muted-foreground">{aspect.question}</div>
        </div>
      ))}
    </div>
  );
}
