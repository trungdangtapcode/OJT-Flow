import { Bot, FileSearch } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import {
  CardHeader,
} from "../../../components/ui/card";
import type { RetrievalPackage } from "../../../types";
import { formatCount } from "../model/retrieval-format";
import {
  diversityFromPackage,
  formatSourceCoverage,
  rankingStackFromPackage,
} from "../model/retrieval-runtime-stack";
import {
  RuntimeDiversityBadge,
  RuntimeRerankBadge,
} from "./retrieval-runtime-status";

export function EmptySearchResults() {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-dashed border-border/60 px-4 py-8 text-sm text-muted-foreground">
      <FileSearch className="h-4 w-4" />
      Enter a query to search evidence
    </div>
  );
}

export function SearchResultsHeader({
  assistantHref,
  isStale,
  packageData,
}: {
  assistantHref: string | null;
  isStale: boolean;
  packageData: RetrievalPackage;
}) {
  const diversity = diversityFromPackage(packageData);
  const ranking = rankingStackFromPackage(packageData);
  return (
    <CardHeader className="flex-row flex-wrap items-center justify-between gap-2 border-b border-border/40 bg-muted/20 py-3">
      <div className="flex items-center gap-2 text-sm font-semibold">
        {formatCount(packageData.hits.length, "hit")}
        <span className="text-xs font-normal text-muted-foreground">
          / {formatCount(packageData.trace.candidates_seen, "candidate")}
        </span>
      </div>
      <div className="flex min-w-0 flex-wrap items-center justify-end gap-1.5">
        {assistantHref ? (
          <Button asChild size="sm" variant="ghost">
            <a href={assistantHref}>
              <Bot className="h-3.5 w-3.5" />
              Ask AI
            </a>
          </Button>
        ) : null}
        {isStale ? <Badge variant="warning">stale</Badge> : null}
        <Badge variant="muted">{packageData.trace.strategy}</Badge>
        <RuntimeDiversityBadge
          enabled={diversity.enabled}
          sourceCoverageLabel={formatSourceCoverage(diversity)}
        />
        <RuntimeRerankBadge enabled={ranking.reranker.enabled} />
      </div>
    </CardHeader>
  );
}
