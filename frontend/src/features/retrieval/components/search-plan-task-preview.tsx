import {
  CheckCircle2,
  ChevronDown,
  Clipboard,
  ExternalLink,
  FileSearch,
} from "lucide-react";
import * as React from "react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { humanize } from "../../../lib/utils";
import type { RetrievalSearchTask } from "../../../types";
import {
  orderedSearchPlanTasks,
  retrievalTaskActionDescription,
  retrievalTaskActionLabel,
  retrievalTaskClipboardText,
  retrievalTaskExternalUrl,
} from "../model/search-plan-tasks";
import { SectionHelpText } from "./section-help-text";

export function SearchPlanTaskPreview({
  copyTextToClipboard,
  isSearchPending,
  onRunTask,
  tasks,
  useCopyFeedback,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  isSearchPending: boolean;
  onRunTask: (task: RetrievalSearchTask) => void;
  tasks: RetrievalSearchTask[];
  useCopyFeedback: () => {
    copiedKey: string | null;
    markCopied: (key: string) => void;
  };
}) {
  if (!tasks.length) {
    return (
      <div className="rounded-md border border-border bg-card p-3">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Execution tasks
        </div>
        <SectionHelpText>
          No executable task plan was returned. Run full search or refine the query to generate task-level routing.
        </SectionHelpText>
      </div>
    );
  }
  const localTasks = tasks.filter((task) => task.target === "local_corpus");
  const externalTasks = tasks.filter((task) => task.target === "external_medical_index");

  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
          Execution tasks
          <HelpTooltip label="Execution task help">
            Local corpus tasks run OJTFlow retrieval. Medical-index tasks open or copy external follow-up searches for manual review.
          </HelpTooltip>
        </span>
        <Badge variant="success">{formatCount(tasks.length, "task")}</Badge>
      </div>
      <SearchPlanTaskGroup
        badgeVariant="success"
        copyTextToClipboard={copyTextToClipboard}
        description="These tasks run against governed OJTFlow evidence and can refresh the ranked package."
        emptyText="No local OJTFlow search task was generated for this plan."
        isSearchPending={isSearchPending}
        label="Local OJTFlow searches"
        onRunTask={onRunTask}
        tasks={localTasks}
        useCopyFeedback={useCopyFeedback}
      />
      <SearchPlanTaskGroup
        badgeVariant="warning"
        copyTextToClipboard={copyTextToClipboard}
        description="These follow-ups open or copy external medical searches for manual review."
        emptyText="No external medical-index follow-up was generated for this plan."
        isSearchPending={isSearchPending}
        label="External follow-ups"
        onRunTask={onRunTask}
        tasks={externalTasks}
        useCopyFeedback={useCopyFeedback}
      />
    </div>
  );
}

function SearchPlanTaskGroup({
  badgeVariant,
  copyTextToClipboard,
  description,
  emptyText,
  isSearchPending,
  label,
  onRunTask,
  tasks,
  useCopyFeedback,
}: {
  badgeVariant: React.ComponentProps<typeof Badge>["variant"];
  copyTextToClipboard: (text: string) => Promise<void>;
  description: string;
  emptyText: string;
  isSearchPending: boolean;
  label: string;
  onRunTask: (task: RetrievalSearchTask) => void;
  tasks: RetrievalSearchTask[];
  useCopyFeedback: () => {
    copiedKey: string | null;
    markCopied: (key: string) => void;
  };
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const orderedTasks = orderedSearchPlanTasks(tasks);
  const visibleTasks = orderedTasks.slice(0, 4);
  const remainingTasks = orderedTasks.slice(4);
  const requiredTaskCount = tasks.filter((task) => task.required).length;
  const optionalTaskCount = tasks.length - requiredTaskCount;
  const copyKey = `task-group:${label}`;
  const copied = copiedKey === copyKey;
  const copyGroupQueries = async () => {
    await copyTextToClipboard(
      orderedTasks.map((task) => retrievalTaskClipboardText(task)).join("\n\n"),
    );
    markCopied(copyKey);
  };
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="break-words text-xs font-black uppercase text-muted-foreground">
            {label}
          </div>
          <div className="break-words text-xs text-muted-foreground">{description}</div>
        </div>
        <Badge variant={tasks.length ? badgeVariant : "muted"}>
          {formatCount(tasks.length, "task")}
        </Badge>
      </div>
      {tasks.length ? (
        <div className="grid gap-2">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge variant={requiredTaskCount ? "warning" : "muted"}>
                {formatCount(requiredTaskCount, "required task")}
              </Badge>
              <Badge variant={optionalTaskCount ? "muted" : "success"}>
                {formatCount(optionalTaskCount, "optional task")}
              </Badge>
              <span className="break-words text-xs font-semibold text-muted-foreground">
                {requiredTaskCount
                  ? "Prioritize required tasks before optional follow-ups."
                  : "No required task in this group."}
              </span>
            </div>
            <Button
              onClick={() => void copyGroupQueries()}
              size="sm"
              type="button"
              variant="outline"
            >
              {copied ? <CheckCircle2 className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
              {copied ? "Copied group" : "Copy group queries"}
            </Button>
          </div>
          {visibleTasks.map((task) => (
            <SearchPlanTaskRow
              copyTextToClipboard={copyTextToClipboard}
              isSearchPending={isSearchPending}
              key={task.task_id}
              onRunTask={onRunTask}
              task={task}
              useCopyFeedback={useCopyFeedback}
            />
          ))}
          {remainingTasks.length ? (
            <details className="group rounded-md border border-border bg-background">
              <summary
                aria-label={`Show remaining ${label.toLowerCase()}`}
                className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-2 px-2 py-1.5 text-xs font-black uppercase text-muted-foreground"
              >
                <span className="flex min-w-0 items-center gap-1.5">
                  <ChevronDown className="h-4 w-4 shrink-0 transition-transform group-open:rotate-180" />
                  <span className="break-words">Show remaining {label.toLowerCase()}</span>
                </span>
                <Badge variant="muted">{formatCount(remainingTasks.length, "task")}</Badge>
              </summary>
              <div className="grid gap-2 border-t border-border p-2">
                {remainingTasks.map((task) => (
                  <SearchPlanTaskRow
                    copyTextToClipboard={copyTextToClipboard}
                    isSearchPending={isSearchPending}
                    key={task.task_id}
                    onRunTask={onRunTask}
                    task={task}
                    useCopyFeedback={useCopyFeedback}
                  />
                ))}
              </div>
            </details>
          ) : null}
        </div>
      ) : (
        <SectionHelpText>{emptyText}</SectionHelpText>
      )}
    </div>
  );
}

function SearchPlanTaskRow({
  copyTextToClipboard,
  isSearchPending,
  onRunTask,
  task,
  useCopyFeedback,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  isSearchPending: boolean;
  onRunTask: (task: RetrievalSearchTask) => void;
  task: RetrievalSearchTask;
  useCopyFeedback: () => {
    copiedKey: string | null;
    markCopied: (key: string) => void;
  };
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const externalUrl = retrievalTaskExternalUrl(task);
  const copyKey = `task-query:${task.task_id}`;
  const copied = copiedKey === copyKey;
  const copyQuery = async () => {
    await copyTextToClipboard(task.query);
    markCopied(copyKey);
  };
  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-1.5 rounded-md border border-border bg-muted/20 p-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <Badge variant="muted">P{task.priority}</Badge>
        <Badge variant={task.target === "local_corpus" ? "success" : "warning"}>
          {task.target === "local_corpus" ? "local corpus" : "medical index"}
        </Badge>
        <Badge variant={task.required ? "warning" : "muted"}>
          {task.required ? "required" : "optional"}
        </Badge>
        <span className="break-words font-black">{task.label}</span>
      </div>
      <div className="break-words text-muted-foreground">{task.rationale}</div>
      <div className="grid gap-1 rounded-md border border-border bg-background px-2 py-1.5">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <span className="font-black uppercase text-muted-foreground">What happens</span>
          <Badge variant={task.action_type === "run_local_search" ? "success" : "muted"}>
            {retrievalTaskActionLabel(task)}
          </Badge>
        </div>
        <div className="break-words text-muted-foreground">
          {retrievalTaskActionDescription(task)}
        </div>
      </div>
      <code className="block max-w-full overflow-hidden break-words rounded bg-background px-2 py-1 font-mono">
        {task.query}
      </code>
      {Object.keys(task.suggested_filters).length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {Object.entries(task.suggested_filters).slice(0, 4).map(([field, value]) => (
            <Badge key={`${task.task_id}-${field}-${value}`} variant="muted">
              {humanize(field)}: {humanize(value)}
            </Badge>
          ))}
        </div>
      ) : null}
      <div className="flex min-w-0 flex-wrap justify-start gap-1.5 sm:justify-end">
        <Button
          onClick={() => void copyQuery()}
          size="sm"
          type="button"
          variant="outline"
        >
          {copied ? <CheckCircle2 className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
          {copied ? "Copied" : "Copy query"}
        </Button>
        {task.action_type === "run_local_search" ? (
          <Button
            disabled={isSearchPending}
            onClick={() => onRunTask(task)}
            size="sm"
            type="button"
            variant="outline"
          >
            <FileSearch className="h-4 w-4" />
            Run task
          </Button>
        ) : task.action_type === "open_external_url" && externalUrl ? (
          <Button asChild size="sm" type="button" variant="outline">
            <a href={externalUrl} rel="noopener noreferrer" target="_blank">
              <ExternalLink className="h-4 w-4" />
              Open follow-up
            </a>
          </Button>
        ) : (
          <Badge variant="muted">{task.action_type === "copy_query" ? "copy query" : "syntax only"}</Badge>
        )}
      </div>
    </div>
  );
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
