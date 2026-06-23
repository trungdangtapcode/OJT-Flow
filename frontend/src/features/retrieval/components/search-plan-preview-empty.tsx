import { BrainCircuit } from "lucide-react";

import { Notice } from "../../../components/ui/notice";

export function SearchPlanPreviewEmpty({
  planError,
}: {
  planError: string | null;
}) {
  if (planError) {
    return (
      <Notice title="Plan error" tone="danger">
        {planError}
      </Notice>
    );
  }

  return (
    <div className="flex items-center gap-2 rounded-lg border border-dashed border-border/60 px-4 py-6 text-sm text-muted-foreground">
      <BrainCircuit className="h-4 w-4" />
      Search plan appears after running a query
    </div>
  );
}
