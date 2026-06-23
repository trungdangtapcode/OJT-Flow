import { FileSearch } from "lucide-react";

export function RetrievalFirstRunGuide() {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-dashed border-border/60 px-4 py-3 text-sm text-muted-foreground">
      <FileSearch className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
      <div className="min-w-0">
        <span className="font-semibold text-foreground">Try a question</span>
        {" — "}
        <span className="italic">&quot;validate lab CSV fields&quot;</span>,{" "}
        <span className="italic">&quot;FHIR Observation mapping&quot;</span>, or{" "}
        <span className="italic">&quot;which fields are PHI?&quot;</span>
      </div>
    </div>
  );
}
