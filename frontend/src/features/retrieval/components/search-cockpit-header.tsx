import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalSearchCockpitView } from "../model/retrieval-cockpit-view-model";
import { SearchCockpitCopyAction } from "./search-cockpit-copy-action";
import { cockpitCountLabel } from "./search-cockpit-format";
import { SearchCockpitStatusBadges } from "./search-cockpit-status-badges";

export function SearchCockpitHeader({
  copyTextToClipboard,
  reportJson,
  view,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  reportJson: string;
  view: RetrievalSearchCockpitView;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Search cockpit
        </div>
        <div className="mt-1 break-words text-lg font-black leading-tight">
          {view.routeLabel}
        </div>
        <div className="mt-1 flex min-w-0 flex-wrap gap-1.5">
          <Badge variant="muted">{humanize(view.strategy)}</Badge>
          <Badge variant="muted">{cockpitCountLabel(view.candidateCount, "candidate")}</Badge>
          <Badge variant="muted">{cockpitCountLabel(view.hitCount, "hit")}</Badge>
          {view.bm25Enabled !== null ? (
            <Badge variant={view.bm25Enabled ? "success" : "muted"}>
              BM25 {view.bm25Enabled ? "on" : "off"}
            </Badge>
          ) : null}
          <Badge variant={view.rerankerEnabled ? "success" : "muted"}>
            rerank {view.rerankerEnabled ? "on" : "off"}
          </Badge>
          {view.activeFilters.map((filter) => (
            <Badge key={filter.field} variant="muted">
              {filter.label}: {filter.displayValue}
            </Badge>
          ))}
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
        <SearchCockpitCopyAction
          copyTextToClipboard={copyTextToClipboard}
          reportJson={reportJson}
        />
        <SearchCockpitStatusBadges view={view} />
      </div>
    </div>
  );
}
