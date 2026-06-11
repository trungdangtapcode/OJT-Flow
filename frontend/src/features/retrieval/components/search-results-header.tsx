import { Bot } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import type { RetrievalPackage } from "../../../types";
import { formatCount } from "../model/retrieval-format";
import {
  diversityFromPackage,
  formatSourceCoverage,
  rankingStackFromPackage,
} from "../model/retrieval-runtime-stack";
import { RetrievalFirstRunGuide } from "./first-run-guide";
import {
  RuntimeDiversityBadge,
  RuntimeRerankBadge,
} from "./retrieval-runtime-status";

export function EmptySearchResults() {
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle>Ranked evidence</CardTitle>
        <CardDescription>Run a search to inspect score components and provenance.</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <RetrievalFirstRunGuide />
      </CardContent>
    </Card>
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
    <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70">
      <div>
        <CardTitle>Ranked evidence</CardTitle>
        <CardDescription>
          {formatCount(packageData.hits.length, "hit")} from{" "}
          {formatCount(packageData.trace.candidates_seen, "candidate")}.{" "}
          The retrieval stack combines lexical search, vector search, and optional
          reranking. How many independent sources survived source-diversity selection
          is shown in the diversity badges. Concepts and query aspects detected from the search are listed in query analysis.
        </CardDescription>
      </div>
      <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
        {assistantHref ? (
          <Button asChild size="sm" variant="outline">
            <a href={assistantHref}>
              <Bot className="h-4 w-4" />
              Ask Assistant
            </a>
          </Button>
        ) : null}
        {isStale ? <Badge variant="warning">pending changes</Badge> : null}
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
