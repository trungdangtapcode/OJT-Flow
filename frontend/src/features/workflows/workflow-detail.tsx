import { Bot, FileSearch } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { StatusBadge } from "../../components/domain/workflow-badges";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { useHashTargetScroll } from "../../lib/use-hash-target-scroll";
import {
  useReviewDecisionMutation,
  useWorkflowEventsQuery,
  useWorkflowQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import { cn, formatCompactDate } from "../../lib/utils";
import {
  WorkflowDetailSkeleton,
  WorkflowFactStrip,
  WorkflowFailureNotice,
} from "./workflow-detail-chrome";
import { ReviewTab } from "./workflow-detail-review";
import {
  Audit,
  Evidence,
  Issues,
  Output,
  Overview,
} from "./workflow-detail-sections";
import { buildAssistantWorkflowContextHref } from "../assistant/assistant-attachments";

export function WorkflowDetail({
  focused = false,
  workflowId,
}: {
  focused?: boolean;
  workflowId: string | null;
}) {
  const workflowQuery = useWorkflowQuery(workflowId);
  const eventsQuery = useWorkflowEventsQuery(workflowId);
  const reviewMutation = useReviewDecisionMutation(workflowId);
  useHashTargetScroll([
    workflowId,
    workflowQuery.data?.updated_at ?? "",
    eventsQuery.data?.length ?? 0,
  ]);

  if (!workflowId) {
    return (
      <Card className="flex min-h-[320px] items-center justify-center">
        <CardContent className="grid place-items-center gap-3 text-center text-muted-foreground">
          <FileSearch className="h-8 w-8" />
          Select a workflow to inspect state, evidence, review, and output.
        </CardContent>
      </Card>
    );
  }

  if (workflowQuery.isLoading) {
    return <WorkflowDetailSkeleton focused={focused} />;
  }

  if (workflowQuery.isError || !workflowQuery.data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Workflow unavailable</CardTitle>
          <CardDescription>{String(workflowQuery.error ?? "Workflow not found")}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const workflow = workflowQuery.data;
  const events = eventsQuery.data ?? [];
  const review = workflow.review ?? null;
  const activeReview = review && workflow.status === "needs_human_review" ? review : null;
  const reviewError = reviewMutation.isError
    ? workflowErrorMessage(reviewMutation.error)
    : null;
  const decideReview = (decision: string) => {
    if (review) reviewMutation.mutate({ reviewId: review.review_id, decision });
  };

  return (
    <div
      className={cn(
        "grid w-full max-w-full min-w-0 self-start",
        focused ? "gap-4" : "gap-3",
        focused ? "mx-auto max-w-[1180px]" : "",
      )}
    >
      <Card
        className={cn(
          "min-w-0 max-w-full overflow-hidden",
          focused ? "border-l-4 border-l-primary/45" : "shadow-sm",
        )}
      >
        <CardHeader className={cn("gap-3", !focused && "gap-2 p-3 sm:p-4")}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardDescription className="font-bold uppercase">Workflow</CardDescription>
            <div className="flex min-w-0 flex-wrap items-center justify-end gap-2">
              <Button asChild size="sm" variant="outline">
                <a href={buildAssistantWorkflowContextHref(workflow.workflow_id)}>
                  <Bot className="h-4 w-4" />
                  Ask Assistant
                </a>
              </Button>
              <StatusBadge
                className="max-w-full shrink-0 justify-center whitespace-normal text-center leading-tight"
                status={workflow.status}
              />
            </div>
          </div>
          <div className="min-w-0">
            <CardTitle
              className={cn(
                "break-all font-mono text-xl leading-tight sm:text-2xl",
                !focused && "text-lg sm:text-xl",
              )}
            >
              {workflow.workflow_id}
            </CardTitle>
            <CardDescription className="mt-1 line-clamp-2">
              {workflow.user_instruction}
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2 text-xs font-bold text-muted-foreground">
            <span className="rounded-full bg-muted px-2 py-0.5 sm:py-1">
              Updated {formatCompactDate(workflow.updated_at)}
            </span>
            <span className="rounded-full bg-muted px-2 py-0.5 sm:py-1">
              Target {workflow.intent.target_format ?? "not set"}
            </span>
          </div>
        </CardHeader>
      </Card>

      <WorkflowFactStrip events={events} workflow={workflow} />

      {workflow.status === "failed" && workflow.failure ? (
        <WorkflowFailureNotice workflow={workflow} />
      ) : null}

      <Tabs className="min-w-0 max-w-full" defaultValue="overview">
        <TabsList className="flex h-auto min-w-0 max-w-full flex-wrap justify-start bg-muted/50">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="issues">Issues</TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
          <TabsTrigger value="review">Review</TabsTrigger>
          <TabsTrigger value="output">Output</TabsTrigger>
          <TabsTrigger value="audit">Audit</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Overview
            compactReview={!focused}
            review={activeReview}
            reviewError={reviewError}
            reviewIsPending={reviewMutation.isPending}
            workflow={workflow}
            onReviewDecision={decideReview}
          />
        </TabsContent>
        <TabsContent value="issues">
          <Issues workflow={workflow} />
        </TabsContent>
        <TabsContent value="evidence">
          <Evidence workflow={workflow} />
        </TabsContent>
        <TabsContent value="review">
          <ReviewTab
            error={reviewError}
            isPending={reviewMutation.isPending}
            isReviewActive={Boolean(activeReview)}
            onDecision={decideReview}
            review={review}
          />
        </TabsContent>
        <TabsContent value="output">
          <Output workflow={workflow} />
        </TabsContent>
        <TabsContent value="audit">
          <Audit events={events} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
