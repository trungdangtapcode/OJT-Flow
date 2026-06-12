import * as React from "react";
import { Network } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { Notice } from "../../../components/ui/notice";
import type { RetrievalGraphContext } from "../../../types";
import { GraphCounter } from "./graph-counter";
import { SectionHelpText } from "./section-help-text";

export function GraphPanel({
  graphContext,
}: {
  graphContext: RetrievalGraphContext | undefined;
}) {
  const summary = graphContext ? graphSummaryFromContext(graphContext) : null;
  const recognizedEntities = graphContext ? graphRecognizedEntities(graphContext) : [];
  const normalizedConcepts = graphContext ? graphNormalizedConcepts(graphContext) : [];
  const fhirSearchParameters = graphContext ? graphFhirSearchParameters(graphContext) : [];
  const relationCounts = graphContext ? graphRelationCounts(graphContext) : [];

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5 text-primary" />
          Graph handoff
        </CardTitle>
        <CardDescription>
          Auditable entities, terminology links, and FHIR search hooks prepared for Graph-NER/RAG.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        {!graphContext ? (
          <Notice title="Graph context unavailable">
            Run a search to inspect graph handoff context.
          </Notice>
        ) : (
          <>
            <div className="grid gap-2 text-sm sm:grid-cols-3 xl:grid-cols-5">
              <GraphCounter label="Nodes" value={summary?.nodeCount ?? graphContext.nodes.length} />
              <GraphCounter label="Edges" value={summary?.edgeCount ?? graphContext.edges.length} />
              <GraphCounter label="Triples" value={summary?.tripleCount ?? graphContext.triples.length} />
              <GraphCounter label="NER rules" value={summary?.ruleSourceCount ?? 0} />
              <GraphCounter label="Concepts" value={summary?.conceptRegistryCount ?? 0} />
            </div>

            <div className="flex min-w-0 flex-wrap items-center gap-2">
              <Badge variant="muted">{graphContext.graph_contract}</Badge>
              {relationCounts.slice(0, 5).map((relation) => (
                <Badge key={relation.relation} variant="muted">
                  {relation.count} {humanizeGraphText(relation.relation)}
                </Badge>
              ))}
            </div>

            <div className="grid gap-3 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
              <GraphSection
                description="What the system recognized from the query and trusted evidence."
                emptyText="No recognized entities were emitted."
                title="Recognized entities"
              >
                {recognizedEntities.slice(0, 10).map((node) => (
                  <GraphEntityRow key={node.id} node={node} />
                ))}
              </GraphSection>

              <GraphSection
                description="Dictionary normalizations are grounding hints, not autonomous clinical coding."
                emptyText="No terminology normalization was emitted."
                title="Terminology grounding"
              >
                {normalizedConcepts.slice(0, 6).map((node) => (
                  <div className="rounded-md border border-border bg-muted/20 p-2" key={node.id}>
                    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                      <div className="min-w-0">
                        <div className="break-words text-sm font-black">
                          {node.normalized_display ?? node.label}
                        </div>
                        <div className="mt-0.5 break-words font-mono text-xs text-muted-foreground">
                          {node.normalized_code}
                        </div>
                      </div>
                      <Badge variant="success">{node.normalized_system ?? "code"}</Badge>
                    </div>
                    <div className="mt-2 flex min-w-0 flex-wrap gap-1.5 text-xs">
                      {node.clinical_domain ? (
                        <Badge variant="muted">{humanizeGraphText(node.clinical_domain)}</Badge>
                      ) : null}
                      {node.matched_text ? (
                        <Badge variant="muted">matched {node.matched_text}</Badge>
                      ) : null}
                      <Badge variant="muted">{formatGraphConfidence(node.confidence)}</Badge>
                    </div>
                  </div>
                ))}
              </GraphSection>
            </div>

            <GraphSection
              description="FHIR resource search parameters exposed for downstream retrieval and MCP tools."
              emptyText="No FHIR search parameters were emitted for this query."
              title="FHIR search hooks"
            >
              {fhirSearchParameters.length ? (
                <div className="grid gap-2 md:grid-cols-2">
                  {fhirSearchParameters.slice(0, 8).map((node) => (
                    <div className="rounded-md border border-border bg-muted/20 p-2 text-sm" key={node.id}>
                      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                        <div className="break-words font-black">{node.label}</div>
                        {node.search_type ? <Badge variant="muted">{node.search_type}</Badge> : null}
                      </div>
                      {node.target_field ? (
                        <div className="mt-1 break-words text-xs font-semibold text-muted-foreground">
                          {node.target_field}
                        </div>
                      ) : null}
                      {node.example ? (
                        <div className="mt-2 break-all rounded bg-card px-2 py-1 font-mono text-xs">
                          {node.example}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : null}
            </GraphSection>

            <div className="grid gap-2">
              <div>
                <div className="text-xs font-bold uppercase text-muted-foreground">
                  Evidence triples
                </div>
                <SectionHelpText>
                  Compact audit trail showing which trusted source supports each entity or normalization.
                </SectionHelpText>
              </div>
              {graphContext.triples.slice(0, 8).map((triple, index) => (
                <div
                  className="grid gap-1 rounded-md border border-border bg-muted/20 p-2 text-sm"
                  key={`${triple.subject}-${triple.object}-${index}`}
                >
                  <div className="flex min-w-0 flex-wrap items-center gap-2">
                    <div className="break-words font-bold">{triple.subject}</div>
                    <Badge variant="muted">{humanizeGraphText(triple.predicate)}</Badge>
                  </div>
                  <div className="break-words text-sm text-muted-foreground">{triple.object}</div>
                  {triple.evidence_id ? (
                    <div className="break-all font-mono text-[11px] text-muted-foreground">
                      {triple.evidence_id}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function GraphSection({
  children,
  description,
  emptyText,
  title,
}: {
  children: React.ReactNode;
  description: string;
  emptyText: string;
  title: string;
}) {
  const childArray = React.Children.toArray(children);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card/60 p-3">
      <div>
        <div className="text-xs font-bold uppercase text-muted-foreground">{title}</div>
        <SectionHelpText>{description}</SectionHelpText>
      </div>
      {childArray.length ? childArray : <Notice title={emptyText}>{emptyText}</Notice>}
    </div>
  );
}

function GraphEntityRow({ node }: { node: RetrievalGraphContext["nodes"][number] }) {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="break-words text-sm font-black">{node.label}</div>
          <div className="mt-0.5 break-all font-mono text-[11px] text-muted-foreground">
            {node.id}
          </div>
        </div>
        <Badge variant={graphNodeBadgeVariant(node.type)}>{humanizeGraphText(node.type)}</Badge>
      </div>
      <div className="mt-2 flex min-w-0 flex-wrap gap-1.5 text-xs">
        {node.rule_source ? <Badge variant="muted">{humanizeGraphText(node.rule_source)}</Badge> : null}
        {node.matched_text ? <Badge variant="muted">matched {node.matched_text}</Badge> : null}
        <Badge variant="muted">{formatGraphConfidence(node.confidence)}</Badge>
      </div>
    </div>
  );
}

function graphSummaryFromContext(graphContext: RetrievalGraphContext) {
  const summary = graphContext.summary;
  return {
    conceptRegistryCount: numericGraphSummaryValue(summary?.concept_registry_count),
    edgeCount: numericGraphSummaryValue(summary?.edge_count) ?? graphContext.edges.length,
    nodeCount: numericGraphSummaryValue(summary?.node_count) ?? graphContext.nodes.length,
    ruleSourceCount: numericGraphSummaryValue(summary?.rule_source_count),
    tripleCount: numericGraphSummaryValue(summary?.triple_count) ?? graphContext.triples.length,
  };
}

function numericGraphSummaryValue(value: number | undefined): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function graphRecognizedEntities(graphContext: RetrievalGraphContext) {
  const priority: Record<string, number> = {
    clinical_concept: 0,
    standard: 1,
    fhir_resource: 2,
    data_field: 3,
    clinical_domain: 4,
    standard_system: 5,
  };
  return graphContext.nodes
    .filter((node) => priority[node.type] !== undefined)
    .sort((left, right) => {
      const priorityDelta = priority[left.type] - priority[right.type];
      if (priorityDelta !== 0) return priorityDelta;
      return left.label.localeCompare(right.label);
    });
}

function graphNormalizedConcepts(graphContext: RetrievalGraphContext) {
  return graphContext.nodes
    .filter((node) => Boolean(node.normalized_code))
    .sort((left, right) => left.label.localeCompare(right.label));
}

function graphFhirSearchParameters(graphContext: RetrievalGraphContext) {
  return graphContext.nodes
    .filter((node) => node.type === "fhir_search_parameter")
    .sort((left, right) => left.label.localeCompare(right.label));
}

function graphRelationCounts(graphContext: RetrievalGraphContext) {
  const counts = new Map<string, number>();
  for (const edge of graphContext.edges) {
    counts.set(edge.relation, (counts.get(edge.relation) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([relation, count]) => ({ count, relation }))
    .sort((left, right) => right.count - left.count || left.relation.localeCompare(right.relation));
}

function graphNodeBadgeVariant(
  nodeType: string,
): React.ComponentProps<typeof Badge>["variant"] {
  if (nodeType === "clinical_concept" || nodeType === "fhir_resource") return "success";
  if (nodeType === "standard" || nodeType === "standard_code") return "default";
  return "muted";
}

function formatGraphConfidence(confidence: number | undefined) {
  return typeof confidence === "number" ? `${Math.round(confidence * 100)}% confidence` : "confidence n/a";
}

function humanizeGraphText(value: string) {
  return value.replace(/[_-]+/g, " ").trim();
}
