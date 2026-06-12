import { Badge } from "../../../components/ui/badge";
import { SectionHelpText } from "./section-help-text";

export function CoverageDiagnosticsHeader({ warningCount }: { warningCount: number }) {
  return (
    <>
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Coverage diagnostics
        </div>
        <Badge variant={warningCount ? "warning" : "success"}>
          {warningCount ? `${warningCount} gap` : "covered"}
        </Badge>
      </div>
      <SectionHelpText>
        Coverage diagnostics show missing standards or query aspects and offer backend-supported filters when available.
      </SectionHelpText>
    </>
  );
}
