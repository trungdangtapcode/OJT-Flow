import * as React from "react";
import { Network, RefreshCw, Search, X } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { Input, Label, Select } from "../../../components/ui/form";
import { Notice } from "../../../components/ui/notice";
import type {
  RetrievalGraphContextRecord,
  RetrievalGraphNeighborhood,
  RetrievalGraphNeighborhoodQuery,
  RetrievalPackage,
} from "../../../types";
import { SectionHelpText } from "./section-help-text";

type GraphQueryDraft = {
  evidence_id: string;
  max_depth: string;
  node_id: string;
  normalized_code: string;
  q: string;
  relation: string;
  source_id: string;
  workflow_id: string;
};

const emptyDraft: GraphQueryDraft = {
  evidence_id: "",
  max_depth: "1",
  node_id: "",
  normalized_code: "",
  q: "",
  relation: "",
  source_id: "",
  workflow_id: "",
};

export function GraphQueryPanel({
  contexts,
  currentPackage,
  isContextLoading,
  isNeighborhoodFetching,
  neighborhood,
  neighborhoodError,
  onRefreshContexts,
  onSubmitNeighborhoodQuery,
  submittedQuery,
}: {
  contexts: RetrievalGraphContextRecord[];
  currentPackage: RetrievalPackage | null | undefined;
  isContextLoading: boolean;
  isNeighborhoodFetching: boolean;
  neighborhood: RetrievalGraphNeighborhood | null;
  neighborhoodError: unknown;
  onRefreshContexts: () => void;
  onSubmitNeighborhoodQuery: (query: RetrievalGraphNeighborhoodQuery | null) => void;
  submittedQuery: RetrievalGraphNeighborhoodQuery | null;
}) {
  const [draft, setDraft] = React.useState<GraphQueryDraft>(emptyDraft);
  const currentHints = graphHintsFromPackage(currentPackage);
  const normalizedQuery = graphQueryFromDraft(draft);
  const canSubmit = hasGraphQueryCriteria(normalizedQuery);

  const updateDraft = (field: keyof GraphQueryDraft, value: string) => {
    setDraft((current) => ({ ...current, [field]: value }));
  };

  const submit = () => {
    if (!canSubmit) return;
    onSubmitNeighborhoodQuery(normalizedQuery);
  };

  const clear = () => {
    setDraft(emptyDraft);
    onSubmitNeighborhoodQuery(null);
  };

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5 text-primary" />
          Graph query
        </CardTitle>
        <CardDescription>
          Query persisted Graph-NER neighborhoods by entity, source, evidence, code, workflow, or relation.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4">
        <div className="grid gap-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div>
              <div className="text-xs font-bold uppercase text-muted-foreground">
                Neighborhood lookup
              </div>
              <SectionHelpText>
                Uses the authenticated graph neighborhood API over persisted retrieval graph records.
              </SectionHelpText>
            </div>
            <div className="flex shrink-0 flex-wrap gap-2">
              <Button
                disabled={!canSubmit || isNeighborhoodFetching}
                onClick={submit}
                size="sm"
                type="button"
              >
                <Search className="h-4 w-4" />
                Query
              </Button>
              <Button onClick={clear} size="sm" type="button" variant="outline">
                <X className="h-4 w-4" />
                Clear
              </Button>
            </div>
          </div>

          <div className="grid gap-2 md:grid-cols-2">
            <Label>
              Text
              <Input
                onChange={(event) => updateDraft("q", event.target.value)}
                placeholder="HbA1c, Observation, UCUM"
                value={draft.q}
              />
            </Label>
            <Label>
              Evidence ID
              <Input
                onChange={(event) => updateDraft("evidence_id", event.target.value)}
                placeholder="ev_..."
                value={draft.evidence_id}
              />
            </Label>
            <Label>
              Node ID
              <Input
                onChange={(event) => updateDraft("node_id", event.target.value)}
                placeholder="clinical_concept:..."
                value={draft.node_id}
              />
            </Label>
            <Label>
              Source ID
              <Input
                onChange={(event) => updateDraft("source_id", event.target.value)}
                placeholder="standard:fhir_observation_r4"
                value={draft.source_id}
              />
            </Label>
            <Label>
              Normalized code
              <Input
                onChange={(event) => updateDraft("normalized_code", event.target.value)}
                placeholder="LOINC:4548-4"
                value={draft.normalized_code}
              />
            </Label>
            <Label>
              Workflow ID
              <Input
                onChange={(event) => updateDraft("workflow_id", event.target.value)}
                placeholder="wf_..."
                value={draft.workflow_id}
              />
            </Label>
            <Label>
              Relation
              <Input
                onChange={(event) => updateDraft("relation", event.target.value)}
                placeholder="supports"
                value={draft.relation}
              />
            </Label>
            <Label>
              Depth
              <Select
                onChange={(event) => updateDraft("max_depth", event.target.value)}
                value={draft.max_depth}
              >
                <option value="0">0</option>
                <option value="1">1</option>
                <option value="2">2</option>
              </Select>
            </Label>
          </div>

          <div className="flex min-w-0 flex-wrap gap-2">
            {currentHints.topEvidenceId ? (
              <Button
                onClick={() => updateDraft("evidence_id", currentHints.topEvidenceId)}
                size="sm"
                type="button"
                variant="outline"
              >
                Use top evidence
              </Button>
            ) : null}
            {currentHints.topNodeId ? (
              <Button
                onClick={() => updateDraft("node_id", currentHints.topNodeId)}
                size="sm"
                type="button"
                variant="outline"
              >
                Use top node
              </Button>
            ) : null}
            {currentHints.topSourceId ? (
              <Button
                onClick={() => updateDraft("source_id", currentHints.topSourceId)}
                size="sm"
                type="button"
                variant="outline"
              >
                Use top source
              </Button>
            ) : null}
          </div>
        </div>

        <GraphNeighborhoodResult
          error={neighborhoodError}
          isFetching={isNeighborhoodFetching}
          neighborhood={neighborhood}
          submittedQuery={submittedQuery}
        />

        <div className="grid gap-2">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div>
              <div className="text-xs font-bold uppercase text-muted-foreground">
                Recent graph records
              </div>
              <SectionHelpText>
                Persisted graph contexts created by retrieval searches for this user.
              </SectionHelpText>
            </div>
            <Button
              disabled={isContextLoading}
              onClick={onRefreshContexts}
              size="sm"
              type="button"
              variant="outline"
            >
              <RefreshCw className={isContextLoading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
              Refresh
            </Button>
          </div>
          {!contexts.length ? (
            <Notice title={isContextLoading ? "Loading graph records" : "No persisted graph records"}>
              Run retrieval search to create graph records, then query neighborhoods here.
            </Notice>
          ) : (
            <div className="grid gap-2">
              {contexts.slice(0, 6).map((record) => (
                <GraphContextRecordRow
                  key={record.graph_id}
                  onUse={() =>
                    onSubmitNeighborhoodQuery({
                      q: record.query,
                      workflow_id: record.workflow_id ?? null,
                      limit: 100,
                      max_depth: 1,
                    })
                  }
                  record={record}
                />
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function GraphNeighborhoodResult({
  error,
  isFetching,
  neighborhood,
  submittedQuery,
}: {
  error: unknown;
  isFetching: boolean;
  neighborhood: RetrievalGraphNeighborhood | null;
  submittedQuery: RetrievalGraphNeighborhoodQuery | null;
}) {
  if (error) {
    return (
      <Notice title="Graph query failed">
        {error instanceof Error ? error.message : "The graph query could not be loaded."}
      </Notice>
    );
  }
  if (isFetching) {
    return <Notice title="Querying graph">Loading graph neighborhood.</Notice>;
  }
  if (!submittedQuery) {
    return <Notice title="No graph query submitted">Choose a graph criterion and query.</Notice>;
  }
  if (!neighborhood) return null;
  return (
    <div className="grid gap-3 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Neighborhood result
        </div>
        <div className="flex min-w-0 flex-wrap gap-1.5">
          <Badge variant={neighborhood.node_count ? "success" : "muted"}>
            {neighborhood.node_count} nodes
          </Badge>
          <Badge variant={neighborhood.edge_count ? "success" : "muted"}>
            {neighborhood.edge_count} edges
          </Badge>
          <Badge variant={neighborhood.triple_count ? "success" : "muted"}>
            {neighborhood.triple_count} triples
          </Badge>
        </div>
      </div>

      {neighborhood.warnings.length ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {neighborhood.warnings.slice(0, 4).map((warning) => (
            <Badge key={warning} variant="warning">
              {humanizeGraphValue(warning)}
            </Badge>
          ))}
        </div>
      ) : null}

      <div className="grid gap-2 xl:grid-cols-2">
        <GraphRecordList
          emptyText="No matched nodes returned."
          items={neighborhood.nodes.slice(0, 8)}
          renderItem={graphNodeSummary}
          title="Nodes"
        />
        <GraphRecordList
          emptyText="No matched edges returned."
          items={neighborhood.edges.slice(0, 8)}
          renderItem={graphEdgeSummary}
          title="Edges"
        />
      </div>

      <GraphRecordList
        emptyText="No matched triples returned."
        items={neighborhood.triples.slice(0, 8)}
        renderItem={graphTripleSummary}
        title="Triples"
      />
    </div>
  );
}

function GraphRecordList({
  emptyText,
  items,
  renderItem,
  title,
}: {
  emptyText: string;
  items: Array<Record<string, unknown>>;
  renderItem: (item: Record<string, unknown>, index: number) => React.ReactNode;
  title: string;
}) {
  return (
    <div className="grid gap-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">{title}</div>
      {items.length ? (
        items.map((item, index) => (
          <div
            className="min-w-0 rounded-md border border-border bg-card p-2 text-sm"
            key={`${title}-${index}-${stableRecordKey(item)}`}
          >
            {renderItem(item, index)}
          </div>
        ))
      ) : (
        <Notice title={emptyText}>{emptyText}</Notice>
      )}
    </div>
  );
}

function GraphContextRecordRow({
  onUse,
  record,
}: {
  onUse: () => void;
  record: RetrievalGraphContextRecord;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-2 text-sm">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="break-words font-bold">{record.query}</div>
          <div className="mt-0.5 break-all font-mono text-[11px] text-muted-foreground">
            {record.graph_id}
          </div>
        </div>
        <Button onClick={onUse} size="sm" type="button" variant="outline">
          <Search className="h-4 w-4" />
          Use
        </Button>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant="muted">{record.node_count} nodes</Badge>
        <Badge variant="muted">{record.edge_count} edges</Badge>
        <Badge variant="muted">{record.triple_count} triples</Badge>
        {record.workflow_id ? <Badge variant="muted">{record.workflow_id}</Badge> : null}
        {record.resource_type ? <Badge variant="muted">{record.resource_type}</Badge> : null}
      </div>
    </div>
  );
}

function graphHintsFromPackage(packageData: RetrievalPackage | null | undefined) {
  const graphContext = packageData?.handoff_context.graph_context;
  return {
    topEvidenceId: packageData?.hits[0]?.evidence.evidence_id ?? "",
    topNodeId: graphContext?.nodes.find((node) => node.type !== "query")?.id ?? "",
    topSourceId: packageData?.hits[0]?.evidence.source_id ?? "",
  };
}

function graphQueryFromDraft(draft: GraphQueryDraft): RetrievalGraphNeighborhoodQuery {
  return {
    evidence_id: optionalText(draft.evidence_id),
    limit: 100,
    max_depth: Number(draft.max_depth) || 1,
    node_id: optionalText(draft.node_id),
    normalized_code: optionalText(draft.normalized_code),
    q: optionalText(draft.q),
    relation: optionalText(draft.relation),
    source_id: optionalText(draft.source_id),
    workflow_id: optionalText(draft.workflow_id),
  };
}

function hasGraphQueryCriteria(query: RetrievalGraphNeighborhoodQuery) {
  return Boolean(
    query.q ||
      query.node_id ||
      query.evidence_id ||
      query.source_id ||
      query.normalized_code ||
      query.workflow_id ||
      query.relation,
  );
}

function graphNodeSummary(item: Record<string, unknown>) {
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="break-words font-bold">{stringValue(item.label, "Node")}</span>
        <Badge variant="muted">{humanizeGraphValue(stringValue(item.type, "node"))}</Badge>
      </div>
      <div className="break-all font-mono text-[11px] text-muted-foreground">
        {stringValue(item.id, "unknown")}
      </div>
    </div>
  );
}

function graphEdgeSummary(item: Record<string, unknown>) {
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-2">
        <span className="break-all font-mono text-[11px]">{stringValue(item.source, "source")}</span>
        <Badge variant="muted">{humanizeGraphValue(stringValue(item.relation, "relation"))}</Badge>
      </div>
      <div className="break-all font-mono text-[11px] text-muted-foreground">
        {stringValue(item.target, "target")}
      </div>
      {item.evidence_id ? (
        <div className="break-all font-mono text-[11px] text-muted-foreground">
          {stringValue(item.evidence_id, "")}
        </div>
      ) : null}
    </div>
  );
}

function graphTripleSummary(item: Record<string, unknown>) {
  return (
    <div className="grid gap-1">
      <div className="break-words font-bold">{stringValue(item.subject, "subject")}</div>
      <div className="flex min-w-0 flex-wrap items-center gap-2">
        <Badge variant="muted">{humanizeGraphValue(stringValue(item.predicate, "predicate"))}</Badge>
        <span className="break-words text-muted-foreground">{stringValue(item.object, "object")}</span>
      </div>
      {item.evidence_id ? (
        <div className="break-all font-mono text-[11px] text-muted-foreground">
          {stringValue(item.evidence_id, "")}
        </div>
      ) : null}
    </div>
  );
}

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function humanizeGraphValue(value: string) {
  return value.replace(/[_-]+/g, " ").trim();
}

function stableRecordKey(item: Record<string, unknown>) {
  return stringValue(item.id, "") || stringValue(item.evidence_id, "") || JSON.stringify(item);
}
