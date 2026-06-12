import * as React from "react";
import { Link } from "@tanstack/react-router";
import { BookOpen, HelpCircle } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";

export function RetrievalInlineGuide() {
  return (
    <details className="rounded-md border border-border bg-muted/25 px-4 py-3">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2 text-sm font-black">
        <HelpCircle className="h-4 w-4 text-primary" />
        How to read Retrieval
        <Badge variant="muted">guide</Badge>
      </summary>
      <div className="mt-3 grid gap-3 text-sm leading-6 md:grid-cols-4">
        <RetrievalGuideItem title="1. Search cockpit">
          Shows the route, provider state, filters, and next best action for the current search.
        </RetrievalGuideItem>
        <RetrievalGuideItem title="2. Evidence readiness">
          Explains whether required support classes are present before trusting the package.
        </RetrievalGuideItem>
        <RetrievalGuideItem title="3. Strategy recommendations">
          Explains why hybrid search, reranking, corrective filters, or more evidence may be needed.
        </RetrievalGuideItem>
        <RetrievalGuideItem title="4. Ranked evidence">
          Inspect sources and match explanations. Evidence supports operations; it is not clinical advice.
        </RetrievalGuideItem>
      </div>
      <div className="mt-3">
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
    <div className="rounded-md border border-border bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <div className="mt-1 text-muted-foreground">{children}</div>
    </div>
  );
}
