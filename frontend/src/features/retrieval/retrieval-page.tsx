import * as React from "react";
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
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
  useRetrievalIntegrityQuery,
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
  RetrievalIntegrityReport,
  RetrievalPackage,
  RetrievalCoverage,
  RetrievalFacets,
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
  const [includeCorpusIntegrity, setIncludeCorpusIntegrity] = React.useState(false);
  const integrityQuery = useRetrievalIntegrityQuery({
    include_seeded: true,
    include_corpus: includeCorpusIntegrity,
  });
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
      {integrityQuery.isError ? (
        <Notice title="Retrieval integrity could not be checked" tone="danger">
          {workflowErrorMessage(integrityQuery.error)}
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
          <IntegrityPanel
            includeCorpus={includeCorpusIntegrity}
            isFetching={integrityQuery.isFetching}
            onRefresh={() => void integrityQuery.refetch()}
            onToggleCorpus={() => setIncludeCorpusIntegrity((current) => !current)}
            report={integrityQuery.data}
          />
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
  const diversity = packageData ? diversityFromPackage(packageData) : null;
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
        label="Coverage"
        supporting={
          diversity
            ? `${diversity.selectedSourceCount} selected unique sources`
            : embeddingProvider
              ? `${embeddingProvider} embeddings`
              : "Runtime loading"
        }
        tone="success"
        value={diversity ? formatSourceCoverage(diversity) : graph?.nodes.length ?? 0}
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
          <DiversityBadge packageData={packageData} />
          <RerankBadge packageData={packageData} />
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        <ResultFacets facets={packageData.facets} />
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

function ResultFacets({ facets }: { facets: RetrievalFacets | null | undefined }) {
  if (!facets) return null;
  const sections = [
    { label: "Source type", values: facets.source_type, formatter: humanize },
    { label: "Domain", values: facets.clinical_domain, formatter: humanize },
    { label: "Standard", values: facets.standard_system, formatter: (value: string) => value },
    { label: "Trust", values: facets.trust_level, formatter: humanize },
  ].filter((section) => section.values.length > 0);
  if (!sections.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Result facets
      </div>
      <div className="grid gap-2 lg:grid-cols-2">
        {sections.map((section) => (
          <div className="grid gap-1.5" key={section.label}>
            <div className="text-xs font-bold text-muted-foreground">{section.label}</div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {section.values.map((bucket) => (
                <span
                  className="inline-flex max-w-full items-center gap-1 rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground"
                  key={`${section.label}-${bucket.value}`}
                >
                  <span className="break-words">{section.formatter(bucket.value)}</span>
                  <span className="tabular-nums text-foreground">{bucket.count}</span>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
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

      {hit.snippet ? <SnippetBlock snippet={hit.snippet} /> : null}

      <p className="break-words text-sm leading-6 text-muted-foreground">
        {formatClaim(evidence.claim)}
      </p>

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

function SnippetBlock({ snippet }: { snippet: NonNullable<RetrievalHit["snippet"]> }) {
  return (
    <div className="grid gap-2 rounded-md border border-primary/20 bg-primary/5 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-bold uppercase text-primary">Best snippet</span>
        <span className="font-mono text-xs font-semibold text-muted-foreground">
          {snippet.start_char}-{snippet.end_char}
        </span>
      </div>
      <p className="break-words text-sm leading-6">
        <HighlightedText terms={snippet.matched_terms} text={formatClaim(snippet.text)} />
      </p>
    </div>
  );
}

function HighlightedText({ text, terms }: { text: string; terms: string[] }) {
  const parts = highlightedParts(text, terms);
  return (
    <>
      {parts.map((part, index) =>
        part.highlight ? (
          <mark
            className="rounded bg-amber-100 px-0.5 font-bold text-amber-950"
            key={`${part.text}-${index}`}
          >
            {part.text}
          </mark>
        ) : (
          <React.Fragment key={`${part.text}-${index}`}>{part.text}</React.Fragment>
        ),
      )}
    </>
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
  const diversity = packageData ? diversityFromPackage(packageData) : null;
  const queryAnalysis = packageData ? queryAnalysisFromPackage(packageData) : null;
  const coverage = packageData?.coverage;
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
              label="Diversity"
              value={diversity ? formatDiversityTrace(diversity) : "unknown"}
            />
            <TraceFact
              label="Filters"
              value={Object.keys(trace.filters_applied).length ? JSON.stringify(trace.filters_applied) : "none"}
            />
            <QueryAnalysisBlock analysis={queryAnalysis} />
            <CoverageDiagnosticsBlock coverage={coverage} />
            <TokenList items={trace.query_variants} title="Query variants" />
            <TokenList items={trace.safety_flags.map(humanize)} title="Safety flags" tone="warning" />
            <TokenList items={trace.warnings} title="Warnings" tone="warning" />
          </>
        )}
      </CardContent>
    </Card>
  );
}

function CoverageDiagnosticsBlock({
  coverage,
}: {
  coverage: RetrievalCoverage | null | undefined;
}) {
  const items = coverage?.standard_system ?? [];
  const warningCount = coverage?.warnings.length ?? 0;
  if (!items.length) {
    return <TokenList items={[]} title="Standard coverage" />;
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Standard coverage
        </div>
        <Badge variant={warningCount ? "warning" : "success"}>
          {warningCount ? `${warningCount} gap` : "covered"}
        </Badge>
      </div>
      <div className="grid gap-2">
        {items.map((item) => (
          <div
            className="grid gap-1 rounded-md border border-border bg-card p-2 text-xs"
            key={`${item.field}-${item.value}`}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{item.value}</span>
              <Badge variant={item.status === "covered" ? "success" : "warning"}>
                {item.status} / {item.selected_count}
              </Badge>
            </div>
            <div className="break-words text-muted-foreground">{item.reason}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function QueryAnalysisBlock({
  analysis,
}: {
  analysis: QueryAnalysisStack | null;
}) {
  if (!analysis) {
    return <TraceFact label="Query analysis" value="unavailable" />;
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Query analysis
        </div>
        <Badge variant="muted">{analysis.strategy}</Badge>
      </div>
      <div className="grid gap-2 text-xs sm:grid-cols-4">
        <QueryAnalysisCounter label="Concepts" value={analysis.detectedConcepts.length} />
        <QueryAnalysisCounter label="Standards" value={analysis.standards.length} />
        <QueryAnalysisCounter label="Rules" value={analysis.ruleIds.length} />
        <QueryAnalysisCounter label="Variants" value={analysis.variantCount} />
      </div>
      <QueryDiagnosticList diagnostics={analysis.diagnostics} />
      <ConceptCandidateList candidates={analysis.conceptCandidates} />
      <SearchHintList hints={analysis.searchHints} />
      <TokenList items={analysis.detectedConcepts.map(humanize)} title="Detected concepts" />
      <TokenList items={analysis.standards} title="Standard cues" />
      <FilterSuggestionList suggestions={analysis.filterSuggestions} />
      <TokenList items={analysis.expandedTerms} title="Expanded terms" />
    </div>
  );
}

function ConceptCandidateList({
  candidates,
}: {
  candidates: ConceptCandidateStack[];
}) {
  if (!candidates.length) {
    return <TokenList items={[]} title="Concept candidates" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Concept candidates
      </div>
      <div className="grid gap-2">
        {candidates.map((candidate) => (
          <div
            className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
            key={`${candidate.standardSystem}-${candidate.code}-${candidate.conceptId}`}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{candidate.displayName}</span>
              <Badge variant="success">
                {candidate.standardSystem}
                {candidate.code ? ` ${candidate.code}` : ""}
              </Badge>
            </div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              <span className="rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground">
                {humanize(candidate.clinicalDomain ?? "unknown")}
              </span>
              <span className="rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground">
                {Math.round(candidate.confidence * 100)}%
              </span>
              {candidate.matchedAliases.slice(0, 4).map((alias) => (
                <span
                  className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                  key={`${candidate.conceptId}-${alias}`}
                >
                  {alias}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SearchHintList({ hints }: { hints: SearchHintStack[] }) {
  if (!hints.length) {
    return <TokenList items={[]} title="Medical search hints" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Medical search hints
      </div>
      <div className="grid gap-2">
        {hints.map((hint) => (
          <div
            className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
            key={`${hint.target}-${hint.query}`}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{humanize(hint.target)}</span>
              <Badge variant="muted">syntax hint</Badge>
            </div>
            <code className="block max-h-24 overflow-auto break-words rounded bg-muted px-2 py-1 font-mono text-xs">
              {hint.query}
            </code>
            <div className="break-words text-muted-foreground">{hint.rationale}</div>
            {hint.warnings.length ? (
              <TokenList items={hint.warnings} title="Hint warnings" tone="warning" />
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function QueryDiagnosticList({
  diagnostics,
}: {
  diagnostics: QueryDiagnosticStack[];
}) {
  if (!diagnostics.length) {
    return <TokenList items={[]} title="Query diagnostics" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Query diagnostics
      </div>
      <div className="grid gap-2">
        {diagnostics.map((diagnostic) => (
          <div
            className="grid gap-1 rounded-md border border-border bg-card p-2 text-xs"
            key={diagnostic.code}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{humanize(diagnostic.code)}</span>
              <Badge variant={diagnosticBadgeVariant(diagnostic.severity)}>
                {humanize(diagnostic.severity)}
              </Badge>
            </div>
            <div className="break-words text-muted-foreground">{diagnostic.message}</div>
            <div className="break-words font-semibold text-foreground">
              {diagnostic.suggestedAction}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FilterSuggestionList({
  suggestions,
}: {
  suggestions: FilterSuggestionStack[];
}) {
  if (!suggestions.length) {
    return <TokenList items={[]} title="Suggested filters" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Suggested filters
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {suggestions.map((suggestion) => (
          <span
            className={cn(
              "inline-flex max-w-full items-center gap-1 rounded-full px-2 py-1 text-xs font-bold",
              suggestion.applied
                ? "bg-emerald-100 text-emerald-900"
                : "bg-card text-muted-foreground",
            )}
            key={`${suggestion.field}-${suggestion.value}`}
            title={suggestion.reason}
          >
            <span className="break-words">
              {humanize(suggestion.field)}={humanize(suggestion.value)}
            </span>
            <span className="tabular-nums">
              {Math.round(suggestion.confidence * 100)}%
            </span>
            {suggestion.applied ? <span>applied</span> : null}
          </span>
        ))}
      </div>
    </div>
  );
}

function QueryAnalysisCounter({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-card px-2 py-1.5">
      <div className="font-bold text-muted-foreground">{label}</div>
      <div className="text-base font-black tabular-nums">{value}</div>
    </div>
  );
}

function DiversityBadge({ packageData }: { packageData: RetrievalPackage }) {
  const diversity = diversityFromPackage(packageData);
  if (!diversity.enabled) {
    return <Badge variant="muted">score order</Badge>;
  }
  return <Badge variant="success">{formatSourceCoverage(diversity)} sources</Badge>;
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

function IntegrityPanel({
  includeCorpus,
  isFetching,
  onRefresh,
  onToggleCorpus,
  report,
}: {
  includeCorpus: boolean;
  isFetching: boolean;
  onRefresh: () => void;
  onToggleCorpus: () => void;
  report: RetrievalIntegrityReport | undefined;
}) {
  const status = report?.status ?? "loading";
  const checks = report ? prioritizedIntegrityChecks(report) : [];
  const hasWarnings = Boolean(report?.warnings.length);
  const StatusIcon = status === "ok" ? CheckCircle2 : AlertTriangle;

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70">
        <div className="min-w-0">
          <CardTitle className="flex items-center gap-2">
            <StatusIcon
              className={cn(
                "h-5 w-5",
                status === "ok" ? "text-emerald-700" : "text-amber-700",
              )}
            />
            Index integrity
          </CardTitle>
          <CardDescription>
            {report
              ? `${report.repository} / ${report.checked_scope}`
              : "Checking indexed knowledge consistency"}
          </CardDescription>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Button onClick={onToggleCorpus} size="sm" type="button" variant="outline">
            <Database className="h-4 w-4" />
            {includeCorpus ? "Corpus on" : "Seeded only"}
          </Button>
          <Button disabled={isFetching} onClick={onRefresh} size="sm" type="button" variant="outline">
            {isFetching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 pt-4">
        {!report ? (
          <Notice title="Integrity check running">
            The app is checking trusted source hashes against the active index.
          </Notice>
        ) : (
          <>
            <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-6">
              <IntegrityMetric
                label="Status"
                tone={integrityBadgeVariant(report.status)}
                value={humanize(report.status)}
              />
              <IntegrityMetric label="Expected" value={report.expected_source_count} />
              <IntegrityMetric label="Indexed" value={report.indexed_source_count} />
              <IntegrityMetric label="OK" tone="success" value={report.ok_count} />
              <IntegrityMetric label="Stale" tone={report.stale_count ? "warning" : "muted"} value={report.stale_count} />
              <IntegrityMetric label="Missing" tone={report.missing_count ? "destructive" : "muted"} value={report.missing_count} />
            </div>

            {hasWarnings ? (
              <TokenList items={report.warnings} title="Integrity warnings" tone="warning" />
            ) : (
              <TokenList items={[]} title="Integrity warnings" />
            )}

            <div className="grid gap-2">
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <div className="text-xs font-bold uppercase text-muted-foreground">
                  Source checks
                </div>
                <Badge variant={report.extra_count ? "warning" : "muted"}>
                  {formatCount(report.extra_count, "extra source")}
                </Badge>
              </div>
              <div className="grid gap-2">
                {checks.map((check) => (
                  <div
                    className="grid gap-2 rounded-md border border-border bg-muted/20 p-3 text-sm"
                    key={check.source_id}
                  >
                    <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="break-all font-mono text-xs font-bold">
                          {check.source_id}
                        </div>
                        <div className="mt-1 break-words text-xs text-muted-foreground">
                          {check.message}
                        </div>
                      </div>
                      <Badge variant={integrityBadgeVariant(check.status)}>
                        {humanize(check.status)}
                      </Badge>
                    </div>
                    <div className="grid gap-2 text-xs sm:grid-cols-4">
                      <IntegrityFact label="Expected" value={`${check.expected_chunk_count}`} />
                      <IntegrityFact label="Indexed" value={`${check.indexed_chunk_count}`} />
                      <IntegrityFact label="Expected hash" value={shortHash(check.expected_hash)} />
                      <IntegrityFact label="Indexed hash" value={shortHash(check.indexed_hash)} />
                    </div>
                  </div>
                ))}
                {!checks.length ? (
                  <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                    No source checks returned.
                  </div>
                ) : null}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function IntegrityMetric({
  label,
  tone = "muted",
  value,
}: {
  label: string;
  tone?: "default" | "success" | "warning" | "destructive" | "muted";
  value: number | string;
}) {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 min-w-0">
        {typeof value === "string" ? (
          <Badge variant={tone}>{value}</Badge>
        ) : (
          <span className={cn("text-lg font-black tabular-nums", integrityMetricToneClass(tone))}>
            {value}
          </span>
        )}
      </div>
    </div>
  );
}

function IntegrityFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md border border-border bg-card p-2">
      <div className="font-bold text-muted-foreground">{label}</div>
      <div className="break-all font-mono font-semibold">{value}</div>
    </div>
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

type DiversityStack = {
  candidateSourceCount: number;
  duplicateSelectedSourceCount: number;
  enabled: boolean;
  lambda: number | null;
  selectedSourceCount: number;
  selectionMode: string;
};

type QueryAnalysisStack = {
  conceptCandidates: ConceptCandidateStack[];
  detectedConcepts: string[];
  diagnostics: QueryDiagnosticStack[];
  expandedTerms: string[];
  filterSuggestions: FilterSuggestionStack[];
  ruleIds: string[];
  searchHints: SearchHintStack[];
  standards: string[];
  strategy: string;
  variantCount: number;
};

type ConceptCandidateStack = {
  clinicalDomain: string | null;
  code: string | null;
  conceptId: string;
  confidence: number;
  displayName: string;
  matchedAliases: string[];
  standardSystem: string;
};

type SearchHintStack = {
  query: string;
  rationale: string;
  target: string;
  warnings: string[];
};

type QueryDiagnosticStack = {
  code: string;
  message: string;
  severity: string;
  suggestedAction: string;
};

type FilterSuggestionStack = {
  applied: boolean;
  confidence: number;
  field: string;
  reason: string;
  value: string;
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

function queryAnalysisFromPackage(packageData: RetrievalPackage): QueryAnalysisStack {
  const queryAnalysis = recordValue(packageData.handoff_context.query_analysis);
  return {
    conceptCandidates: conceptCandidatesValue(queryAnalysis.concept_candidates),
    detectedConcepts: stringArrayValue(queryAnalysis.detected_concepts),
    diagnostics: queryDiagnosticsValue(queryAnalysis.diagnostics),
    expandedTerms: stringArrayValue(queryAnalysis.expanded_terms),
    filterSuggestions: filterSuggestionsValue(queryAnalysis.filter_suggestions),
    ruleIds: stringArrayValue(queryAnalysis.rule_ids),
    searchHints: searchHintsValue(queryAnalysis.search_hints),
    standards: stringArrayValue(queryAnalysis.standards),
    strategy: stringValue(queryAnalysis.strategy, "unknown"),
    variantCount: stringArrayValue(queryAnalysis.query_variants).length,
  };
}

function diversityFromPackage(packageData: RetrievalPackage): DiversityStack {
  const diversity = recordValue(packageData.handoff_context.diversity);
  return {
    candidateSourceCount: numberValue(diversity.candidate_source_count) ?? 0,
    duplicateSelectedSourceCount:
      numberValue(diversity.duplicate_selected_source_count) ?? 0,
    enabled: booleanValue(diversity.enabled),
    lambda: numberValue(diversity.lambda),
    selectedSourceCount: numberValue(diversity.selected_source_count) ?? 0,
    selectionMode: stringValue(diversity.selection_mode, "unknown"),
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

function formatSourceCoverage(diversity: DiversityStack): string {
  return `${diversity.selectedSourceCount}/${diversity.candidateSourceCount}`;
}

function formatDiversityTrace(diversity: DiversityStack): string {
  const lambda = diversity.lambda === null ? "n/a" : diversity.lambda.toFixed(2);
  const duplicateText = `${diversity.duplicateSelectedSourceCount} duplicate selected`;
  return `${diversity.selectionMode} / lambda ${lambda} / ${formatSourceCoverage(diversity)} sources / ${duplicateText}`;
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

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function conceptCandidatesValue(value: unknown): ConceptCandidateStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      clinicalDomain: optionalStringValue(item.clinical_domain),
      code: optionalStringValue(item.code),
      conceptId: stringValue(item.concept_id, "concept"),
      confidence: numberValue(item.confidence) ?? 0,
      displayName: stringValue(item.display_name, "Unknown concept"),
      matchedAliases: stringArrayValue(item.matched_aliases),
      standardSystem: stringValue(item.standard_system, "unknown"),
    }))
    .filter((item) => item.conceptId !== "concept" && item.standardSystem !== "unknown");
}

function filterSuggestionsValue(value: unknown): FilterSuggestionStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      applied: booleanValue(item.applied),
      confidence: numberValue(item.confidence) ?? 0,
      field: stringValue(item.field, "filter"),
      reason: stringValue(item.reason, "Suggested by query analysis."),
      value: stringValue(item.value, "unknown"),
    }))
    .filter((item) => item.field !== "filter" && item.value !== "unknown");
}

function queryDiagnosticsValue(value: unknown): QueryDiagnosticStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      code: stringValue(item.code, "query_diagnostic"),
      message: stringValue(item.message, "Query diagnostic unavailable."),
      severity: stringValue(item.severity, "info"),
      suggestedAction: stringValue(item.suggested_action, "Review the retrieval query."),
    }))
    .filter((item) => item.code !== "query_diagnostic");
}

function searchHintsValue(value: unknown): SearchHintStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      query: stringValue(item.query, ""),
      rationale: stringValue(item.rationale, "Generated from deterministic query analysis."),
      target: stringValue(item.target, "medical_search"),
      warnings: stringArrayValue(item.warnings),
    }))
    .filter((item) => item.query.length > 0 && item.target !== "medical_search");
}

function diagnosticBadgeVariant(
  severity: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (severity === "warning") return "warning";
  if (severity === "error") return "destructive";
  if (severity === "info") return "muted";
  return "default";
}

function integrityBadgeVariant(
  status: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (status === "ok") return "success";
  if (status === "missing") return "destructive";
  if (status === "stale" || status === "extra" || status === "warning") return "warning";
  if (status === "loading") return "muted";
  return "default";
}

function integrityMetricToneClass(
  tone: "default" | "success" | "warning" | "destructive" | "muted",
) {
  if (tone === "success") return "text-emerald-800";
  if (tone === "warning") return "text-amber-800";
  if (tone === "destructive") return "text-red-800";
  return "text-foreground";
}

function prioritizedIntegrityChecks(report: RetrievalIntegrityReport) {
  const nonOk = report.checks.filter((check) => check.status !== "ok");
  const source = nonOk.length ? nonOk : report.checks;
  return source.slice(0, nonOk.length ? 12 : 8);
}

function shortHash(value: string | null | undefined) {
  return value ? value.slice(0, 12) : "-";
}

function highlightedParts(text: string, terms: string[]) {
  const normalizedTerms = Array.from(
    new Set(
      terms
        .map((term) => term.trim())
        .filter((term) => term.length > 1)
        .sort((left, right) => right.length - left.length),
    ),
  );
  if (!normalizedTerms.length) {
    return [{ text, highlight: false }];
  }
  const pattern = new RegExp(`(${normalizedTerms.map(escapeRegExp).join("|")})`, "gi");
  return text
    .split(pattern)
    .filter(Boolean)
    .map((part) => ({
      text: part,
      highlight: normalizedTerms.some((term) => part.toLowerCase() === term.toLowerCase()),
    }));
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
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
