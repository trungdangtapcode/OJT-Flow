import { Badge } from "../../../components/ui/badge";
import { cn } from "../../../lib/utils";

type MetricTone = "default" | "success" | "warning" | "destructive" | "muted";

export function IntegrityMetric({
  label,
  tone = "muted",
  value,
}: {
  label: string;
  tone?: MetricTone;
  value: number | string;
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-muted/20 p-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 min-w-0">
        {typeof value === "string" ? (
          <Badge variant={tone}>{value}</Badge>
        ) : (
          <span className={cn("text-lg font-black tabular-nums", metricToneClass(tone))}>
            {value}
          </span>
        )}
      </div>
    </div>
  );
}

export function IntegrityFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg border border-border/60 bg-card p-2">
      <div className="font-bold text-muted-foreground">{label}</div>
      <div className="break-all font-mono font-semibold">{value}</div>
    </div>
  );
}

export function SourceReadinessMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/80 px-3 py-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 break-words text-sm font-black">{value}</div>
    </div>
  );
}

function metricToneClass(tone: MetricTone) {
  if (tone === "success") return "text-emerald-800";
  if (tone === "warning") return "text-amber-800";
  if (tone === "destructive") return "text-red-800";
  return "text-foreground";
}
