import { CheckCircle2, Clipboard, FileSearch } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { humanize } from "../../../lib/utils";
import type {
  RetrievalPlanRiskSignal,
  RetrievalPlanTaskSummary,
  RetrievalSearchTask,
} from "../../../types";
import { retrievalTaskClipboardText } from "../model/search-plan-tasks";
import { SectionHelpText } from "./section-help-text";

export type SearchPlanCoverageSummaryView = {
  externalTaskCount: number;
  filterCount: number;
  localTaskCount: number;
  ready: boolean;
  requiredLocalTaskCount: number;
  standards: string[];
  nextAction: string;
  summary: string;
  warnings: string[];
};

export function SearchPlanCoverageSummaryPanel({
  summary,
}: {
  summary: SearchPlanCoverageSummaryView;
}) {
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Plan coverage
        </span>
        <Badge variant={summary.ready ? "success" : "warning"}>
          {summary.ready ? "coverage planned" : "needs detail"}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <MetricMiniCard
          label="Required local tasks"
          supporting="Trusted corpus coverage"
          value={`${summary.requiredLocalTaskCount}/${summary.localTaskCount}`}
        />
        <MetricMiniCard
          label="External follow-ups"
          supporting="Medical index checks"
          value={summary.externalTaskCount}
        />
        <MetricMiniCard
          label="Standards"
          supporting={summary.standards.slice(0, 3).join(", ") || "No standard inferred"}
          value={summary.standards.length}
        />
        <MetricMiniCard
          label="Filters"
          supporting="Suggested scope controls"
          value={summary.filterCount}
        />
      </div>
      <div className="rounded-md border border-border bg-muted/20 px-2 py-1.5 text-xs">
        <div className="font-black uppercase text-muted-foreground">Next action</div>
        <div className="mt-1 break-words font-semibold">{summary.nextAction}</div>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {summary.standards.slice(0, 6).map((standard) => (
          <Badge key={standard} variant="muted">
            {standard}
          </Badge>
        ))}
        {summary.warnings.slice(0, 3).map((warning) => (
          <Badge key={warning} variant="warning">
            {warning}
          </Badge>
        ))}
      </div>
      <SectionHelpText>{summary.summary}</SectionHelpText>
      {!summary.ready ? (
        <SectionHelpText>
          Add a more specific standard, data field, resource type, or clinical domain before relying on this search for review.
        </SectionHelpText>
      ) : null}
    </div>
  );
}

export function SearchPlanTaskSummaryPanel({
  copyTextToClipboard,
  isSearchPending,
  onRunTask,
  summary,
  tasks,
  useCopyFeedback,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  isSearchPending: boolean;
  onRunTask: (task: RetrievalSearchTask) => void;
  summary: RetrievalPlanTaskSummary;
  tasks: RetrievalSearchTask[];
  useCopyFeedback: () => {
    copiedKey: string | null;
    markCopied: (key: string) => void;
  };
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const firstRequiredTask =
    tasks.find(
      (task) =>
        task.target === "local_corpus" &&
        task.action_type === "run_local_search" &&
        task.required,
    ) ??
    tasks.find(
      (task) => task.target === "local_corpus" && task.action_type === "run_local_search",
    ) ??
    null;
  const externalTasks = tasks.filter((task) => task.target === "external_medical_index");
  const copyExternalQueries = async () => {
    await copyTextToClipboard(
      externalTasks.map((task) => retrievalTaskClipboardText(task)).join("\n\n"),
    );
    markCopied("plan-external-followups");
  };
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Execution summary
        </span>
        <Badge variant={summary.required_runnable_local_count ? "success" : "warning"}>
          {summary.required_runnable_local_count
            ? "ready to run"
            : summary.manual_followup_count
              ? "manual follow-up"
              : "needs query detail"}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        <MetricMiniCard
          label="Runnable local"
          supporting="Can execute inside OJTFlow"
          value={summary.runnable_local_count}
        />
        <MetricMiniCard
          label="Required local"
          supporting="Recommended first actions"
          value={summary.required_runnable_local_count}
        />
        <MetricMiniCard
          label="Manual follow-ups"
          supporting="External medical indexes"
          value={summary.manual_followup_count}
        />
      </div>
      <div className="rounded-md border border-border bg-muted/20 px-2 py-1.5 text-xs">
        <div className="font-black uppercase text-muted-foreground">Primary action</div>
        <div className="mt-1 break-words font-semibold">{summary.primary_action}</div>
      </div>
      <div className="grid gap-1.5 rounded-md border border-border bg-background px-2 py-1.5 text-xs">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <span className="font-black uppercase text-muted-foreground">Run order</span>
          <HelpTooltip label="Retrieval task order help">
            Start with required local OJTFlow searches because those can produce audited evidence. External medical-index tasks are follow-up links or copied queries for manual source review.
          </HelpTooltip>
        </div>
        <ol className="grid gap-1 pl-4 text-muted-foreground">
          <li className="list-decimal break-words">
            Run required local corpus tasks to collect trusted evidence inside OJTFlow.
          </li>
          <li className="list-decimal break-words">
            Apply supported filters if the plan suggests a narrower source, standard, or trust scope.
          </li>
          <li className="list-decimal break-words">
            Review external medical-index follow-ups only as manual context; they are not imported evidence until indexed.
          </li>
        </ol>
      </div>
      <div className="flex min-w-0 flex-wrap gap-2">
        {firstRequiredTask ? (
          <Button
            disabled={isSearchPending}
            onClick={() => onRunTask(firstRequiredTask)}
            size="sm"
            type="button"
            variant="outline"
          >
            <FileSearch className="h-4 w-4" />
            Run first local task
          </Button>
        ) : null}
        {externalTasks.length ? (
          <Button
            onClick={() => void copyExternalQueries()}
            size="sm"
            type="button"
            variant="outline"
          >
            {copiedKey === "plan-external-followups" ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}
            {copiedKey === "plan-external-followups"
              ? "Copied follow-ups"
              : "Copy external follow-ups"}
          </Button>
        ) : null}
      </div>
      <SectionHelpText>{summary.summary}</SectionHelpText>
    </div>
  );
}

export function SearchPlanRiskSignalsPanel({
  signals,
}: {
  signals: RetrievalPlanRiskSignal[];
}) {
  if (!signals.length) return null;
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Plan risks
        </span>
        <Badge variant={riskSignalListBadgeVariant(signals)}>
          {formatCount(signals.length, "signal")}
        </Badge>
      </div>
      <div className="grid gap-2">
        {signals.slice(0, 4).map((signal) => (
          <div className="grid gap-1 rounded-md border border-border bg-muted/20 p-2 text-xs" key={signal.code}>
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge variant={diagnosticBadgeVariant(signal.severity)}>
                {humanize(signal.severity)}
              </Badge>
              <Badge variant="muted">{humanize(signal.source)}</Badge>
              <span className="break-words font-black">{humanize(signal.code)}</span>
            </div>
            <div className="break-words text-muted-foreground">{signal.message}</div>
            <div className="break-words font-semibold">{signal.suggested_action}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MetricMiniCard({
  label,
  supporting,
  value,
}: {
  label: string;
  supporting: string;
  value: number | string;
}) {
  return (
    <div className="min-w-0 rounded-md border border-border bg-muted/20 p-2">
      <div className="truncate text-[0.68rem] font-black uppercase text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 break-words text-lg font-black">{value}</div>
      <div className="mt-1 line-clamp-2 break-words text-xs text-muted-foreground">
        {supporting}
      </div>
    </div>
  );
}

function diagnosticBadgeVariant(
  severity: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (severity === "warning") return "warning";
  if (severity === "error") return "destructive";
  if (severity === "info") return "muted";
  return "default";
}

function riskSignalListBadgeVariant(
  signals: RetrievalPlanRiskSignal[],
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (signals.some((signal) => ["destructive", "error"].includes(signal.severity))) {
    return "destructive";
  }
  if (signals.some((signal) => signal.severity === "warning")) return "warning";
  return "muted";
}

function formatCount(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}
