import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RunComparisonDiagnosisView } from "./run-comparison-summary-types";

export function RunComparisonDiagnosis({
  diagnosis,
  formatCount,
}: {
  diagnosis: RunComparisonDiagnosisView[];
  formatCount: (count: number, singular: string) => string;
}) {
  const warningCount = diagnosis.filter((item) => item.severity === "warning").length;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">
          Comparison diagnosis
        </span>
        <Badge variant={warningCount ? "warning" : "success"}>
          {warningCount ? formatCount(warningCount, "change driver") : "stable"}
        </Badge>
      </div>
      <div className="grid gap-1">
        {diagnosis.map((item) => (
          <div
            className="flex min-w-0 flex-wrap items-start gap-2"
            key={item.code}
          >
            <Badge variant={item.severity}>{humanize(item.code)}</Badge>
            <span className="min-w-0 flex-1 break-words text-muted-foreground">
              {item.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
