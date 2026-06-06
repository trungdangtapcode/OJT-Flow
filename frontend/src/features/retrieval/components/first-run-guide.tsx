import { FileSearch } from "lucide-react";

import { Badge } from "../../../components/ui/badge";

export function RetrievalFirstRunGuide() {
  return (
    <div className="grid gap-3 rounded-md border border-border bg-muted/20 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-sm font-black">
            <FileSearch className="h-4 w-4 text-primary" />
            Start with a concrete healthcare data question
          </div>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">
            Retrieval finds trusted schema, terminology, policy, and corpus evidence. It is best for explaining data operations, validation findings, and workflow grounding.
          </p>
        </div>
        <Badge variant="muted">first search guide</Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-3">
        <FirstRunGuideCard
          title="1. Pick a preset"
          text="Use presets for common lab, FHIR-like, PHI, and standards questions. They fill the builder safely."
        />
        <FirstRunGuideCard
          title="2. Add context"
          text="Fields, schema, format, and source filters narrow evidence. Leave them blank when you need broad discovery."
        />
        <FirstRunGuideCard
          title="3. Read readiness first"
          text="After search, check readiness, strategy recommendations, and evidence buckets before individual hits."
        />
      </div>
      <div className="grid gap-2 rounded-md border border-border bg-card p-3 text-sm">
        <div className="font-black">Good starter questions</div>
        <ul className="grid gap-1 text-muted-foreground">
          <li>Validate lab CSV fields and explain missing unit issues.</li>
          <li>Find trusted evidence for FHIR Observation mapping.</li>
          <li>Which fields are sensitive patient information in this dataset?</li>
        </ul>
      </div>
    </div>
  );
}

function FirstRunGuideCard({ text, title }: { text: string; title: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <p className="mt-1 text-sm leading-6 text-muted-foreground">{text}</p>
    </div>
  );
}
