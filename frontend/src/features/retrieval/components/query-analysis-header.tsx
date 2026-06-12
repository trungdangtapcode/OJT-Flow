import { Badge } from "../../../components/ui/badge";
import { QueryAnalysisCounter } from "./query-analysis-counter";

export function QueryAnalysisHeader({
  conceptCount,
  ruleCount,
  standardCount,
  strategy,
  variantCount,
}: {
  conceptCount: number;
  ruleCount: number;
  standardCount: number;
  strategy: string;
  variantCount: number;
}) {
  return (
    <>
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Query analysis
        </div>
        <Badge variant="muted">{strategy}</Badge>
      </div>
      <div className="grid gap-2 text-xs sm:grid-cols-4">
        <QueryAnalysisCounter label="Concepts" value={conceptCount} />
        <QueryAnalysisCounter label="Standards" value={standardCount} />
        <QueryAnalysisCounter label="Rules" value={ruleCount} />
        <QueryAnalysisCounter label="Variants" value={variantCount} />
      </div>
    </>
  );
}
