import * as React from "react";
import {
  BrainCircuit,
  Database,
  FileSearch,
  Gauge,
  ListFilter,
  Loader2,
  Network,
  RefreshCw,
  Search,
  ShieldCheck,
} from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Input, Label, Select, Textarea } from "../../components/ui/form";
import { PageHeader } from "../../components/layout/page-header";
import { Notice } from "../../components/ui/notice";
import { SummaryStrip, SummaryStripItem } from "../../components/ui/summary-strip";
import { Table, TBody, TD, TH, THead, TR } from "../../components/ui/table";
import {
  useRetrievalReindexMutation,
  useRetrievalSearchMutation,
  useRetrievalSourcesQuery,
  useRuntimeConfigQuery,
  useSchemasQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import { cn, humanize } from "../../lib/utils";
import type {
  Evidence,
  RetrievalGraphContext,
  RetrievalHit,
  RetrievalPackage,
  RetrievalSource,
  RuntimeConfig,
} from "../../types";

const defaultQuery = "HbA1c lab CSV missing units FHIR Observation";
const defaultFields = "date, patient_id, lab_name, value, unit";
const sourceTypeOptions = [
  "schema",
  "data_dictionary",
  "healthcare_standard",
  "terminology_system",
  "transformation_example",
  "tool_output",
];
const trustOptions = ["approved", "internal", "user_provided", "untrusted"];

export function RetrievalPage() {
  const sourcesQuery = useRetrievalSourcesQuery();
  const schemasQuery = useSchemasQuery();
  const runtimeQuery = useRuntimeConfigQuery();
  const searchMutation = useRetrievalSearchMutation();
  const reindexMutation = useRetrievalReindexMutation();
  const [query, setQuery] = React.useState(defaultQuery);
  const [fields, setFields] = React.useState(defaultFields);
  const [schemaId, setSchemaId] = React.useState("lab_result_v1");
  const [detectedFormat, setDetectedFormat] = React.useState("csv");
  const [resourceType, setResourceType] = React.useState("Observation");
  const [clinicalDomain, setClinicalDomain] = React.useState("laboratory");
  const [standardSystem, setStandardSystem] = React.useState("");
  const [trustLevel, setTrustLevel] = React.useState("approved");
  const [sourceType, setSourceType] = React.useState("");
  const [topK, setTopK] = React.useState(5);
  const [formError, setFormError] = React.useState<string | null>(null);

  const packageData = searchMutation.data;
  const sources = sourcesQuery.data ?? [];
  const domains = uniqueValues(sources.map((source) => source.clinical_domain));
  const standards = uniqueValues(sources.map((source) => source.standard_system));
  const graphContext = packageData?.handoff_context.graph_context;

  const runSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    const normalizedQuery = query.trim();
    if (!normalizedQuery) {
      setFormError("Enter a retrieval query before searching.");
      return;
    }
    setFormError(null);
    await searchMutation.mutateAsync({
      query: normalizedQuery,
      top_k: topK,
      schema_id: schemaId || null,
      fields: parseFields(fields),
      detected_format: detectedFormat || null,
      resource_type: resourceType || null,
      clinical_domain: clinicalDomain || null,
      standard_system: standardSystem || null,
      trust_level: trustLevel || null,
      source_type: sourceType || null,
      filters: {},
    });
  };

  const reindex = () => {
    reindexMutation.mutate({ include_seeded: true, include_corpus: true });
  };

  return (
    <div className="grid gap-5">
      <PageHeader
        action={
          <Button
            disabled={reindexMutation.isPending}
            onClick={reindex}
            type="button"
            variant="outline"
          >
            {reindexMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Reindex
          </Button>
        }
        title="Retrieval"
        description="Inspect trusted healthcare search, rank signals, source filters, and graph handoff."
      />

      <RetrievalSummary
        packageData={packageData}
        runtime={runtimeQuery.data}
        sources={sources}
        sourcesLoading={sourcesQuery.isLoading}
      />

      {sourcesQuery.isError ? (
        <Notice title="Retrieval sources could not be loaded" tone="danger">
          {workflowErrorMessage(sourcesQuery.error)}
        </Notice>
      ) : null}
      {reindexMutation.isError ? (
        <Notice title="Retrieval index could not be refreshed" tone="danger">
          {workflowErrorMessage(reindexMutation.error)}
        </Notice>
      ) : null}
      {reindexMutation.data ? (
        <Notice title="Retrieval index refreshed">
          {formatCount(reindexMutation.data.chunks_indexed, "chunk")} indexed with{" "}
          {String(reindexMutation.data.embedding?.provider ?? "configured")} embeddings.
        </Notice>
      ) : null}

      <div className="grid gap-5 xl:grid-cols-[minmax(360px,0.72fr)_minmax(0,1.28fr)]">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="border-b border-border bg-card/70">
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5 text-primary" />
              Query builder
            </CardTitle>
            <CardDescription>Search approved schema, terminology, and corpus evidence.</CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <form className="grid gap-4" onSubmit={(event) => void runSearch(event)}>
              {formError ? (
                <Notice title="Search blocked" tone="danger">
                  {formError}
                </Notice>
              ) : null}
              {searchMutation.isError ? (
                <Notice title="Search request failed" tone="danger">
                  {workflowErrorMessage(searchMutation.error)}
                </Notice>
              ) : null}

              <Label>
                Query
                <Textarea
                  className="min-h-24 resize-y"
                  onChange={(event) => {
                    setQuery(event.target.value);
                    if (formError) setFormError(null);
                  }}
                  value={query}
                />
              </Label>

              <Label>
                Fields
                <Textarea
                  className="min-h-16 resize-y"
                  onChange={(event) => setFields(event.target.value)}
                  value={fields}
                />
              </Label>

              <div className="grid gap-3 sm:grid-cols-2">
                <Label>
                  Schema
                  <Select onChange={(event) => setSchemaId(event.target.value)} value={schemaId}>
                    <option value="">Any schema</option>
                    {(schemasQuery.data ?? []).map((schema) => (
                      <option key={schema.schema_id} value={schema.schema_id}>
                        {schema.schema_id}
                      </option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Top K
                  <Select onChange={(event) => setTopK(Number(event.target.value))} value={topK}>
                    {[3, 5, 8, 10, 15, 20].map((value) => (
                      <option key={value} value={value}>{value}</option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Format
                  <Select onChange={(event) => setDetectedFormat(event.target.value)} value={detectedFormat}>
                    <option value="">Any format</option>
                    <option value="csv">CSV</option>
                    <option value="json">JSON</option>
                    <option value="yaml">YAML</option>
                    <option value="fhir_like">FHIR-like</option>
                  </Select>
                </Label>
                <Label>
                  Resource
                  <Input
                    onChange={(event) => setResourceType(event.target.value)}
                    placeholder="Observation"
                    value={resourceType}
                  />
                </Label>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <Label>
                  Domain
                  <Select onChange={(event) => setClinicalDomain(event.target.value)} value={clinicalDomain}>
                    <option value="">Any domain</option>
                    {domains.map((domain) => (
                      <option key={domain} value={domain}>{humanize(domain)}</option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Standard
                  <Select onChange={(event) => setStandardSystem(event.target.value)} value={standardSystem}>
                    <option value="">Any standard</option>
                    {standards.map((standard) => (
                      <option key={standard} value={standard}>{standard}</option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Trust
                  <Select onChange={(event) => setTrustLevel(event.target.value)} value={trustLevel}>
                    <option value="">Any trust</option>
                    {trustOptions.map((trust) => (
                      <option key={trust} value={trust}>{humanize(trust)}</option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Source type
                  <Select onChange={(event) => setSourceType(event.target.value)} value={sourceType}>
                    <option value="">Any source</option>
                    {sourceTypeOptions.map((type) => (
                      <option key={type} value={type}>{humanize(type)}</option>
                    ))}
                  </Select>
                </Label>
              </div>

              <Button disabled={searchMutation.isPending} type="submit">
                {searchMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileSearch className="h-4 w-4" />
                )}
                Search evidence
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="grid min-w-0 gap-5">
          <SearchResults packageData={packageData} />
          <div className="grid min-w-0 gap-5 2xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.9fr)]">
            <TracePanel packageData={packageData} />
            <GraphPanel graphContext={graphContext} />
          </div>
          <SourcesPanel isLoading={sourcesQuery.isLoading} sources={sources} />
        </div>
      </div>
    </div>
  );
}

function RetrievalSummary({
  packageData,
  runtime,
  sources,
  sourcesLoading,
}: {
  packageData: RetrievalPackage | undefined;
  runtime: RuntimeConfig | undefined;
  sources: RetrievalSource[];
  sourcesLoading: boolean;
}) {
  const graph = packageData?.handoff_context.graph_context;
  const packageRuntime = packageData ? rankingStackFromPackage(packageData) : null;
  const rerankerEnabled = Boolean(
    packageRuntime?.reranker.enabled ?? runtime?.rerank?.enabled,
  );
  const embeddingProvider = packageRuntime?.embedding.provider ?? runtime?.embedding.provider;
  const rerankerProvider = packageRuntime?.reranker.provider ?? runtime?.rerank?.provider;
  return (
    <SummaryStrip columns={5}>
      <SummaryStripItem
        icon={Database}
        label="Sources"
        loading={sourcesLoading}
        supporting="Trusted retrieval inventory"
        value={sources.length}
      />
      <SummaryStripItem
        icon={Gauge}
        label="Hits"
        supporting={packageData ? packageData.trace.strategy : "No search yet"}
        tone="info"
        value={packageData?.hits.length ?? 0}
      />
      <SummaryStripItem
        icon={ShieldCheck}
        label="Safety flags"
        supporting="Prompt and sensitive-context flags"
        tone={packageData?.trace.safety_flags.length ? "warning" : "success"}
        value={packageData?.trace.safety_flags.length ?? 0}
      />
      <SummaryStripItem
        icon={Network}
        label="Graph nodes"
        supporting={embeddingProvider ? `${embeddingProvider} embeddings` : "Runtime loading"}
        tone="success"
        value={graph?.nodes.length ?? 0}
      />
      <SummaryStripItem
        icon={BrainCircuit}
        label="Reranker"
        supporting={
          rerankerProvider
            ? rerankerEnabled
              ? `${rerankerProvider} second stage`
              : `${rerankerProvider} disabled`
            : "Runtime loading"
        }
        tone={rerankerEnabled ? "success" : "neutral"}
        value={rerankerEnabled ? "on" : "off"}
      />
    </SummaryStrip>
  );
}

function SearchResults({ packageData }: { packageData: RetrievalPackage | undefined }) {
  if (!packageData) {
    return (
      <Card className="min-w-0 overflow-hidden">
        <CardHeader className="border-b border-border bg-card/70">
          <CardTitle>Ranked evidence</CardTitle>
          <CardDescription>Run a search to inspect score components and provenance.</CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <Notice title="No search executed">
            Use the query builder to retrieve trusted healthcare evidence.
          </Notice>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70">
        <div>
          <CardTitle>Ranked evidence</CardTitle>
          <CardDescription>
            {formatCount(packageData.hits.length, "hit")} from{" "}
            {formatCount(packageData.trace.candidates_seen, "candidate")}
          </CardDescription>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant="muted">{packageData.trace.strategy}</Badge>
          <RerankBadge packageData={packageData} />
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        {packageData.hits.map((hit, index) => (
          <HitCard hit={hit} index={index} key={hit.evidence.evidence_id} />
        ))}
        {!packageData.hits.length ? (
          <Notice title="No matching evidence">
            Adjust filters or reindex the trusted corpus.
          </Notice>
        ) : null}
      </CardContent>
    </Card>
  );
}

function HitCard({ hit, index }: { hit: RetrievalHit; index: number }) {
  const evidence = hit.evidence;
  return (
    <article className="grid min-w-0 gap-3 rounded-md border border-border bg-card p-3 shadow-sm">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-bold uppercase text-muted-foreground">Rank {index + 1}</div>
          <h3 className="mt-1 break-words text-base font-extrabold leading-5">
            {evidence.source_id}
          </h3>
          <div className="mt-1 flex flex-wrap gap-1.5 text-xs font-bold text-muted-foreground">
            <span>{humanize(evidence.source_type)}</span>
            <span>/</span>
            <span>{humanize(evidence.trust_level)}</span>
            {String(evidence.locator.standard_system ?? "") ? (
              <>
                <span>/</span>
                <span>{String(evidence.locator.standard_system)}</span>
              </>
            ) : null}
          </div>
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          <Badge variant="success">{formatConfidence(evidence.confidence)}</Badge>
          <Badge variant="muted">score {formatScore(hit.score)}</Badge>
        </div>
      </div>

      <p className="break-words text-sm leading-6">{formatClaim(evidence.claim)}</p>

      <div className="grid gap-2 md:grid-cols-3">
        <ScoreMeter label="Lexical" value={hit.lexical_score} />
        <ScoreMeter label="Vector" value={hit.vector_score} />
        <ScoreMeter label="Rerank" value={hit.rerank_score} />
      </div>

      <div className="flex min-w-0 flex-wrap gap-1.5">
        {hit.matched_terms.slice(0, 12).map((term) => (
          <span
            className="max-w-full break-words rounded-full bg-muted px-2 py-1 text-xs font-bold text-muted-foreground"
            key={term}
          >
            {term}
          </span>
        ))}
        {!hit.matched_terms.length ? (
          <span className="text-xs font-semibold text-muted-foreground">No exact terms matched.</span>
        ) : null}
      </div>

      <details className="rounded-md border border-border bg-muted/20 p-2 text-xs">
        <summary className="cursor-pointer font-bold">Locator and evidence ID</summary>
        <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words font-mono">
          {JSON.stringify(
            {
              evidence_id: evidence.evidence_id,
              locator: evidence.locator,
              source_locator: hit.source_locator,
            },
            null,
            2,
          )}
        </pre>
      </details>
    </article>
  );
}

function ScoreMeter({ label, value }: { label: string; value: number }) {
  const normalized = Math.max(0, Math.min(100, Math.abs(value) * 100));
  return (
    <div className="grid gap-1 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex items-center justify-between gap-2 text-xs font-bold">
        <span>{label}</span>
        <span className="tabular-nums text-muted-foreground">{formatScore(value)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-border">
        <div className="h-full rounded-full bg-primary" style={{ width: `${normalized}%` }} />
      </div>
    </div>
  );
}

function TracePanel({ packageData }: { packageData: RetrievalPackage | undefined }) {
  const trace = packageData?.trace;
  const stack = packageData ? rankingStackFromPackage(packageData) : null;
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle className="flex items-center gap-2">
          <ListFilter className="h-5 w-5 text-primary" />
          Retrieval trace
        </CardTitle>
        <CardDescription>Query variants, filters, warnings, and safety flags.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        {!trace ? (
          <Notice title="Trace unavailable">Run a search to inspect the trace.</Notice>
        ) : (
          <>
            <TraceFact label="Strategy" value={trace.strategy} />
            <TraceFact label="Candidates" value={String(trace.candidates_seen)} />
            <TraceFact
              label="Embedding"
              value={stack ? formatEmbeddingStack(stack) : "unknown"}
            />
            <TraceFact
              label="Reranker"
              value={stack ? formatRerankerStack(stack) : "unknown"}
            />
            <TraceFact
              label="Filters"
              value={Object.keys(trace.filters_applied).length ? JSON.stringify(trace.filters_applied) : "none"}
            />
            <TokenList items={trace.query_variants} title="Query variants" />
            <TokenList items={trace.safety_flags.map(humanize)} title="Safety flags" tone="warning" />
            <TokenList items={trace.warnings} title="Warnings" tone="warning" />
          </>
        )}
      </CardContent>
    </Card>
  );
}

function RerankBadge({ packageData }: { packageData: RetrievalPackage }) {
  const stack = rankingStackFromPackage(packageData);
  if (!stack.reranker.enabled) {
    return <Badge variant="muted">first stage only</Badge>;
  }
  return <Badge variant="success">reranked</Badge>;
}

function GraphPanel({ graphContext }: { graphContext: RetrievalGraphContext | undefined }) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5 text-primary" />
          Graph handoff
        </CardTitle>
        <CardDescription>Entity and evidence triples prepared for Graph-NER/RAG.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        {!graphContext ? (
          <Notice title="Graph context unavailable">
            Run a search to inspect graph handoff context.
          </Notice>
        ) : (
          <>
            <div className="grid gap-2 text-sm sm:grid-cols-3">
              <GraphCounter label="Nodes" value={graphContext.nodes.length} />
              <GraphCounter label="Edges" value={graphContext.edges.length} />
              <GraphCounter label="Triples" value={graphContext.triples.length} />
            </div>
            <div className="grid gap-2">
              <div className="text-xs font-bold uppercase text-muted-foreground">
                {graphContext.graph_contract}
              </div>
              {graphContext.triples.slice(0, 8).map((triple, index) => (
                <div
                  className="grid gap-1 rounded-md border border-border bg-muted/20 p-2 text-sm"
                  key={`${triple.subject}-${triple.object}-${index}`}
                >
                  <div className="break-words font-bold">{triple.subject}</div>
                  <div className="break-words text-muted-foreground">
                    {triple.predicate} / {triple.object}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function SourcesPanel({
  isLoading,
  sources,
}: {
  isLoading: boolean;
  sources: RetrievalSource[];
}) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle>Trusted sources</CardTitle>
        <CardDescription>{isLoading ? "Loading inventory" : formatCount(sources.length, "source")}</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="grid gap-3 md:hidden">
          {sources.map((source) => (
            <SourceCard key={source.source_id} source={source} />
          ))}
          {!sources.length ? (
            <div className="rounded-md border border-border p-3 text-sm text-muted-foreground">
              {isLoading ? "Loading sources." : "No retrieval sources indexed."}
            </div>
          ) : null}
        </div>
        <Table wrapperClassName="hidden md:block">
          <THead>
            <TR>
              <TH>Source</TH>
              <TH>Type</TH>
              <TH>Domain</TH>
              <TH>Standard</TH>
              <TH>Chunks</TH>
            </TR>
          </THead>
          <TBody>
            {sources.map((source) => (
              <TR key={source.source_id}>
                <TD className="min-w-64">
                  <div className="break-words font-bold">{source.title}</div>
                  <div className="break-all font-mono text-xs text-muted-foreground">{source.source_id}</div>
                </TD>
                <TD>{humanize(source.source_type)}</TD>
                <TD>{source.clinical_domain ? humanize(source.clinical_domain) : "-"}</TD>
                <TD>{source.standard_system ?? "-"}</TD>
                <TD className="tabular-nums">{source.chunk_count}</TD>
              </TR>
            ))}
            {!sources.length ? (
              <TR>
                <TD colSpan={5}>{isLoading ? "Loading sources." : "No retrieval sources indexed."}</TD>
              </TR>
            ) : null}
          </TBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function SourceCard({ source }: { source: RetrievalSource }) {
  return (
    <article className="grid gap-2 rounded-md border border-border bg-muted/20 p-3 text-sm">
      <div className="min-w-0">
        <div className="break-words font-bold">{source.title}</div>
        <div className="break-all font-mono text-xs text-muted-foreground">
          {source.source_id}
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
          {humanize(source.source_type)}
        </span>
        {source.clinical_domain ? (
          <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
            {humanize(source.clinical_domain)}
          </span>
        ) : null}
        {source.standard_system ? (
          <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
            {source.standard_system}
          </span>
        ) : null}
        <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
          {formatCount(source.chunk_count, "chunk")}
        </span>
      </div>
    </article>
  );
}

function TokenList({
  items,
  title,
  tone = "neutral",
}: {
  items: string[];
  title: string;
  tone?: "neutral" | "warning";
}) {
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">{title}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {items.map((item) => (
          <span
            className={cn(
              "max-w-full break-words rounded-full px-2 py-1 text-xs font-bold",
              tone === "warning"
                ? "bg-amber-100 text-amber-900"
                : "bg-muted text-muted-foreground",
            )}
            key={item}
          >
            {item}
          </span>
        ))}
        {!items.length ? (
          <span className="text-xs font-semibold text-muted-foreground">none</span>
        ) : null}
      </div>
    </div>
  );
}

function TraceFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[7rem_minmax(0,1fr)] gap-3 text-sm">
      <span className="font-bold text-muted-foreground">{label}</span>
      <span className="break-words">{value}</span>
    </div>
  );
}

function GraphCounter({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-black tabular-nums">{value}</div>
    </div>
  );
}

type RankingStack = {
  embedding: {
    dimensions: number | null;
    model: string;
    provider: string;
  };
  reranker: {
    device: string | null;
    enabled: boolean;
    model: string;
    provider: string;
  };
};

function rankingStackFromPackage(packageData: RetrievalPackage): RankingStack {
  const embedding = recordValue(packageData.handoff_context.embedding);
  const reranker = recordValue(packageData.handoff_context.reranker);
  const rerankerProvider = stringValue(reranker.provider, "none");
  return {
    embedding: {
      dimensions: numberValue(embedding.dimensions),
      model: stringValue(embedding.model, "unknown"),
      provider: stringValue(embedding.provider, "unknown"),
    },
    reranker: {
      device: optionalStringValue(reranker.device),
      enabled: booleanValue(reranker.enabled) && rerankerProvider !== "none",
      model: stringValue(reranker.model, "none"),
      provider: rerankerProvider,
    },
  };
}

function formatEmbeddingStack(stack: RankingStack): string {
  const dimensions = stack.embedding.dimensions ? ` / ${stack.embedding.dimensions}d` : "";
  return `${stack.embedding.provider} / ${stack.embedding.model}${dimensions}`;
}

function formatRerankerStack(stack: RankingStack): string {
  if (!stack.reranker.enabled) {
    return `${stack.reranker.provider} disabled`;
  }
  const device = stack.reranker.device ? ` / ${stack.reranker.device}` : "";
  return `${stack.reranker.provider} / ${stack.reranker.model}${device}`;
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function booleanValue(value: unknown): boolean {
  return value === true;
}

function parseFields(value: string) {
  return value
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
}

function formatClaim(claim: string) {
  return claim
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[ \t]+/g, " ")
    .trim();
}

function formatConfidence(confidence: Evidence["confidence"]) {
  return typeof confidence === "number" ? `${Math.round(confidence * 100)}%` : "n/a";
}

function formatScore(score: number) {
  return score.toFixed(3);
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
