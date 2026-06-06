import * as React from "react";
import { CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { RetrievalPackage, RetrievalSearchPayload } from "../../../types";
import {
  buildSearchAnswerViewModel,
  type SearchAnswerMetric,
} from "../model/search-answer";

export function SearchAnswerCard({
  packageData,
  submittedSearchPayload,
}: {
  packageData: RetrievalPackage;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  const [copied, setCopied] = React.useState(false);
  const answer = buildSearchAnswerViewModel(packageData, submittedSearchPayload);

  const copyReport = async () => {
    await navigator.clipboard.writeText(JSON.stringify(answer.report, null, 2));
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  };

  return (
    <section
      aria-label="Search answer"
      className="grid gap-3 rounded-md border border-primary/25 bg-primary/5 p-3"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Search answer
            </div>
            <Badge variant={answer.status.variant}>{answer.status.label}</Badge>
            {answer.qualityScore !== null ? (
              <Badge variant={answer.status.variant}>
                readiness {answer.qualityScore}/100
              </Badge>
            ) : null}
            <Badge variant="muted">{formatCount(packageData.hits.length, "hit")}</Badge>
          </div>
          <div className="mt-2 max-w-4xl break-words text-base font-black leading-7">
            {answer.remediation}
          </div>
          <p className="mt-1 max-w-4xl text-sm leading-6 text-muted-foreground">
            This is an evidence retrieval summary for workflow operations. It explains source
            support and search quality; it is not clinical advice.
          </p>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Button
            aria-label="Copy retrieval answer report"
            onClick={() => void copyReport()}
            size="sm"
            type="button"
            variant="outline"
          >
            {copied ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}
            {copied ? "Copied" : "Copy answer JSON"}
          </Button>
          <HelpTooltip label="Answer JSON report help">
            Copies the plain-language retrieval answer, readiness, warnings, top evidence, missing required buckets, and recommended backend actions.
          </HelpTooltip>
        </div>
      </div>

      <div className="grid gap-2 md:grid-cols-3">
        {answer.metrics.map((metric) => (
          <SearchAnswerMetricCard key={metric.label} metric={metric} />
        ))}
      </div>

      {answer.warnings.length ? (
        <div className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5">
          <div className="font-black uppercase text-amber-800">
            Coverage warnings
          </div>
          {answer.warnings.slice(0, 3).map((warning) => (
            <div className="break-words text-amber-900" key={warning}>
              {warning}
            </div>
          ))}
          {answer.warnings.length > 3 ? (
            <div className="font-semibold text-amber-900">
              {formatCount(answer.warnings.length - 3, "additional warning")} hidden in detailed panels.
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function SearchAnswerMetricCard({ metric }: { metric: SearchAnswerMetric }) {
  return (
    <div className="min-w-0 rounded-md border border-border bg-card px-3 py-2">
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

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
