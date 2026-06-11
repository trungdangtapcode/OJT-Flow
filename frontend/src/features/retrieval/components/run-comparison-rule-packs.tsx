import { Badge } from "../../../components/ui/badge";
import type { RetrievalRulePackChangeView } from "./run-comparison-detail-types";

export function RunComparisonRulePacks({
  formatCount,
  rulePackChanges,
}: {
  formatCount: (count: number, singular: string) => string;
  rulePackChanges: RetrievalRulePackChangeView[];
}) {
  const changedCount = rulePackChanges.filter((change) => change.status !== "stable").length;
  if (!rulePackChanges.length) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Rule packs</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-bold text-muted-foreground">Rule packs</span>
        <Badge variant={changedCount ? "warning" : "success"}>
          {changedCount ? formatCount(changedCount, "changed pack") : "stable"}
        </Badge>
      </div>
      <div className="grid gap-1">
        {rulePackChanges.slice(0, 4).map((change) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2 text-xs"
            key={change.name}
          >
            <span className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{change.name}</span>
              <Badge variant={change.status === "stable" ? "success" : "warning"}>
                {change.status}
              </Badge>
            </span>
            <span className="break-words text-muted-foreground">
              {change.baselineFingerprint} to {change.activeFingerprint}
            </span>
          </div>
        ))}
        {rulePackChanges.length > 4 ? (
          <div className="text-xs font-semibold text-muted-foreground">
            +{formatCount(rulePackChanges.length - 4, "more rule pack")}
          </div>
        ) : null}
      </div>
    </div>
  );
}
