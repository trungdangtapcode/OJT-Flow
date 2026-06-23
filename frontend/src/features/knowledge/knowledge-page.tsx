import * as React from "react";
import {
  ChevronDown,
  FileSearch,
  GitBranch,
  Loader2,
  Network,
  Search,
  Upload,
} from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Notice } from "../../components/ui/notice";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { humanize } from "../../lib/utils";
import {
  useGraphMedStatusQuery,
  useKnowledgeGraphFileImportMutation,
  useKnowledgeGraphImportMutation,
  useKnowledgeGraphNeighborhoodQuery,
  useKnowledgeGraphSearchQuery,
  useKnowledgeGraphStatsQuery,
  useRetrievalSearchMutation,
  useRetrievalSearchOptionsQuery,
  useRetrievalSourcesQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import type {
  Evidence,
  GraphMedStatus,
  KnowledgeGraphEdge,
  KnowledgeGraphImportResult,
  KnowledgeGraphNode,
  KnowledgeGraphView,
  RetrievalAnswer,
  RetrievalHit,
  RetrievalPackage,
  RetrievalSearchPayload,
  RetrievalSource,
} from "../../types";

const EXAMPLE_QUERIES = [
  "What does HbA1c mean?",
  "FHIR Observation for a lab result",
  "How should UCUM units be represented?",
  "When is source evidence insufficient?",
];

const DEFAULT_TRUST_LEVEL = "approved";
const DEFAULT_TOP_K = 5;

export function KnowledgePage() {
  const [activeTab, setActiveTab] = React.useState("graph");
  const [query, setQuery] = React.useState("");
  const [topK, setTopK] = React.useState(DEFAULT_TOP_K);
  const [trustLevel, setTrustLevel] = React.useState(DEFAULT_TRUST_LEVEL);
  const [clinicalDomain, setClinicalDomain] = React.useState("");
  const [standardSystem, setStandardSystem] = React.useState("");
  const [sourceType, setSourceType] = React.useState("");
  const [submittedQuery, setSubmittedQuery] = React.useState<string | null>(null);

  const searchMutation = useRetrievalSearchMutation();
  const searchOptionsQuery = useRetrievalSearchOptionsQuery();
  const sourcesQuery = useRetrievalSourcesQuery();
  const sources = sourcesQuery.data ?? [];

  const topKOptions = uniqueNumbers([
    ...(searchOptionsQuery.data?.top_k_values ?? []),
    3,
    DEFAULT_TOP_K,
    10,
  ]);
  const trustOptions = uniqueStrings([DEFAULT_TRUST_LEVEL, ...sources.map((source) => source.trust_level)]);
  const domainOptions = uniqueStrings(sources.map((source) => source.clinical_domain));
  const standardOptions = uniqueStrings(sources.map((source) => source.standard_system));
  const sourceTypeOptions = uniqueStrings(sources.map((source) => source.source_type));

  const result = searchMutation.data ?? null;
  const trimmedQuery = query.trim();
  const canSubmit = Boolean(trimmedQuery) && !searchMutation.isPending;

  async function submitSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!trimmedQuery) return;
    const payload = buildPayload({
      clinicalDomain,
      query: trimmedQuery,
      sourceType,
      standardSystem,
      topK,
      trustLevel,
    });
    setSubmittedQuery(trimmedQuery);
    await searchMutation.mutateAsync(payload);
  }

  function useExample(value: string) {
    setQuery(value);
  }

  async function searchCorpusFromConcept(value: string) {
    const nextQuery = value.trim();
    if (!nextQuery || searchMutation.isPending) return;
    setQuery(nextQuery);
    setSubmittedQuery(nextQuery);
    setActiveTab("search");
    await searchMutation.mutateAsync(
      buildPayload({
        clinicalDomain,
        query: nextQuery,
        sourceType,
        standardSystem,
        topK,
        trustLevel,
      }),
    );
  }

  return (
    <div className="grid gap-3">
      <div className="flex min-w-0 flex-wrap items-center gap-3">
        <h1 className="text-lg font-bold tracking-tight text-foreground">Knowledge</h1>
        <Badge variant="muted">{sources.length} sources</Badge>
      </div>

      <Tabs onValueChange={setActiveTab} value={activeTab}>
        <TabsList className="w-fit max-w-full overflow-x-auto">
          <TabsTrigger value="graph">
            <Network className="h-4 w-4" />
            Graph
          </TabsTrigger>
          <TabsTrigger value="search">
            <Search className="h-4 w-4" />
            Search
          </TabsTrigger>
        </TabsList>

        <TabsContent value="graph">
          <KnowledgeGraphPanel onSearchConcept={(value) => void searchCorpusFromConcept(value)} />
        </TabsContent>

        <TabsContent value="search">
          <form className="grid gap-2" onSubmit={(event) => void submitSearch(event)}>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <textarea
                className="min-h-[2.75rem] w-full resize-y rounded-lg border border-border/70 bg-background py-2.5 pl-9 pr-3 text-sm font-medium leading-6 outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/15"
                id="knowledge-query"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search medical knowledge... e.g. HbA1c, FHIR Observation, UCUM units"
                value={query}
              />
            </div>

            <div className="flex min-w-0 flex-wrap items-center gap-2">
              {EXAMPLE_QUERIES.map((example) => (
                <button
                  className="rounded-full border border-border/50 bg-muted/30 px-2.5 py-1 text-[11px] font-medium text-muted-foreground transition hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
                  key={example}
                  onClick={() => useExample(example)}
                  type="button"
                >
                  {example}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <Button disabled={!canSubmit} size="sm" type="submit">
                {searchMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Search className="h-3.5 w-3.5" />
                )}
                Search
              </Button>

              <details className="rounded-lg border border-border/40 bg-muted/10 px-3 py-1.5">
                <summary className="flex cursor-pointer list-none items-center gap-1.5 text-xs font-medium text-muted-foreground">
                  <ChevronDown className="h-3 w-3" />
                  Filters
                </summary>
                <div className="mt-2 grid gap-2 border-t border-border/40 pt-2 sm:grid-cols-5">
                  <SelectField
                    label="Results"
                    onChange={(value) => setTopK(Number(value))}
                    options={topKOptions.map((value) => ({
                      label: String(value),
                      value: String(value),
                    }))}
                    value={String(topK)}
                  />
                  <SelectField
                    label="Trust"
                    onChange={setTrustLevel}
                    options={withAnyOption(trustOptions)}
                    value={trustLevel}
                  />
                  <SelectField
                    label="Domain"
                    onChange={setClinicalDomain}
                    options={withAnyOption(domainOptions)}
                    value={clinicalDomain}
                  />
                  <SelectField
                    label="Standard"
                    onChange={setStandardSystem}
                    options={withAnyOption(standardOptions)}
                    value={standardSystem}
                  />
                  <SelectField
                    label="Source"
                    onChange={setSourceType}
                    options={withAnyOption(sourceTypeOptions)}
                    value={sourceType}
                  />
                </div>
              </details>
            </div>

            {sourcesQuery.isError ? (
              <p className="text-xs text-amber-700">Filters limited - source metadata unavailable.</p>
            ) : null}
          </form>

          {searchMutation.isError ? (
            <Notice title="Search failed" tone="danger">
              {workflowErrorMessage(searchMutation.error)}
            </Notice>
          ) : null}

          {searchMutation.isPending ? <LoadingResults /> : null}

          {!searchMutation.isPending && result ? (
            <KnowledgeResults
              packageData={result}
              query={submittedQuery ?? trimmedQuery}
              sources={sources}
            />
          ) : null}

          {!result && !searchMutation.isPending && !searchMutation.isError ? <EmptyState /> : null}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function KnowledgeGraphPanel({
  onSearchConcept,
}: {
  onSearchConcept: (value: string) => void;
}) {
  const [graphQuery, setGraphQuery] = React.useState("");
  const [submittedGraphQuery, setSubmittedGraphQuery] = React.useState("");
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);
  const [selectedEdgeKey, setSelectedEdgeKey] = React.useState<string | null>(null);
  const [importText, setImportText] = React.useState("");
  const [importFile, setImportFile] = React.useState<File | null>(null);

  const statsQuery = useKnowledgeGraphStatsQuery();
  const graphMedStatusQuery = useGraphMedStatusQuery();
  const graphSearchQuery = useKnowledgeGraphSearchQuery({
    limit: 24,
    q: submittedGraphQuery,
  });
  const graphNodes = graphSearchQuery.data ?? [];
  const neighborhoodQuery = useKnowledgeGraphNeighborhoodQuery(
    selectedNodeId
      ? { depth: 2, limit: 80, node_id: selectedNodeId }
      : submittedGraphQuery
        ? { depth: 1, limit: 80, q: submittedGraphQuery }
        : null,
    { enabled: Boolean(selectedNodeId || submittedGraphQuery) },
  );
  const importMutation = useKnowledgeGraphImportMutation();
  const fileImportMutation = useKnowledgeGraphFileImportMutation();

  React.useEffect(() => {
    if (selectedNodeId || !graphNodes.length) return;
    setSelectedNodeId(graphNodes[0].node_id);
  }, [graphNodes, selectedNodeId]);

  const view = neighborhoodQuery.data ?? emptyGraphView();
  const selectedNode =
    view.nodes.find((node) => node.node_id === selectedNodeId)
    ?? graphNodes.find((node) => node.node_id === selectedNodeId)
    ?? null;
  const selectedEdge =
    view.edges.find((edge) => edgeKey(edge) === selectedEdgeKey) ?? null;

  function submitGraphSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSelectedNodeId(null);
    setSelectedEdgeKey(null);
    setSubmittedGraphQuery(graphQuery.trim());
  }

  async function submitImport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = importText.trim();
    if ((!text && !importFile) || importMutation.isPending || fileImportMutation.isPending) return;
    if (importFile) {
      await fileImportMutation.mutateAsync({ file: importFile });
    } else {
      await importMutation.mutateAsync({ text });
    }
    setImportText("");
    setImportFile(null);
    setSelectedNodeId(null);
    setSelectedEdgeKey(null);
  }

  return (
    <section className="grid gap-3">
      <div className="grid gap-2 rounded-lg border border-border/60 bg-card p-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="muted">
            {statsQuery.data ? `${statsQuery.data.node_count} nodes` : "nodes"}
          </Badge>
          <Badge variant="muted">
            {statsQuery.data ? `${statsQuery.data.edge_count} edges` : "edges"}
          </Badge>
          <Badge variant="muted">
            {statsQuery.data ? `${statsQuery.data.chunk_count} chunks` : "chunks"}
          </Badge>
        </div>

        {statsQuery.isError ? (
          <Notice title="Graph unavailable" tone="danger">
            {workflowErrorMessage(statsQuery.error)}
          </Notice>
        ) : null}

        {graphMedStatusQuery.data ? (
          <GraphMedStatusStrip status={graphMedStatusQuery.data} />
        ) : null}

        <form className="flex min-w-0 flex-wrap items-center gap-2" onSubmit={submitGraphSearch}>
          <div className="relative min-w-[14rem] flex-1">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              className="h-10 w-full rounded-lg border border-border/70 bg-background pl-9 pr-3 text-sm font-medium outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/15"
              onChange={(event) => setGraphQuery(event.target.value)}
              placeholder="Search graph concepts"
              value={graphQuery}
            />
          </div>
          <Button disabled={graphSearchQuery.isFetching} size="sm" type="submit">
            {graphSearchQuery.isFetching ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <GitBranch className="h-3.5 w-3.5" />
            )}
            Graph
          </Button>
        </form>

        {graphSearchQuery.isError ? (
          <Notice title="Graph search failed" tone="danger">
            {workflowErrorMessage(graphSearchQuery.error)}
          </Notice>
        ) : null}

        {graphNodes.length ? (
          <div className="flex gap-2 overflow-x-auto pb-1">
            {graphNodes.map((node) => (
              <button
                className="min-w-[10rem] rounded-lg border border-border/60 bg-background px-3 py-2 text-left text-xs transition hover:border-primary/40 hover:bg-primary/5 data-[selected=true]:border-primary/60 data-[selected=true]:bg-primary/10"
                data-selected={node.node_id === selectedNodeId}
                key={node.node_id}
                onClick={() => {
                  setSelectedNodeId(node.node_id);
                  setSelectedEdgeKey(null);
                }}
                type="button"
              >
                <span className="block truncate font-bold text-foreground">{node.label}</span>
                <span className="mt-1 block truncate text-muted-foreground">
                  {node.code_system || humanize(node.node_type)}
                </span>
              </button>
            ))}
          </div>
        ) : !graphSearchQuery.isFetching && !graphSearchQuery.isError ? (
          <div className="rounded-lg border border-dashed border-border/60 px-4 py-5 text-sm text-muted-foreground">
            No graph nodes indexed
          </div>
        ) : null}
      </div>

      <div className="grid min-h-[28rem] gap-3 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <GraphCanvas
          selectedEdgeKey={selectedEdgeKey}
          selectedNodeId={selectedNodeId}
          view={view}
          onSelectEdge={(edge) => {
            setSelectedEdgeKey(edgeKey(edge));
            setSelectedNodeId(null);
          }}
          onSelectNode={(node) => {
            setSelectedNodeId(node.node_id);
            setSelectedEdgeKey(null);
          }}
        />
        <GraphInspector
          edge={selectedEdge}
          node={selectedNode}
          onImport={submitImport}
          onSearchConcept={onSearchConcept}
          graphMedStatus={graphMedStatusQuery.data ?? null}
          importError={importMutation.error ?? fileImportMutation.error ?? null}
          importFile={importFile}
          importPending={importMutation.isPending || fileImportMutation.isPending}
          importResult={importMutation.data ?? fileImportMutation.data ?? null}
          importText={importText}
          setImportFile={setImportFile}
          setImportText={setImportText}
        />
      </div>

      {neighborhoodQuery.isError ? (
        <Notice title="Neighborhood failed" tone="danger">
          {workflowErrorMessage(neighborhoodQuery.error)}
        </Notice>
      ) : null}
    </section>
  );
}

function GraphMedStatusStrip({ status }: { status: GraphMedStatus }) {
  const tone = status.available ? "success" : "warning";
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-2 rounded-lg border border-border/50 bg-muted/15 px-3 py-2 text-xs">
      <Badge variant={tone}>{status.available ? "graph-med ready" : "graph-med unavailable"}</Badge>
      <span className="min-w-0 flex-1 text-muted-foreground">{status.message}</span>
      <Badge variant="muted">{status.icd_disease_count} ICD</Badge>
      <Badge variant="muted">{status.hpo_phenotype_count} HPO</Badge>
      <Badge variant={status.gpu_required && !status.gpu_available ? "warning" : "muted"}>
        GPU {status.gpu_available ? "ready" : status.gpu_required ? "missing" : "optional"}
      </Badge>
      <Badge variant="muted">
        annotation providers{" "}
        {graphMedEndpointLabel(status)}
      </Badge>
      {status.gnn_endpoint_configured ? (
        <Badge variant={status.gnn_endpoint_reachable ? "muted" : "warning"}>
          GNN {status.gnn_endpoint_reachable ? "reachable" : "offline"}
        </Badge>
      ) : null}
    </div>
  );
}

function graphMedEndpointLabel(status: GraphMedStatus) {
  if (!status.embedding_endpoint_configured || !status.llm_endpoint_configured) {
    return "missing";
  }
  if (!status.embedding_endpoint_reachable || !status.llm_endpoint_reachable) {
    return "offline";
  }
  return "reachable";
}

const GRAPH_W = 720;
const GRAPH_H = 460;
const MIN_ZOOM = 0.4;
const MAX_ZOOM = 4;

function GraphCanvas({
  selectedEdgeKey,
  selectedNodeId,
  view,
  onSelectEdge,
  onSelectNode,
}: {
  selectedEdgeKey: string | null;
  selectedNodeId: string | null;
  view: KnowledgeGraphView;
  onSelectEdge: (edge: KnowledgeGraphEdge) => void;
  onSelectNode: (node: KnowledgeGraphNode) => void;
}) {
  const [hoveredNodeId, setHoveredNodeId] = React.useState<string | null>(null);
  const [transform, setTransform] = React.useState({ k: 1, x: 0, y: 0 });
  const dragRef = React.useRef<{ x: number; y: number; tx: number; ty: number } | null>(null);
  const svgRef = React.useRef<SVGSVGElement | null>(null);

  const layout = React.useMemo(() => graphLayout(view.nodes, view.edges), [view]);
  const degree = React.useMemo(() => {
    const counts = new Map<string, number>();
    for (const edge of view.edges) {
      counts.set(edge.source_node_id, (counts.get(edge.source_node_id) ?? 0) + 1);
      counts.set(edge.target_node_id, (counts.get(edge.target_node_id) ?? 0) + 1);
    }
    return counts;
  }, [view]);
  // Only label hub nodes by default (top by degree) so dense graphs stay readable;
  // everything else reveals its label on hover/selection.
  const alwaysLabel = React.useMemo(() => {
    const ranked = [...view.nodes].sort(
      (a, b) => (degree.get(b.node_id) ?? 0) - (degree.get(a.node_id) ?? 0),
    );
    const keep = view.nodes.length <= 16 ? view.nodes.length : 12;
    return new Set(ranked.slice(0, keep).map((node) => node.node_id));
  }, [view, degree]);

  React.useEffect(() => {
    setTransform({ k: 1, x: 0, y: 0 });
  }, [view]);

  // Native non-passive wheel listener so we can preventDefault page scroll while zooming.
  React.useEffect(() => {
    const el = svgRef.current;
    if (!el) return undefined;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      setTransform((current) => {
        const factor = event.deltaY < 0 ? 1.12 : 0.89;
        return { ...current, k: clampZoom(current.k * factor) };
      });
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  if (!view.nodes.length) {
    return (
      <div className="flex min-h-[28rem] items-center justify-center rounded-lg border border-dashed border-border/60 bg-muted/10 text-sm text-muted-foreground">
        <Network className="mr-2 h-4 w-4" />
        No neighborhood selected
      </div>
    );
  }

  const activeNodeId = hoveredNodeId ?? selectedNodeId;
  const isEdgeActive = (edge: KnowledgeGraphEdge) =>
    edgeKey(edge) === selectedEdgeKey ||
    edge.source_node_id === activeNodeId ||
    edge.target_node_id === activeNodeId;

  const onPointerDown = (event: React.PointerEvent<SVGSVGElement>) => {
    if (event.button !== 0) return;
    dragRef.current = { x: event.clientX, y: event.clientY, tx: transform.x, ty: transform.y };
  };
  const onPointerMove = (event: React.PointerEvent<SVGSVGElement>) => {
    const drag = dragRef.current;
    if (!drag) return;
    setTransform((current) => ({
      ...current,
      x: drag.tx + (event.clientX - drag.x),
      y: drag.ty + (event.clientY - drag.y),
    }));
  };
  const endDrag = () => {
    dragRef.current = null;
  };
  const zoomBy = (factor: number) =>
    setTransform((current) => ({ ...current, k: clampZoom(current.k * factor) }));

  return (
    <div className="relative min-h-[28rem] overflow-hidden rounded-lg border border-border/60 bg-[radial-gradient(circle_at_50%_30%,rgba(14,165,233,0.08),transparent_45%),linear-gradient(180deg,rgba(248,250,252,0.95),rgba(255,255,255,1))]">
      <div className="pointer-events-none absolute left-3 top-3 z-10 rounded-md bg-white/80 px-2 py-1 text-[11px] font-bold text-muted-foreground shadow-sm backdrop-blur">
        {view.nodes.length} nodes · {view.edges.length} edges
      </div>
      <div className="absolute right-3 top-3 z-10 flex flex-col overflow-hidden rounded-md border border-border/60 bg-white/90 shadow-sm backdrop-blur">
        <button
          aria-label="Zoom in"
          className="px-2 py-1 text-sm font-bold text-slate-600 hover:bg-slate-100"
          onClick={() => zoomBy(1.2)}
          type="button"
        >
          +
        </button>
        <button
          aria-label="Zoom out"
          className="border-t border-border/60 px-2 py-1 text-sm font-bold text-slate-600 hover:bg-slate-100"
          onClick={() => zoomBy(0.83)}
          type="button"
        >
          −
        </button>
        <button
          aria-label="Reset view"
          className="border-t border-border/60 px-2 py-1 text-[10px] font-bold text-slate-600 hover:bg-slate-100"
          onClick={() => setTransform({ k: 1, x: 0, y: 0 })}
          type="button"
        >
          RESET
        </button>
      </div>
      <GraphLegend nodes={view.nodes} />
      <svg
        aria-label="Knowledge graph neighborhood"
        className="h-full min-h-[28rem] w-full touch-none select-none"
        ref={svgRef}
        role="img"
        style={{ cursor: dragRef.current ? "grabbing" : "grab" }}
        viewBox={`0 0 ${GRAPH_W} ${GRAPH_H}`}
        onPointerDown={onPointerDown}
        onPointerLeave={endDrag}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
      >
        <defs>
          <marker id="graph-arrow" markerHeight="7" markerWidth="7" orient="auto" refX="6.5" refY="3.5">
            <path d="M0,0 L7,3.5 L0,7 z" fill="#cbd5e1" />
          </marker>
          <marker id="graph-arrow-active" markerHeight="8" markerWidth="8" orient="auto" refX="6.5" refY="4">
            <path d="M0,0 L8,4 L0,8 z" fill="#0f766e" />
          </marker>
        </defs>
        <g transform={`translate(${transform.x} ${transform.y}) scale(${transform.k})`}>
          {view.edges.map((edge) => {
            const source = layout.get(edge.source_node_id);
            const target = layout.get(edge.target_node_id);
            if (!source || !target) return null;
            const active = isEdgeActive(edge);
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const norm = Math.hypot(dx, dy) || 1;
            const curve = Math.min(34, norm * 0.12);
            const cx = (source.x + target.x) / 2 - (dy / norm) * curve;
            const cy = (source.y + target.y) / 2 + (dx / norm) * curve;
            return (
              <g
                className="cursor-pointer"
                key={edgeKey(edge)}
                onClick={() => onSelectEdge(edge)}
                role="button"
                tabIndex={0}
              >
                <path
                  d={`M ${source.x} ${source.y} Q ${cx} ${cy} ${target.x} ${target.y}`}
                  fill="none"
                  markerEnd={active ? "url(#graph-arrow-active)" : "url(#graph-arrow)"}
                  stroke={active ? "#0f766e" : "#cbd5e1"}
                  strokeOpacity={active ? 0.95 : 0.45}
                  strokeWidth={active ? 2.2 : 1.1}
                />
                {active ? (
                  <text
                    fill="#0f766e"
                    fontSize="9"
                    fontWeight="700"
                    paintOrder="stroke"
                    stroke="#ffffff"
                    strokeWidth="3"
                    textAnchor="middle"
                    x={cx}
                    y={cy - 3}
                  >
                    {truncateLabel(humanize(edge.relation), 22)}
                  </text>
                ) : null}
              </g>
            );
          })}
          {view.nodes.map((node) => {
            const point = layout.get(node.node_id);
            if (!point) return null;
            const selected = node.node_id === selectedNodeId;
            const hovered = node.node_id === hoveredNodeId;
            const dimmed = activeNodeId !== null && !selected && !hovered &&
              !view.edges.some(
                (edge) =>
                  isEdgeActive(edge) &&
                  (edge.source_node_id === node.node_id || edge.target_node_id === node.node_id),
              );
            const radius = 6 + Math.min(12, (degree.get(node.node_id) ?? 0) * 1.4) +
              (selected || hovered ? 3 : 0);
            const showLabel = selected || hovered || alwaysLabel.has(node.node_id);
            return (
              <g
                className="cursor-pointer"
                key={node.node_id}
                onClick={() => onSelectNode(node)}
                onPointerEnter={() => setHoveredNodeId(node.node_id)}
                onPointerLeave={() => setHoveredNodeId((current) =>
                  current === node.node_id ? null : current,
                )}
                opacity={dimmed ? 0.3 : 1}
                role="button"
                tabIndex={0}
              >
                <circle
                  cx={point.x}
                  cy={point.y}
                  fill={nodeColor(node.node_type)}
                  r={radius}
                  stroke={selected ? "#0f172a" : hovered ? "#0f766e" : "#ffffff"}
                  strokeWidth={selected || hovered ? 2.5 : 1.5}
                />
                {showLabel ? (
                  <text
                    fill="#0f172a"
                    fontSize="10"
                    fontWeight={selected || hovered ? 800 : 600}
                    paintOrder="stroke"
                    stroke="#ffffff"
                    strokeWidth="3"
                    textAnchor="middle"
                    x={point.x}
                    y={point.y + radius + 11}
                  >
                    {truncateLabel(node.label, 24)}
                  </text>
                ) : null}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}

function clampZoom(value: number): number {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, value));
}

function GraphLegend({ nodes }: { nodes: KnowledgeGraphNode[] }) {
  const present = React.useMemo(() => {
    const seen = new Map<string, string>();
    for (const node of nodes) {
      const entry = legendEntry(node.node_type);
      if (!seen.has(entry.label)) seen.set(entry.label, entry.color);
    }
    return [...seen.entries()];
  }, [nodes]);
  if (!present.length) return null;
  return (
    <div className="pointer-events-none absolute bottom-3 left-3 z-10 flex flex-wrap gap-x-3 gap-y-1 rounded-md bg-white/80 px-2 py-1 shadow-sm backdrop-blur">
      {present.map(([label, color]) => (
        <span className="flex items-center gap-1 text-[10px] font-bold text-slate-600" key={label}>
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
          {label}
        </span>
      ))}
    </div>
  );
}

function legendEntry(nodeType: string): { label: string; color: string } {
  const type = nodeType.toLowerCase();
  if (type.includes("hpo")) return { label: "HPO phenotype", color: "#bae6fd" };
  if (type.includes("icd") || type.includes("condition")) return { label: "ICD / condition", color: "#bbf7d0" };
  if (type.includes("medication") || type.includes("rxnorm")) return { label: "Medication", color: "#fde68a" };
  if (type.includes("observation") || type.includes("loinc")) return { label: "Observation", color: "#ddd6fe" };
  if (type.includes("umls")) return { label: "UMLS", color: "#fecaca" };
  return { label: "Other", color: "#e2e8f0" };
}

function GraphInspector({
  edge,
  graphMedStatus,
  importError,
  importFile,
  importPending,
  importResult,
  importText,
  node,
  onImport,
  onSearchConcept,
  setImportFile,
  setImportText,
}: {
  edge: KnowledgeGraphEdge | null;
  graphMedStatus: GraphMedStatus | null;
  importError: unknown;
  importFile: File | null;
  importPending: boolean;
  importResult: KnowledgeGraphImportResult | null;
  importText: string;
  node: KnowledgeGraphNode | null;
  onImport: (event: React.FormEvent<HTMLFormElement>) => void;
  onSearchConcept: (value: string) => void;
  setImportFile: (value: File | null) => void;
  setImportText: (value: string) => void;
}) {
  return (
    <aside className="grid content-start gap-3 rounded-lg border border-border/60 bg-card p-3">
      {edge ? <EdgeProvenancePanel edge={edge} /> : <NodeProvenancePanel node={node} onSearchConcept={onSearchConcept} />}

      <form className="grid gap-2 border-t border-border/60 pt-3" onSubmit={onImport}>
        <label className="grid gap-1.5 text-xs font-bold text-muted-foreground">
          graph-med import
          <textarea
            className="min-h-24 resize-y rounded-lg border border-border/70 bg-background px-3 py-2 text-sm font-medium text-foreground outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/15"
            onChange={(event) => setImportText(event.target.value)}
            placeholder="Paste clinical note text"
            value={importText}
          />
        </label>
        <label className="grid gap-1.5 text-xs font-bold text-muted-foreground">
          File
          <input
            accept=".txt,.csv,.md,.json,text/plain,text/csv,application/json"
            className="block w-full text-xs text-muted-foreground file:mr-2 file:rounded-md file:border-0 file:bg-primary/10 file:px-2.5 file:py-1.5 file:text-xs file:font-bold file:text-primary"
            key={importFile?.name ?? "empty-graph-med-upload"}
            onChange={(event) => setImportFile(event.target.files?.[0] ?? null)}
            type="file"
          />
        </label>
        {importFile ? (
          <div className="text-xs font-semibold text-muted-foreground">{importFile.name}</div>
        ) : null}
        {graphMedStatus && !graphMedStatus.available ? (
          <Notice title="graph-med import unavailable">
            {graphMedStatus.message}
          </Notice>
        ) : null}
        {importError ? (
          <Notice title="Import failed" tone="danger">
            {workflowErrorMessage(importError)}
          </Notice>
        ) : null}
        <div className="flex items-center gap-2">
          <Button
            disabled={
              (!importText.trim() && !importFile)
              || importPending
              || Boolean(graphMedStatus && !graphMedStatus.available)
            }
            size="sm"
            type="submit"
          >
            {importPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Upload className="h-3.5 w-3.5" />
            )}
            Import
          </Button>
          {importResult ? (
            <span className="text-xs font-semibold text-muted-foreground">
              {importResult.linked_entities} linked, {importResult.nodes} nodes
            </span>
          ) : null}
        </div>
      </form>
    </aside>
  );
}

function NodeProvenancePanel({
  node,
  onSearchConcept,
}: {
  node: KnowledgeGraphNode | null;
  onSearchConcept: (value: string) => void;
}) {
  if (!node) {
    return (
      <div className="rounded-lg border border-dashed border-border/60 px-3 py-5 text-sm text-muted-foreground">
        Select a node or edge
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      <div className="grid gap-1">
        <div className="text-sm font-black leading-5 text-foreground">{node.label}</div>
        <div className="flex flex-wrap gap-1">
          <Badge variant="muted">{humanize(node.node_type)}</Badge>
          <Badge variant={node.review_state === "accepted" ? "success" : "warning"}>
            {humanize(node.review_state)}
          </Badge>
        </div>
      </div>
      <dl className="grid gap-2 text-xs">
        <GraphFact label="Code" value={node.normalized_code || "n/a"} />
        <GraphFact label="System" value={node.code_system || "n/a"} />
        <GraphFact label="Scope" value={humanize(node.scope)} />
        <GraphFact label="Confidence" value={formatOptionalNumber(node.confidence)} />
      </dl>
      {node.aliases.length ? (
        <div className="flex flex-wrap gap-1">
          {node.aliases.slice(0, 8).map((alias) => (
            <Badge key={alias} variant="muted">
              {alias}
            </Badge>
          ))}
        </div>
      ) : null}
      {node.source_chunk_ids.length ? (
        <div className="grid gap-1">
          <div className="text-[11px] font-bold uppercase text-muted-foreground">
            Provenance
          </div>
          <div className="flex flex-wrap gap-1">
            {node.source_chunk_ids.map((chunkId) => (
              <Badge key={chunkId} variant="muted">
                {chunkId}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}
      <Button size="sm" type="button" onClick={() => onSearchConcept(node.label)}>
        <Search className="h-3.5 w-3.5" />
        Search concept
      </Button>
    </div>
  );
}

function EdgeProvenancePanel({ edge }: { edge: KnowledgeGraphEdge }) {
  return (
    <div className="grid gap-3">
      <div className="grid gap-1">
        <div className="text-sm font-black leading-5 text-foreground">
          {humanize(edge.relation)}
        </div>
        <div className="flex flex-wrap gap-1">
          <Badge variant="muted">{formatOptionalNumber(edge.confidence)}</Badge>
          <Badge variant={edge.review_state === "accepted" ? "success" : "warning"}>
            {humanize(edge.review_state)}
          </Badge>
        </div>
      </div>
      <dl className="grid gap-2 text-xs">
        <GraphFact label="Source" value={edge.source_node_id} />
        <GraphFact label="Target" value={edge.target_node_id} />
      </dl>
      {edge.source_chunk_ids.length ? (
        <div className="flex flex-wrap gap-1">
          {edge.source_chunk_ids.map((chunkId) => (
            <Badge key={chunkId} variant="muted">
              {chunkId}
            </Badge>
          ))}
        </div>
      ) : null}
      {edge.source_snippets.length ? (
        <div className="grid gap-2">
          <div className="text-[11px] font-bold uppercase text-muted-foreground">
            Provenance
          </div>
          {edge.source_snippets.map((snippet, index) => (
            <blockquote
              className="rounded border-l-2 border-primary/30 bg-muted/20 px-2.5 py-1.5 text-xs leading-5 text-muted-foreground"
              key={`${snippet}-${index}`}
            >
              {cleanText(snippet)}
            </blockquote>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-border/60 px-3 py-4 text-xs text-muted-foreground">
          No source sentence resolved
        </div>
      )}
    </div>
  );
}

function GraphFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-0.5">
      <dt className="text-[10px] font-bold uppercase text-muted-foreground">{label}</dt>
      <dd className="break-words font-semibold text-foreground">{value}</dd>
    </div>
  );
}

function KnowledgeResults({
  packageData,
  query,
  sources,
}: {
  packageData: RetrievalPackage;
  query: string;
  sources: RetrievalSource[];
}) {
  const hitCount = packageData.hits.length;
  const sourceCount = new Set(packageData.hits.map((hit) => hit.evidence.source_id)).size;

  if (!hitCount) {
    return (
      <Notice title="No results">
        No evidence for &quot;{query}&quot;. Try a different term or check indexing.
      </Notice>
    );
  }

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-semibold text-muted-foreground">
          {hitCount} result{hitCount === 1 ? "" : "s"} from {sourceCount} source
          {sourceCount === 1 ? "" : "s"}
        </div>
        <Badge variant="muted">{packageData.trace.strategy}</Badge>
      </div>

      <AnswerPanel answer={packageData.answer ?? null} evidence={packageData.evidence} />

      <div className="grid gap-3">
        {packageData.hits.map((hit, index) => (
          <KnowledgeHitCard
            hit={hit}
            index={index}
            key={`${hit.evidence.evidence_id}-${index}`}
            source={sources.find((item) => item.source_id === hit.evidence.source_id) ?? null}
          />
        ))}
      </div>

      <details className="rounded-xl border border-border/60 bg-card p-4 text-sm">
        <summary className="cursor-pointer list-none font-bold">Retrieval details</summary>
        <div className="mt-3 grid gap-2 text-xs text-muted-foreground">
          <div>Strategy: {packageData.trace.strategy}</div>
          <div>Final hit IDs: {packageData.trace.final_hit_ids.join(", ") || "n/a"}</div>
          {packageData.trace.warnings.length ? (
            <div>Warnings: {packageData.trace.warnings.join("; ")}</div>
          ) : null}
        </div>
      </details>
    </section>
  );
}

function AnswerPanel({
  answer,
  evidence,
}: {
  answer: RetrievalAnswer | null;
  evidence: Evidence[];
}) {
  if (!answer) {
    return null;
  }

  const statusVariant =
    answer.status === "supported"
      ? "success"
      : answer.status === "refused"
        ? "destructive"
        : "warning";

  return (
    <section className="grid gap-2 rounded-lg border border-primary/20 bg-primary/5 p-3">
      <div className="flex items-center gap-2">
        <Badge variant={statusVariant}>{humanize(answer.status)}</Badge>
        {answer.citations.length ? (
          <span className="text-xs text-muted-foreground">{answer.citations.length} citations</span>
        ) : null}
      </div>

      {answer.answer_text ? (
        <p className="whitespace-pre-wrap text-sm leading-6 text-foreground">{answer.answer_text}</p>
      ) : null}

      {answer.refusal_reason ? (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          {answer.refusal_reason}
        </p>
      ) : null}

      {answer.missing_evidence_gaps.length ? (
        <ul className="grid gap-1 text-xs text-muted-foreground">
          {answer.missing_evidence_gaps.map((gap) => (
            <li key={gap}>- {gap}</li>
          ))}
        </ul>
      ) : null}

      {answer.citations.length ? (
        <div className="flex flex-wrap gap-1">
          {answer.citations.map((citation) => {
            const citedEvidence = evidence.find((item) => item.evidence_id === citation.evidence_id);
            return (
              <Badge key={citation.citation_id} variant="muted">
                {citedEvidence?.source_id ?? citation.source_id}
              </Badge>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}

function KnowledgeHitCard({
  hit,
  index,
  source,
}: {
  hit: RetrievalHit;
  index: number;
  source: RetrievalSource | null;
}) {
  return (
    <article className="grid gap-2 rounded-lg border border-border/50 bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="flex min-w-0 items-baseline gap-2">
          <span className="text-[10px] font-bold text-muted-foreground">#{index + 1}</span>
          <h2 className="break-words text-sm font-bold leading-5">
            {source?.title ?? hit.evidence.source_id}
          </h2>
        </div>
        <div className="flex flex-wrap gap-1">
          <Badge variant="default">{humanize(hit.evidence.source_type)}</Badge>
          <Badge variant="muted">{formatScore(hit.score)}</Badge>
        </div>
      </div>

      <p className="text-sm leading-5 text-foreground">{cleanText(hit.evidence.claim)}</p>

      {hit.snippet?.text ? (
        <blockquote className="rounded border-l-2 border-primary/30 bg-muted/20 px-2.5 py-1.5 text-xs leading-5 text-muted-foreground">
          {cleanText(hit.snippet.text)}
        </blockquote>
      ) : null}

      {hit.matched_terms.length ? (
        <div className="flex flex-wrap gap-1">
          {hit.matched_terms.slice(0, 6).map((term) => (
            <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[11px] font-medium text-primary" key={term}>
              {term}
            </span>
          ))}
        </div>
      ) : null}

      <details className="text-xs text-muted-foreground">
        <summary className="cursor-pointer list-none text-[11px] font-medium text-foreground">Details</summary>
        <div className="mt-1.5 grid gap-1">
          <div>{hit.evidence.source_id} / {humanize(hit.evidence.trust_level)}</div>
          <div>Confidence: {formatOptionalNumber(hit.evidence.confidence)} | Vector: {formatScore(hit.vector_score)} | Rerank: {formatScore(hit.rerank_score)}</div>
          {source?.authority ? <div>Authority: {source.authority}</div> : null}
        </div>
      </details>
    </article>
  );
}

function EmptyState() {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-dashed border-border/60 px-4 py-8 text-sm text-muted-foreground">
      <FileSearch className="h-4 w-4" />
      Enter a question to search the knowledge corpus
    </div>
  );
}

function LoadingResults() {
  return (
    <div className="flex items-center gap-2 px-2 py-4 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin text-primary" />
      Searching...
    </div>
  );
}

function SelectField({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  value: string;
}) {
  return (
    <label className="grid gap-1.5 text-xs font-bold text-muted-foreground">
      {label}
      <select
        className="h-9 rounded-lg border border-border/70 bg-background px-2 text-sm font-semibold text-foreground outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/15"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        {options.map((option) => (
          <option key={`${label}-${option.value}`} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function buildPayload({
  clinicalDomain,
  query,
  sourceType,
  standardSystem,
  topK,
  trustLevel,
}: {
  clinicalDomain: string;
  query: string;
  sourceType: string;
  standardSystem: string;
  topK: number;
  trustLevel: string;
}): RetrievalSearchPayload {
  const normalizedTrust = trustLevel || null;
  const normalizedDomain = clinicalDomain || null;
  const normalizedStandard = standardSystem || null;
  const normalizedSourceType = sourceType || null;

  return {
    clinical_domain: normalizedDomain,
    fields: [],
    filters: {
      clinical_domain: normalizedDomain,
      source_type: normalizedSourceType,
      standard_system: normalizedStandard,
      trust_level: normalizedTrust,
    },
    query,
    source_type: normalizedSourceType,
    standard_system: normalizedStandard,
    top_k: topK,
    trust_level: normalizedTrust,
  };
}

function uniqueStrings(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort(
    (left, right) => humanize(left).localeCompare(humanize(right)),
  );
}

function uniqueNumbers(values: Array<number | null | undefined>): number[] {
  return Array.from(
    new Set(
      values.filter(
        (value): value is number => typeof value === "number" && Number.isFinite(value) && value > 0,
      ),
    ),
  ).sort((left, right) => left - right);
}

function withAnyOption(values: string[]): Array<{ label: string; value: string }> {
  return [
    { label: "Any", value: "" },
    ...values.map((value) => ({
      label: value === DEFAULT_TRUST_LEVEL ? "Approved" : capitalizeWords(humanize(value)),
      value,
    })),
  ];
}

function cleanText(value: string): string {
  return value
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[ \t]+/g, " ")
    .trim();
}

function formatScore(value: number): string {
  return Number.isFinite(value) ? value.toFixed(3) : "n/a";
}

function formatOptionalNumber(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(3) : "n/a";
}

function capitalizeWords(value: string): string {
  return value.replace(/\b[a-z]/g, (char) => char.toUpperCase());
}

function emptyGraphView(): KnowledgeGraphView {
  return {
    depth: 0,
    edge_count: 0,
    edges: [],
    generated_at: new Date(0).toISOString(),
    node_count: 0,
    nodes: [],
    seed_node_ids: [],
  };
}

function edgeKey(edge: KnowledgeGraphEdge): string {
  return `${edge.source_node_id}::${edge.relation}::${edge.target_node_id}`;
}

// Deterministic force-directed (Fruchterman–Reingold) layout. Seeded on a circle so the
// result is stable across renders (no jitter), then relaxed: connected nodes attract,
// all nodes repel, so clusters separate instead of collapsing into one unreadable ring.
function graphLayout(
  nodes: KnowledgeGraphNode[],
  edges: KnowledgeGraphEdge[],
): Map<string, { x: number; y: number }> {
  const layout = new Map<string, { x: number; y: number }>();
  const n = nodes.length;
  if (n === 0) return layout;
  if (n === 1) {
    layout.set(nodes[0].node_id, { x: GRAPH_W / 2, y: GRAPH_H / 2 });
    return layout;
  }

  const pos = nodes.map((node, i) => {
    const angle = (i / n) * Math.PI * 2;
    return {
      id: node.node_id,
      x: GRAPH_W / 2 + Math.cos(angle) * 150,
      y: GRAPH_H / 2 + Math.sin(angle) * 110,
    };
  });
  const index = new Map(pos.map((p, i) => [p.id, i] as const));
  const links = edges
    .map((edge) => [index.get(edge.source_node_id), index.get(edge.target_node_id)] as const)
    .filter((pair): pair is readonly [number, number] => pair[0] !== undefined && pair[1] !== undefined);

  const k = Math.sqrt((GRAPH_W * GRAPH_H) / n) * 0.6; // ideal edge length
  let temp = GRAPH_W / 8;
  const iterations = n > 60 ? 240 : 340;

  for (let step = 0; step < iterations; step += 1) {
    const disp = pos.map(() => ({ x: 0, y: 0 }));
    for (let i = 0; i < n; i += 1) {
      for (let j = i + 1; j < n; j += 1) {
        const dx = pos[i].x - pos[j].x;
        const dy = pos[i].y - pos[j].y;
        const dist = Math.hypot(dx, dy) || 0.01;
        const force = (k * k) / dist;
        const ux = dx / dist;
        const uy = dy / dist;
        disp[i].x += ux * force;
        disp[i].y += uy * force;
        disp[j].x -= ux * force;
        disp[j].y -= uy * force;
      }
    }
    for (const [a, b] of links) {
      const dx = pos[a].x - pos[b].x;
      const dy = pos[a].y - pos[b].y;
      const dist = Math.hypot(dx, dy) || 0.01;
      const force = (dist * dist) / k;
      const ux = dx / dist;
      const uy = dy / dist;
      disp[a].x -= ux * force;
      disp[a].y -= uy * force;
      disp[b].x += ux * force;
      disp[b].y += uy * force;
    }
    for (let i = 0; i < n; i += 1) {
      const d = Math.hypot(disp[i].x, disp[i].y) || 0.01;
      pos[i].x += (disp[i].x / d) * Math.min(d, temp);
      pos[i].y += (disp[i].y / d) * Math.min(d, temp);
      pos[i].x += (GRAPH_W / 2 - pos[i].x) * 0.006; // gentle centering
      pos[i].y += (GRAPH_H / 2 - pos[i].y) * 0.006;
    }
    temp *= 0.985;
  }

  const pad = 56;
  const xs = pos.map((p) => p.x);
  const ys = pos.map((p) => p.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const scale = Math.min(
    (GRAPH_W - pad * 2) / Math.max(maxX - minX, 1),
    (GRAPH_H - pad * 2) / Math.max(maxY - minY, 1),
  );
  const offsetX = (GRAPH_W - (maxX - minX) * scale) / 2;
  const offsetY = (GRAPH_H - (maxY - minY) * scale) / 2;
  for (const p of pos) {
    layout.set(p.id, {
      x: offsetX + (p.x - minX) * scale,
      y: offsetY + (p.y - minY) * scale,
    });
  }
  return layout;
}

function nodeColor(nodeType: string): string {
  if (nodeType.includes("hpo")) return "#bae6fd";
  if (nodeType.includes("icd") || nodeType.includes("condition")) return "#bbf7d0";
  if (nodeType.includes("medication") || nodeType.includes("rxnorm")) return "#fde68a";
  if (nodeType.includes("observation") || nodeType.includes("loinc")) return "#ddd6fe";
  if (nodeType.includes("umls")) return "#fecaca";
  return "#e2e8f0";
}

function truncateLabel(value: string, limit: number): string {
  if (value.length <= limit) return value;
  return `${value.slice(0, Math.max(0, limit - 1))}...`;
}
