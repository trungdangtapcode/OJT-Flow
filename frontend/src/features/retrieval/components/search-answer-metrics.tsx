import type { SearchAnswerMetric } from "../model/search-answer";

export function SearchAnswerMetrics({ metrics }: { metrics: SearchAnswerMetric[] }) {
  return (
    <div className="grid gap-2 md:grid-cols-3">
      {metrics.map((metric) => (
        <SearchAnswerMetricCard key={metric.label} metric={metric} />
      ))}
    </div>
  );
}

function SearchAnswerMetricCard({ metric }: { metric: SearchAnswerMetric }) {
  return (
    <div className="min-w-0 rounded-lg border border-border/60 bg-card px-3 py-2">
      <div className="text-xs font-black uppercase text-muted-foreground">
        {metric.label}
      </div>
      <div className="mt-1 break-words text-sm font-black">{metric.value}</div>
      <div className="mt-1 break-words text-xs leading-5 text-muted-foreground">
        {metric.detail}
      </div>
    </div>
  );
}
