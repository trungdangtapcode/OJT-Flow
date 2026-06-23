import * as React from "react";
import { Link } from "@tanstack/react-router";
import { BookOpen, HelpCircle } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";

export function RetrievalInlineGuide() {
  return (
    <details className="rounded-xl border border-border/50 bg-muted/20 px-5 py-4">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2.5 text-sm font-semibold">
        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary/10">
          <HelpCircle className="h-3.5 w-3.5 text-primary" />
        </div>
        How to read Retrieval
        <Badge variant="muted">guide</Badge>
      </summary>
      <div className="mt-4 grid gap-3 text-sm leading-6 md:grid-cols-4">
        <RetrievalGuideItem title="1. Search">
          Build your query, review the search plan, and inspect ranked evidence results.
        </RetrievalGuideItem>
        <RetrievalGuideItem title="2. Analysis">
          Deep-dive into trace details, graph handoff entities, and graph neighborhood queries.
        </RetrievalGuideItem>
        <RetrievalGuideItem title="3. Sources">
          Manage source inventory, check freshness gates, and verify integrity checksums.
        </RetrievalGuideItem>
        <RetrievalGuideItem title="4. History">
          Compare search runs, track regression metrics, and review active-learning candidates.
        </RetrievalGuideItem>
      </div>
      <div className="mt-4">
        <Button asChild size="sm" type="button" variant="outline">
          <Link to="/help">
            <BookOpen className="h-4 w-4" />
            Open full manual
          </Link>
        </Button>
      </div>
    </details>
  );
}

function RetrievalGuideItem({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="rounded-xl border border-border/50 bg-card px-4 py-3">
      <div className="font-semibold">{title}</div>
      <div className="mt-1.5 text-muted-foreground">{children}</div>
    </div>
  );
}
