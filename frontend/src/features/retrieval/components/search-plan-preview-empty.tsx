import { BrainCircuit } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { Notice } from "../../../components/ui/notice";

export function SearchPlanPreviewEmpty({
  planError,
}: {
  planError: string | null;
}) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5 text-primary" />
          Search plan
          <HelpTooltip label="Search plan help">
            After a search, this shows the backend route, generated query aspects, external medical search hints, and filter suggestions before you inspect ranked evidence.
          </HelpTooltip>
        </CardTitle>
        <CardDescription>Run a search to see how retrieval will be routed.</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        {planError ? (
          <Notice title="Search plan unavailable" tone="danger">
            {planError}
          </Notice>
        ) : null}
        <Notice title="No search plan yet">
          Enter a query to preview the route, standards, and medical search follow-ups before running full evidence search.
        </Notice>
      </CardContent>
    </Card>
  );
}
