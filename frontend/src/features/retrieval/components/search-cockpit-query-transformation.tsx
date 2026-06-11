import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalSearchCockpitView } from "../model/retrieval-cockpit-view-model";
import { cockpitCountLabel } from "./search-cockpit-format";

export function SearchCockpitQueryTransformation({
  view,
}: {
  view: RetrievalSearchCockpitView;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Query transformation
        </div>
        <Badge variant="muted">{cockpitCountLabel(view.variantCount, "variant")}</Badge>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {view.standards.slice(0, 8).map((standard) => (
          <Badge key={standard} variant="success">
            {standard}
          </Badge>
        ))}
        {view.detectedConcepts.slice(0, 8).map((concept) => (
          <Badge key={concept} variant="muted">
            {humanize(concept)}
          </Badge>
        ))}
        {view.expandedTerms.slice(0, 10).map((term) => (
          <span
            className="max-w-full break-words rounded-full border border-border bg-muted px-2.5 py-1 text-xs font-bold text-muted-foreground"
            key={term}
          >
            {term}
          </span>
        ))}
      </div>
      {view.queryAspects.length ? (
        <div className="grid gap-1.5">
          {view.queryAspects.slice(0, 3).map((aspect) => (
            <div
              className="grid gap-1 rounded-md border border-border bg-muted/25 px-3 py-2 text-xs"
              key={aspect.aspectId}
            >
              <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                <Badge variant="muted">P{aspect.priority}</Badge>
                <span className="break-words font-black">{aspect.label}</span>
              </div>
              <div className="break-words text-muted-foreground">
                {aspect.question}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
