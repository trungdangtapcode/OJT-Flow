import * as React from "react";
import { Link } from "@tanstack/react-router";
import { BookOpen, HelpCircle } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";

export function AssistantInlineGuide() {
  return (
    <details className="rounded-lg border border-border/60 bg-muted/25 px-4 py-3">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2 text-sm font-black">
        <HelpCircle className="h-4 w-4 text-primary" />
        How to use Assistant
        <Badge variant="muted">guide</Badge>
      </summary>
      <div className="mt-3 grid gap-3 text-sm leading-6 md:grid-cols-3">
        <InlineGuideItem title="1. Ask normally">
          Example: validate this CSV, explain PHI risks, find trusted evidence, or list pending reviews.
        </InlineGuideItem>
        <InlineGuideItem title="2. Attach data when needed">
          Use CSV, JSON, YAML, PDF, DOCX, or image files. Extraction warnings mean the file may need review.
        </InlineGuideItem>
        <InlineGuideItem title="3. Read the timeline">
          LLM text is the explanation. Tool calls are real backend actions. Expand tools only when you need details.
        </InlineGuideItem>
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

function InlineGuideItem({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="rounded-lg border border-border/60 bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <div className="mt-1 text-muted-foreground">{children}</div>
    </div>
  );
}
