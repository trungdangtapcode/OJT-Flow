import { ListFilter } from "lucide-react";

import {
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { HelpTooltip } from "../../../components/ui/help-tooltip";

export function RetrievalTraceHeader() {
  return (
    <CardHeader className="border-b border-border bg-card/70">
      <CardTitle className="flex items-center gap-2">
        <ListFilter className="h-5 w-5 text-primary" />
        Retrieval trace
        <HelpTooltip label="Retrieval trace help">
          Trace shows how the backend transformed the query, which filters were applied, and which quality or safety issues affected the evidence package.
        </HelpTooltip>
      </CardTitle>
      <CardDescription>Query route, rewrites, filters, warnings, and quality diagnostics.</CardDescription>
    </CardHeader>
  );
}
