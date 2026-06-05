import * as React from "react";
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Clipboard,
  Database,
  ExternalLink,
  FileSearch,
  Gauge,
  GitCompareArrows,
  History,
  ListFilter,
  Loader2,
  Network,
  RefreshCw,
  Search,
  ShieldCheck,
  X,
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
  useDeleteRetrievalJudgmentMutation,
  useRetrievalIntegrityQuery,
  useRetrievalJudgmentEvaluationQuery,
  useRetrievalJudgmentMutation,
  useRetrievalJudgmentSummaryQuery,
  useRetrievalJudgmentsQuery,
  useRetrievalPresetsQuery,
  useRetrievalSearchOptionsQuery,
  useRetrievalSearchMutation,
  useRetrievalSourcesQuery,
  useRuntimeConfigQuery,
  useSchemasQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import { cn, humanize } from "../../lib/utils";
import type {
  Evidence,
  RetrievalFacetBucket,
  RetrievalGraphContext,
  RetrievalHit,
  RetrievalIntegrityReport,
  RetrievalPackage,
  RetrievalCoverage,
  RetrievalFacets,
  RetrievalJudgmentEvaluationResult,
  RetrievalQualitySummary,
  RetrievalQualitySignal,
  RetrievalQueryVariant,
  RetrievalRelevanceJudgment,
  RetrievalRelevanceJudgmentSummary,
  RetrievalScoreComponent,
  RetrievalSearchPayload,
  RetrievalSearchOption,
  RetrievalSearchPreset,
  RetrievalSource,
  RuntimeRetrievalRulePack,
  RuntimeConfig,
} from "../../types";

type SupportedFilterField = "clinical_domain" | "standard_system" | "source_type" | "trust_level";
type ActiveFacetFilters = Partial<Record<SupportedFilterField, string>>;
type ActiveFilterEntry = {
  field: SupportedFilterField;
  label: string;
  displayValue: string;
};
type CoverageFilterAction = {
  field: SupportedFilterField;
  value: string;
};
type RetrievalFormState = {
  query: string;
  fields: string;
  schemaId: string;
  detectedFormat: string;
  resourceType: string;
  clinicalDomain: string;
  standardSystem: string;
  trustLevel: string;
  sourceType: string;
  topK: number;
};
type FacetSection = {
  field: SupportedFilterField;
  label: string;
  values: RetrievalFacetBucket[];
  formatter: (value: string) => string;
};
type RetrievalSearchRun = {
  packageData: RetrievalPackage;
  payload: RetrievalSearchPayload;
  runId: string;
  signature: string;
  submittedAt: string;
  summary: RetrievalRunSummary;
};
type RetrievalRunSummary = {
  candidateCount: number;
  coverage: RetrievalCoverageSummary[];
  hitCount: number;
  qualityWarningCount: number;
  queryAspects: QueryAspectSummary[];
  queryProfile: QueryProfileSummary | null;
  rulePackCount: number;
  rulePackFingerprint: string;
  topSourceId: string | null;
  warningCount: number;
};
type RetrievalCoverageSummary = {
  field: string;
  label: string;
  selectedCount: number;
  status: string;
  suggestedFilter: Record<string, string>;
  value: string;
};
type QueryAspectSummary = {
  aspectId: string;
  label: string;
  priority: number;
  question: string;
  ruleId: string;
};
type QueryProfileSummary = {
  complexity: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
};
type RetrievalRulePackChange = {
  active?: RuntimeRetrievalRulePack;
  baseline?: RuntimeRetrievalRulePack;
  name: string;
  status: "added" | "removed" | "changed" | "stable";
};
type RelevanceJudgmentValue = "relevant" | "partial" | "not_relevant";
type RelevanceJudgment = {
  evidenceId: string;
  judgedAt: string;
  judgmentId?: string | null;
  query: string;
  rating: number;
  runId: string;
  searchSignature?: string | null;
  sourceId?: string | null;
  value: RelevanceJudgmentValue;
};
type RelevanceJudgmentIndex = Record<string, RelevanceJudgment>;
type RelevanceJudgmentMetrics = {
  averageRating: number | null;
  judgedCount: number;
  judgedPrecision: number | null;
  judgmentCoverage: number;
  ndcgAtK: number | null;
  notRelevantCount: number;
  partialCount: number;
  precisionAtK: number;
  relevantCount: number;
  totalHits: number;
};
type RetrievalRunComparison = {
  addedEvidenceIds: string[];
  activePayload: RetrievalSearchPayload;
  activeQuery: string;
  activeRunId: string;
  activeSubmittedAt: string;
  activeSummary: RetrievalRunSummary;
  baselinePayload: RetrievalSearchPayload;
  baselineQuery: string;
  baselineRunId: string;
  baselineSubmittedAt: string;
  baselineSummary: RetrievalRunSummary;
  candidateDelta: number;
  coverageComparison: RetrievalCoverageComparison;
  diagnosis: RetrievalComparisonDiagnosis[];
  facetComparisons: RetrievalFacetComparison[];
  hitDelta: number;
  metrics: RetrievalRunComparisonMetrics;
  queryAspectComparison: RetrievalQueryAspectComparison;
  qualityWarningDelta: number;
  qualitySignalComparison: RetrievalQualitySignalComparison;
  queryProfileChanged: boolean;
  rankChanges: RetrievalRankChange[];
  removedEvidenceIds: string[];
  retainedEvidenceIds: string[];
  rulePackChanges: RetrievalRulePackChange[];
  rulePackChanged: boolean;
  topSourceAfter: string | null;
  topSourceBefore: string | null;
  topSourceChanged: boolean;
  warningDelta: number;
};
type RetrievalComparisonDiagnosis = {
  code: string;
  message: string;
  severity: "success" | "warning" | "muted";
};
type RetrievalQueryAspectComparison = {
  added: QueryAspectSummary[];
  removed: QueryAspectSummary[];
  retained: QueryAspectSummary[];
};
type RetrievalCoverageComparison = {
  added: RetrievalCoverageSummary[];
  improved: RetrievalCoverageStatusChange[];
  regressed: RetrievalCoverageStatusChange[];
  removed: RetrievalCoverageSummary[];
  retained: RetrievalCoverageSummary[];
};
type RetrievalCoverageStatusChange = {
  active: RetrievalCoverageSummary;
  baseline: RetrievalCoverageSummary;
};
type RetrievalQualitySignalComparison = {
  added: RetrievalQualitySignalSummary[];
  removed: RetrievalQualitySignalSummary[];
  retained: RetrievalQualitySignalSummary[];
};
type RetrievalQualitySignalSummary = {
  code: string;
  message: string;
  severity: string;
  suggestedAction: string;
};
type RetrievalFacetComparison = {
  activeCount: number;
  addedValues: string[];
  baselineCount: number;
  field: SupportedFilterField;
  label: string;
  removedValues: string[];
  retainedValues: string[];
};
type RetrievalRunComparisonMetrics = {
  changedRankCount: number;
  churnRate: number;
  meanAbsoluteRankDelta: number;
  overlapRatio: number;
  sharedCount: number;
  unionCount: number;
};
type RetrievalRankChange = {
  evidenceId: string;
  fromRank: number;
  rankDelta: number;
  toRank: number;
};

const supportedSuggestionFilterFields = new Set<SupportedFilterField>([
  "clinical_domain",
  "standard_system",
  "source_type",
  "trust_level",
]);
const searchRunHistoryLimit = 6;
const relevanceJudgmentOptions: Array<{
  activeVariant: "default" | "secondary" | "destructive";
  description: string;
  label: string;
  value: RelevanceJudgmentValue;
}> = [
  {
    activeVariant: "default",
    description: "Mark this evidence as relevant for the submitted query.",
    label: "Relevant",
    value: "relevant",
  },
  {
    activeVariant: "secondary",
    description: "Mark this evidence as partially relevant for the submitted query.",
    label: "Partial",
    value: "partial",
  },
  {
    activeVariant: "destructive",
    description: "Mark this evidence as not relevant for the submitted query.",
    label: "Not relevant",
    value: "not_relevant",
  },
];

export function RetrievalPage() {
  const presetsQuery = useRetrievalPresetsQuery();
  const searchOptionsQuery = useRetrievalSearchOptionsQuery();
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
  const upsertJudgmentMutation = useRetrievalJudgmentMutation();
  const deleteJudgmentMutation = useDeleteRetrievalJudgmentMutation();
  const [query, setQuery] = React.useState("");
  const [fields, setFields] = React.useState("");
  const [schemaId, setSchemaId] = React.useState("");
  const [detectedFormat, setDetectedFormat] = React.useState("");
  const [resourceType, setResourceType] = React.useState("");
  const [clinicalDomain, setClinicalDomain] = React.useState("");
  const [standardSystem, setStandardSystem] = React.useState("");
  const [trustLevel, setTrustLevel] = React.useState("approved");
  const [sourceType, setSourceType] = React.useState("");
  const [topK, setTopK] = React.useState(5);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [lastSearchSignature, setLastSearchSignature] = React.useState<string | null>(null);
  const [submittedSearchPayload, setSubmittedSearchPayload] =
    React.useState<RetrievalSearchPayload | null>(null);
  const [activePresetId, setActivePresetId] = React.useState<string | null>(null);
  const [didApplyInitialPreset, setDidApplyInitialPreset] = React.useState(false);
  const [searchRuns, setSearchRuns] = React.useState<RetrievalSearchRun[]>([]);
  const [activeRunId, setActiveRunId] = React.useState<string | null>(null);
  const [comparisonBaselineRunId, setComparisonBaselineRunId] =
    React.useState<string | null>(null);
  const [relevanceJudgments, setRelevanceJudgments] =
    React.useState<RelevanceJudgmentIndex>({});

  const activeRun = React.useMemo(
    () => searchRuns.find((run) => run.runId === activeRunId) ?? null,
    [activeRunId, searchRuns],
  );
  const persistedJudgmentsQuery = useRetrievalJudgmentsQuery({
    query: activeRun?.payload.query ?? null,
    limit: 500,
  });
  const persistedJudgmentSummaryQuery = useRetrievalJudgmentSummaryQuery({
    query: activeRun?.payload.query ?? null,
    limit: 1000,
  });
  const activeRunEvidenceIds = React.useMemo(
    () => activeRun?.packageData.hits.map((hit) => hit.evidence.evidence_id) ?? [],
    [activeRun],
  );
  const persistedJudgmentEvaluationQuery = useRetrievalJudgmentEvaluationQuery(
    activeRun
      ? {
          query: activeRun.payload.query,
          ranked_evidence_ids: activeRunEvidenceIds,
          cutoff: activeRun.packageData.hits.length,
        }
      : null,
  );
  const activeRunComparison = React.useMemo(() => {
    if (!activeRun) return null;
    const baselineRun = comparisonRunForActive(
      searchRuns,
      activeRun.runId,
      comparisonBaselineRunId,
    );
    return baselineRun ? compareSearchRuns(activeRun, baselineRun) : null;
  }, [activeRun, comparisonBaselineRunId, searchRuns]);
  const comparisonJudgments = React.useMemo(
    () =>
      activeRunComparison
        ? judgmentsForComparison(activeRunComparison, relevanceJudgments)
        : [],
    [activeRunComparison, relevanceJudgments],
  );
  const packageData = activeRun?.packageData ?? searchMutation.data;
  const isJudgmentSyncing = Boolean(
    activeRun &&
      (persistedJudgmentsQuery.isFetching ||
        persistedJudgmentSummaryQuery.isFetching ||
        persistedJudgmentEvaluationQuery.isFetching ||
        upsertJudgmentMutation.isPending ||
        deleteJudgmentMutation.isPending),
  );
  const presets = presetsQuery.data ?? [];
  const searchOptions = searchOptionsQuery.data;
  const sources = sourcesQuery.data ?? [];
  const domains = uniqueValues(sources.map((source) => source.clinical_domain));
  const standards = uniqueValues(sources.map((source) => source.standard_system));
  const domainOptions = uniqueValues([...domains, clinicalDomain]);
  const standardOptions = uniqueValues([...standards, standardSystem]);
  const trustOptions = uniqueValues([
    ...sources.map((source) => source.trust_level),
    ...presets.map((preset) => preset.trust_level),
    trustLevel,
  ]);
  const sourceTypeOptions = uniqueValues([
    ...sources.map((source) => source.source_type),
    ...presets.map((preset) => preset.source_type),
    sourceType,
  ]);
  const formatOptions = mergeSearchOptions(
    searchOptions?.detected_formats ?? [],
    presets.map((preset) => preset.detected_format),
    detectedFormat,
  );
  const topKOptions = uniqueNumberValues([
    ...(searchOptions?.top_k_values ?? []),
    topK,
    ...presets.map((preset) => preset.top_k),
  ]);
  const graphContext = packageData?.handoff_context.graph_context;
  const activeFacetFilters: ActiveFacetFilters = {
    clinical_domain: clinicalDomain || undefined,
    standard_system: standardSystem || undefined,
    source_type: sourceType || undefined,
    trust_level: trustLevel || undefined,
  };
  const formState: RetrievalFormState = {
    query,
    fields,
    schemaId,
    detectedFormat,
    resourceType,
    clinicalDomain,
    standardSystem,
    trustLevel,
    sourceType,
    topK,
  };
  const currentSearchSignature = retrievalSearchSignature(retrievalPayloadFromForm(formState));
  const isSearchResultStale = Boolean(
    packageData && lastSearchSignature && currentSearchSignature !== lastSearchSignature,
  );

  const executeSearch = async (overrides: Partial<RetrievalSearchPayload> = {}) => {
    const payload = retrievalPayloadFromForm(formState, overrides);
    if (!payload.query) {
      setFormError("Enter a retrieval query before searching.");
      return;
    }
    setFormError(null);
    const packageResult = await searchMutation.mutateAsync(payload);
    const signature = retrievalSearchSignature(payload);
    const run = createSearchRun(payload, packageResult, signature);
    setSearchRuns((current) => [
      run,
      ...current.filter((item) => item.signature !== signature),
    ].slice(0, searchRunHistoryLimit));
    setActiveRunId(run.runId);
    setSubmittedSearchPayload(payload);
    setLastSearchSignature(signature);
  };

  const runSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    await executeSearch();
  };

  const markCustomSearch = () => setActivePresetId(null);

  const applyPreset = React.useCallback((preset: RetrievalSearchPreset) => {
    setQuery(preset.query);
    setFields(preset.fields.join(", "));
    setSchemaId(preset.schema_id ?? "");
    setDetectedFormat(preset.detected_format ?? "");
    setResourceType(preset.resource_type ?? "");
    setClinicalDomain(preset.clinical_domain ?? "");
    setStandardSystem(preset.standard_system ?? "");
    setSourceType(preset.source_type ?? "");
    setTrustLevel(preset.trust_level ?? "");
    setTopK(preset.top_k);
    setFormError(null);
    setActivePresetId(preset.preset_id);
  }, []);

  React.useEffect(() => {
    if (didApplyInitialPreset || !presets.length) return;
    applyPreset(presets[0]);
    setDidApplyInitialPreset(true);
  }, [applyPreset, didApplyInitialPreset, presets]);

  React.useEffect(() => {
    if (!comparisonBaselineRunId) return;
    if (searchRuns.some((run) => run.runId === comparisonBaselineRunId)) return;
    setComparisonBaselineRunId(null);
  }, [comparisonBaselineRunId, searchRuns]);

  React.useEffect(() => {
    const runIds = new Set(searchRuns.map((run) => run.runId));
    setRelevanceJudgments((current) => {
      const next = Object.fromEntries(
        Object.entries(current).filter(([, judgment]) => runIds.has(judgment.runId)),
      );
      return Object.keys(next).length === Object.keys(current).length ? current : next;
    });
  }, [searchRuns]);

  React.useEffect(() => {
    if (!activeRun || !persistedJudgmentsQuery.data) return;
    const hitEvidenceIds = new Set(
      activeRun.packageData.hits.map((hit) => hit.evidence.evidence_id),
    );
    const matchingJudgments = persistedJudgmentsQuery.data.filter((judgment) =>
      hitEvidenceIds.has(judgment.evidence_id),
    );
    if (!matchingJudgments.length) return;
    setRelevanceJudgments((current) => {
      const next = { ...current };
      for (const judgment of matchingJudgments) {
        const key = relevanceJudgmentKey(activeRun.runId, judgment.evidence_id);
        next[key] = relevanceJudgmentFromPersisted(judgment, {
          query: activeRun.payload.query,
          runId: activeRun.runId,
          signature: activeRun.signature,
        });
      }
      return next;
    });
  }, [activeRun, persistedJudgmentsQuery.data]);

  const applySearchFilter = (field: SupportedFilterField, value: string) => {
    markCustomSearch();
    const overrides: Partial<RetrievalSearchPayload> = {};
    if (field === "clinical_domain") {
      setClinicalDomain(value);
      overrides.clinical_domain = value;
    } else if (field === "standard_system") {
      setStandardSystem(value);
      overrides.standard_system = value;
    } else if (field === "source_type") {
      setSourceType(value);
      overrides.source_type = value;
    } else if (field === "trust_level") {
      setTrustLevel(value);
      overrides.trust_level = value;
    }
    void executeSearch(overrides);
  };

  const clearSearchFilter = (field: SupportedFilterField) => {
    markCustomSearch();
    const overrides: Partial<RetrievalSearchPayload> = {};
    if (field === "clinical_domain") {
      setClinicalDomain("");
      overrides.clinical_domain = null;
    } else if (field === "standard_system") {
      setStandardSystem("");
      overrides.standard_system = null;
    } else if (field === "source_type") {
      setSourceType("");
      overrides.source_type = null;
    } else if (field === "trust_level") {
      setTrustLevel("");
      overrides.trust_level = null;
    }
    if (packageData) void executeSearch(overrides);
  };

  const clearAllSearchFilters = () => {
    markCustomSearch();
    setClinicalDomain("");
    setStandardSystem("");
    setSourceType("");
    setTrustLevel("");
    if (packageData) {
      void executeSearch({
        clinical_domain: null,
        standard_system: null,
        source_type: null,
        trust_level: null,
      });
    }
  };

  const restoreSubmittedSearch = () => {
    if (!submittedSearchPayload) return;
    restoreSearchPayload(submittedSearchPayload);
  };

  const restoreSearchPayload = (payload: RetrievalSearchPayload) => {
    markCustomSearch();
    setQuery(payload.query);
    setFields(payload.fields.join(", "));
    setSchemaId(payload.schema_id ?? "");
    setDetectedFormat(payload.detected_format ?? "");
    setResourceType(payload.resource_type ?? "");
    setClinicalDomain(payload.clinical_domain ?? "");
    setStandardSystem(payload.standard_system ?? "");
    setSourceType(payload.source_type ?? "");
    setTrustLevel(payload.trust_level ?? "");
    setTopK(payload.top_k);
    setFormError(null);
  };

  const restoreSearchRun = (run: RetrievalSearchRun) => {
    restoreSearchPayload(run.payload);
    setSubmittedSearchPayload(run.payload);
    setLastSearchSignature(run.signature);
    setActiveRunId(run.runId);
    if (comparisonBaselineRunId === run.runId) setComparisonBaselineRunId(null);
  };

  const clearSearchRuns = () => {
    setSearchRuns([]);
    setActiveRunId(null);
    setComparisonBaselineRunId(null);
    setRelevanceJudgments({});
  };

  const setHitJudgment = (
    runId: string | null,
    queryText: string,
    searchSignature: string | null,
    evidence: Evidence,
    value: RelevanceJudgmentValue,
  ) => {
    if (!runId) return;
    const evidenceId = evidence.evidence_id;
    const key = relevanceJudgmentKey(runId, evidenceId);
    const existing = relevanceJudgments[key] ?? null;
    if (existing?.value === value) {
      setRelevanceJudgments((current) => {
        const { [key]: _removed, ...remaining } = current;
        return remaining;
      });
      if (existing.judgmentId) {
        deleteJudgmentMutation.mutate(existing.judgmentId);
      }
      return;
    }
    const rating = relevanceJudgmentRating(value);
    setRelevanceJudgments((current) => {
      return {
        ...current,
        [key]: {
          evidenceId,
          judgedAt: new Date().toISOString(),
          judgmentId: existing?.judgmentId ?? null,
          query: queryText,
          rating,
          runId,
          searchSignature,
          sourceId: evidence.source_id,
          value,
        },
      };
    });
    upsertJudgmentMutation.mutate(
      {
        query: queryText,
        evidence_id: evidenceId,
        source_id: evidence.source_id,
        source_type: evidence.source_type,
        source_version: evidence.source_version ?? null,
        value,
        rating,
        run_id: runId,
        search_signature: searchSignature,
        metadata: {
          trust_level: evidence.trust_level,
          review_surface: "retrieval_console",
        },
      },
      {
        onSuccess: (persisted) => {
          setRelevanceJudgments((current) => {
            if (current[key]?.value !== value) return current;
            return {
              ...current,
              [key]: relevanceJudgmentFromPersisted(persisted, {
                query: queryText,
                runId,
                signature: searchSignature ?? "",
              }),
            };
          });
        },
      },
    );
  };

  const applyFilterSuggestion = (suggestion: FilterSuggestionStack) => {
    if (!isSupportedFilterField(suggestion.field)) return;
    applySearchFilter(suggestion.field, suggestion.value);
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
        <div className="grid min-w-0 gap-5">
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
              {presetsQuery.isError ? (
                <Notice title="Search presets unavailable">
                  {workflowErrorMessage(presetsQuery.error)}
                </Notice>
              ) : null}
              {searchOptionsQuery.isError ? (
                <Notice title="Search options unavailable">
                  {workflowErrorMessage(searchOptionsQuery.error)}
                </Notice>
              ) : null}

              <SearchPresetStrip
                activePresetId={activePresetId}
                isLoading={presetsQuery.isLoading}
                onApplyPreset={applyPreset}
                presets={presets}
              />

              <Label>
                Query
                <Textarea
                  className="min-h-24 resize-y"
                  onChange={(event) => {
                    markCustomSearch();
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
                  onChange={(event) => {
                    markCustomSearch();
                    setFields(event.target.value);
                  }}
                  value={fields}
                />
              </Label>

              <div className="grid gap-3 sm:grid-cols-2">
                <Label>
                  Schema
                  <Select
                    onChange={(event) => {
                      markCustomSearch();
                      setSchemaId(event.target.value);
                    }}
                    value={schemaId}
                  >
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
                  <Select
                    onChange={(event) => {
                      markCustomSearch();
                      setTopK(Number(event.target.value));
                    }}
                    value={topK}
                  >
                    {topKOptions.map((value) => (
                      <option key={value} value={value}>{value}</option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Format
                  <Select
                    onChange={(event) => {
                      markCustomSearch();
                      setDetectedFormat(event.target.value);
                    }}
                    value={detectedFormat}
                  >
                    <option value="">Any format</option>
                    {formatOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Resource
                  <Input
                    onChange={(event) => {
                      markCustomSearch();
                      setResourceType(event.target.value);
                    }}
                    placeholder="Observation"
                    value={resourceType}
                  />
                </Label>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <Label>
                  Domain
                  <Select
                    onChange={(event) => {
                      markCustomSearch();
                      setClinicalDomain(event.target.value);
                    }}
                    value={clinicalDomain}
                  >
                    <option value="">Any domain</option>
                    {domainOptions.map((domain) => (
                      <option key={domain} value={domain}>{humanize(domain)}</option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Standard
                  <Select
                    onChange={(event) => {
                      markCustomSearch();
                      setStandardSystem(event.target.value);
                    }}
                    value={standardSystem}
                  >
                    <option value="">Any standard</option>
                    {standardOptions.map((standard) => (
                      <option key={standard} value={standard}>{standard}</option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Trust
                  <Select
                    onChange={(event) => {
                      markCustomSearch();
                      setTrustLevel(event.target.value);
                    }}
                    value={trustLevel}
                  >
                    <option value="">Any trust</option>
                    {trustOptions.map((trust) => (
                      <option key={trust} value={trust}>{humanize(trust)}</option>
                    ))}
                  </Select>
                </Label>
                <Label>
                  Source type
                  <Select
                    onChange={(event) => {
                      markCustomSearch();
                      setSourceType(event.target.value);
                    }}
                    value={sourceType}
                  >
                    <option value="">Any source</option>
                    {sourceTypeOptions.map((type) => (
                      <option key={type} value={type}>{humanize(type)}</option>
                    ))}
                  </Select>
                </Label>
              </div>

              <ActiveFilterBar
                filters={activeFilterEntries(activeFacetFilters)}
                isSearchPending={searchMutation.isPending}
                onClearAll={clearAllSearchFilters}
                onRemove={clearSearchFilter}
              />

              {isSearchResultStale ? (
                <Notice title="Search settings changed">
                  Run search to refresh ranked evidence with the current query builder state.
                </Notice>
              ) : null}

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
          <SearchRunHistory
            activeRunId={activeRunId}
            comparison={activeRunComparison}
            comparisonBaselineRunId={comparisonBaselineRunId}
            comparisonJudgments={comparisonJudgments}
            isSearchPending={searchMutation.isPending}
            onClear={clearSearchRuns}
            onRestore={restoreSearchRun}
            onSetComparisonBaseline={setComparisonBaselineRunId}
            runs={searchRuns}
          />
        </div>

        <div className="grid min-w-0 gap-5">
          <SearchResults
            activeFilters={activeFacetFilters}
            isSearchPending={searchMutation.isPending}
            isStale={isSearchResultStale}
            onApplyFacet={applySearchFilter}
            onSetJudgment={(evidence, value) =>
              setHitJudgment(
                activeRun?.runId ?? null,
                activeRun?.payload.query ?? submittedSearchPayload?.query ?? "",
                activeRun?.signature ?? lastSearchSignature,
                evidence,
                value,
              )
            }
            onRestoreSubmittedSearch={restoreSubmittedSearch}
            packageData={packageData}
            relevanceJudgments={relevanceJudgments}
            runId={activeRun?.runId ?? null}
            persistedJudgmentSummary={persistedJudgmentSummaryQuery.data ?? null}
            persistedJudgmentEvaluation={persistedJudgmentEvaluationQuery.data ?? null}
            isJudgmentSyncing={isJudgmentSyncing}
            submittedSearchPayload={submittedSearchPayload}
          />
          <div className="grid min-w-0 gap-5 2xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.9fr)]">
            <TracePanel
              isSearchPending={searchMutation.isPending}
              onApplyCoverageFilter={applySearchFilter}
              onApplyFilterSuggestion={applyFilterSuggestion}
              packageData={packageData}
            />
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
  const qualitySummary = packageData?.quality_summary ?? null;
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
        label="Readiness"
        supporting={qualitySummary?.top_action ?? "Run search to assess package quality"}
        tone={qualitySummaryTone(qualitySummary)}
        value={qualitySummary ? `${qualitySummary.score}/100` : "n/a"}
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

function SearchRunHistory({
  activeRunId,
  comparison,
  comparisonBaselineRunId,
  comparisonJudgments,
  isSearchPending,
  onClear,
  onRestore,
  onSetComparisonBaseline,
  runs,
}: {
  activeRunId: string | null;
  comparison: RetrievalRunComparison | null;
  comparisonBaselineRunId: string | null;
  comparisonJudgments: RelevanceJudgment[];
  isSearchPending: boolean;
  onClear: () => void;
  onRestore: (run: RetrievalSearchRun) => void;
  onSetComparisonBaseline: (runId: string | null) => void;
  runs: RetrievalSearchRun[];
}) {
  if (!runs.length) return null;
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3 border-b border-border bg-card/70">
        <div>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            Search runs
          </CardTitle>
          <CardDescription>{formatCount(runs.length, "recent run")}</CardDescription>
        </div>
        <Button
          aria-label="Clear recent search runs"
          disabled={isSearchPending}
          onClick={onClear}
          size="sm"
          type="button"
          variant="ghost"
        >
          Clear
        </Button>
      </CardHeader>
      <CardContent className="grid gap-2 pt-4">
        {runs.map((run) => {
          const active = run.runId === activeRunId;
          const baseline = run.runId === comparisonBaselineRunId;
          const canSetBaseline = !active && !isSearchPending;
          return (
            <div
              className={cn(
                "grid min-w-0 gap-2 rounded-md border px-3 py-2 text-sm transition-colors",
                active
                  ? "border-primary bg-primary/10 text-foreground"
                  : "border-border bg-card hover:bg-muted",
              )}
              key={run.runId}
              title={run.payload.query}
            >
              <button
                aria-label={`Restore search run ${run.payload.query}`}
                aria-pressed={active}
                className="grid w-full min-w-0 gap-2 text-left focus-ring disabled:cursor-not-allowed disabled:opacity-70"
                disabled={isSearchPending}
                onClick={() => onRestore(run)}
                type="button"
              >
                <span className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                  <span className="min-w-0 break-words font-black">
                    {run.payload.query}
                  </span>
                  <span className="flex min-w-0 flex-wrap justify-end gap-1.5">
                    {baseline ? <Badge variant="default">baseline</Badge> : null}
                    <Badge variant={searchRunSummaryVariant(run.summary)}>
                      {run.summary.qualityWarningCount
                        ? formatCount(run.summary.qualityWarningCount, "issue")
                        : "ready"}
                    </Badge>
                  </span>
                </span>
                <span className="flex min-w-0 flex-wrap gap-1.5">
                  <Badge variant="muted">{formatRunTime(run.submittedAt)}</Badge>
                  <Badge variant="muted">top {run.payload.top_k}</Badge>
                  <Badge variant="muted">
                    {formatCount(run.summary.hitCount, "hit")}
                  </Badge>
                  <Badge variant="muted">
                    {formatCount(run.summary.candidateCount, "candidate")}
                  </Badge>
                  <Badge variant="muted">
                    {formatCount(run.summary.rulePackCount, "rule pack")}
                  </Badge>
                  {run.summary.queryProfile ? (
                    <Badge variant="muted">
                      {humanize(run.summary.queryProfile.route)}
                    </Badge>
                  ) : null}
                  {run.summary.warningCount ? (
                    <Badge variant="warning">
                      {formatCount(run.summary.warningCount, "warning")}
                    </Badge>
                  ) : null}
                </span>
                {run.summary.topSourceId ? (
                  <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
                    Top source: {run.summary.topSourceId}
                  </span>
                ) : null}
                {run.summary.queryProfile ? (
                  <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
                    Profile: {run.summary.queryProfile.label} /{" "}
                    {humanize(run.summary.queryProfile.retrievalMode)}
                  </span>
                ) : null}
              </button>
              <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
                <Button
                  aria-label={
                    baseline
                      ? `Clear comparison baseline ${run.payload.query}`
                      : `Use ${run.payload.query} as comparison baseline`
                  }
                  disabled={!canSetBaseline}
                  onClick={() => onSetComparisonBaseline(baseline ? null : run.runId)}
                  size="sm"
                  type="button"
                  variant={baseline ? "secondary" : "outline"}
                >
                  <GitCompareArrows className="h-4 w-4" />
                  {baseline ? "Baseline" : "Set baseline"}
                </Button>
              </div>
            </div>
          );
        })}
        {comparison ? (
          <SearchRunComparison
            comparison={comparison}
            judgments={comparisonJudgments}
          />
        ) : null}
      </CardContent>
    </Card>
  );
}

function SearchRunComparison({
  comparison,
  judgments,
}: {
  comparison: RetrievalRunComparison;
  judgments: RelevanceJudgment[];
}) {
  const copyReport = async () => {
    await copyTextToClipboard(
      JSON.stringify(comparisonReportFromComparison(comparison, judgments), null, 2),
    );
  };

  return (
    <div
      aria-label="Search run comparison"
      className="mt-1 grid gap-3 rounded-md border border-border bg-muted/25 p-3 text-sm"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Run comparison
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={comparison.topSourceChanged ? "warning" : "success"}>
            {comparison.topSourceChanged ? "top source changed" : "top source stable"}
          </Badge>
          <Badge variant={comparison.queryProfileChanged ? "warning" : "success"}>
            {comparison.queryProfileChanged ? "profile changed" : "profile stable"}
          </Badge>
          <Badge variant={comparison.rulePackChanged ? "warning" : "success"}>
            {comparison.rulePackChanged ? "rule packs changed" : "rule packs stable"}
          </Badge>
          <Button
            aria-label="Copy retrieval comparison report"
            onClick={() => void copyReport()}
            size="sm"
            type="button"
            variant="outline"
          >
            <Clipboard className="h-4 w-4" />
            Copy report
          </Button>
        </div>
      </div>
      <div className="break-words text-xs leading-5 text-muted-foreground">
        Compared with: {comparison.baselineQuery}
      </div>
      <RunComparisonDiagnosis diagnosis={comparison.diagnosis} />
      <RunComparisonMetrics metrics={comparison.metrics} />
      <div className="grid gap-2 sm:grid-cols-2">
        <RunComparisonMetric
          delta={comparison.hitDelta}
          label="Hits"
          positiveIsGood
        />
        <RunComparisonMetric
          delta={comparison.candidateDelta}
          label="Candidates"
          positiveIsGood
        />
        <RunComparisonMetric
          delta={comparison.warningDelta}
          label="Warnings"
          positiveIsGood={false}
        />
        <RunComparisonMetric
          delta={comparison.qualityWarningDelta}
          label="Quality issues"
          positiveIsGood={false}
        />
      </div>
      <div className="grid gap-2">
        <RunComparisonQueryProfile comparison={comparison} />
        <RunComparisonQueryAspects comparison={comparison.queryAspectComparison} />
        <RunComparisonCoverage comparison={comparison.coverageComparison} />
        <RunComparisonQualitySignals comparison={comparison.qualitySignalComparison} />
        <RunComparisonFacetCoverage facetComparisons={comparison.facetComparisons} />
        <RunComparisonRulePacks rulePackChanges={comparison.rulePackChanges} />
        <RunComparisonRankChanges rankChanges={comparison.rankChanges} />
        <RunComparisonEvidenceChange
          evidenceIds={comparison.addedEvidenceIds}
          label="Added evidence"
          variant="success"
        />
        <RunComparisonEvidenceChange
          evidenceIds={comparison.removedEvidenceIds}
          label="Removed evidence"
          variant="warning"
        />
        <RunComparisonEvidenceChange
          evidenceIds={comparison.retainedEvidenceIds}
          label="Retained evidence"
          variant="muted"
        />
      </div>
      <div className="break-words text-xs font-semibold text-muted-foreground">
        Top source: {comparison.topSourceBefore ?? "none"} to{" "}
        {comparison.topSourceAfter ?? "none"}
      </div>
    </div>
  );
}

function RunComparisonDiagnosis({
  diagnosis,
}: {
  diagnosis: RetrievalComparisonDiagnosis[];
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">
          Comparison diagnosis
        </span>
        <Badge
          variant={diagnosis.some((item) => item.severity === "warning") ? "warning" : "success"}
        >
          {diagnosis.some((item) => item.severity === "warning")
            ? formatCount(
                diagnosis.filter((item) => item.severity === "warning").length,
                "change driver",
              )
            : "stable"}
        </Badge>
      </div>
      <div className="grid gap-1">
        {diagnosis.map((item) => (
          <div
            className="flex min-w-0 flex-wrap items-start gap-2"
            key={item.code}
          >
            <Badge variant={item.severity}>{humanize(item.code)}</Badge>
            <span className="min-w-0 flex-1 break-words text-muted-foreground">
              {item.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RunComparisonMetrics({
  metrics,
}: {
  metrics: RetrievalRunComparisonMetrics;
}) {
  return (
    <div aria-label="Search comparison metrics" className="grid gap-2 sm:grid-cols-2">
      <RunComparisonMetricCard
        label="Overlap"
        tone={metrics.overlapRatio >= 0.5 ? "success" : "warning"}
        value={formatPercent(metrics.overlapRatio)}
      />
      <RunComparisonMetricCard
        label="Result churn"
        tone={metrics.churnRate > 0.5 ? "warning" : "success"}
        value={formatPercent(metrics.churnRate)}
      />
      <RunComparisonMetricCard
        label="Shared evidence"
        tone={metrics.sharedCount ? "success" : "warning"}
        value={`${metrics.sharedCount}/${metrics.unionCount}`}
      />
      <RunComparisonMetricCard
        label="Mean rank delta"
        tone={metrics.meanAbsoluteRankDelta > 1 ? "warning" : "success"}
        value={formatDecimal(metrics.meanAbsoluteRankDelta)}
      />
    </div>
  );
}

function RunComparisonMetricCard({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "success" | "warning";
  value: string;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2">
      <span className="text-xs font-bold text-muted-foreground">{label}</span>
      <Badge variant={tone}>{value}</Badge>
    </div>
  );
}

function RunComparisonMetric({
  delta,
  label,
  positiveIsGood,
}: {
  delta: number;
  label: string;
  positiveIsGood: boolean;
}) {
  return (
    <div className="flex min-w-0 items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
      <span className="text-xs font-bold text-muted-foreground">{label}</span>
      <Badge variant={deltaBadgeVariant(delta, positiveIsGood)}>
        {formatSignedDelta(delta)}
      </Badge>
    </div>
  );
}

function RunComparisonQueryProfile({
  comparison,
}: {
  comparison: RetrievalRunComparison;
}) {
  const before = comparison.baselineSummary.queryProfile;
  const after = comparison.activeSummary.queryProfile;
  if (!before && !after) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Query profile</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-1 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Query profile</span>
        <Badge variant={comparison.queryProfileChanged ? "warning" : "success"}>
          {comparison.queryProfileChanged ? "changed" : "stable"}
        </Badge>
      </div>
      <div className="grid gap-1 sm:grid-cols-2">
        <QueryProfileSummaryCard label="Baseline" profile={before} />
        <QueryProfileSummaryCard label="Active" profile={after} />
      </div>
    </div>
  );
}

function QueryProfileSummaryCard({
  label,
  profile,
}: {
  label: string;
  profile: QueryProfileSummary | null;
}) {
  if (!profile) {
    return (
      <div className="rounded-md bg-muted/40 px-2 py-1.5 text-muted-foreground">
        {label}: none
      </div>
    );
  }
  return (
    <div className="grid gap-1 rounded-md bg-muted/40 px-2 py-1.5">
      <span className="font-bold">{label}: {profile.label}</span>
      <span className="break-words text-muted-foreground">
        {humanize(profile.route)} / {humanize(profile.retrievalMode)} /{" "}
        {humanize(profile.complexity)}
      </span>
    </div>
  );
}

function RunComparisonQueryAspects({
  comparison,
}: {
  comparison: RetrievalQueryAspectComparison;
}) {
  const changed = comparison.added.length + comparison.removed.length;
  const total = changed + comparison.retained.length;
  if (!total) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Search aspects</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Search aspects</span>
        <Badge variant={changed ? "warning" : "success"}>
          {changed ? formatCount(changed, "changed aspect") : "stable"}
        </Badge>
      </div>
      <QueryAspectChangeList
        aspects={comparison.added}
        label="Added"
        variant="warning"
      />
      <QueryAspectChangeList
        aspects={comparison.removed}
        label="Removed"
        variant="warning"
      />
      <QueryAspectChangeList
        aspects={comparison.retained}
        label="Retained"
        variant="muted"
      />
    </div>
  );
}

function QueryAspectChangeList({
  aspects,
  label,
  variant,
}: {
  aspects: QueryAspectSummary[];
  label: string;
  variant: "warning" | "muted";
}) {
  if (!aspects.length) return null;
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-semibold text-muted-foreground">{label}:</span>
        {aspects.slice(0, 4).map((aspect) => (
          <Badge key={`${label}-${aspect.aspectId}`} variant={variant}>
            {aspect.label}
          </Badge>
        ))}
        {aspects.length > 4 ? <Badge variant="muted">+{aspects.length - 4}</Badge> : null}
      </div>
      <div className="grid gap-1">
        {aspects.slice(0, 2).map((aspect) => (
          <div className="break-words text-muted-foreground" key={`${label}-${aspect.aspectId}-question`}>
            {aspect.question}
          </div>
        ))}
      </div>
    </div>
  );
}

function RunComparisonCoverage({
  comparison,
}: {
  comparison: RetrievalCoverageComparison;
}) {
  const changed =
    comparison.added.length +
    comparison.removed.length +
    comparison.improved.length +
    comparison.regressed.length;
  const total = changed + comparison.retained.length;
  if (!total) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Coverage diagnostics</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Coverage diagnostics</span>
        <Badge variant={comparison.regressed.length || comparison.added.length ? "warning" : "success"}>
          {changed ? formatCount(changed, "changed item") : "stable"}
        </Badge>
      </div>
      <CoverageStatusChangeList
        changes={comparison.improved}
        label="Improved"
        variant="success"
      />
      <CoverageStatusChangeList
        changes={comparison.regressed}
        label="Regressed"
        variant="warning"
      />
      <CoverageSummaryList
        items={comparison.added}
        label="Added"
        variant="warning"
      />
      <CoverageSummaryList
        items={comparison.removed}
        label="Removed"
        variant="muted"
      />
      <CoverageSummaryList
        items={comparison.retained}
        label="Retained"
        variant="muted"
      />
    </div>
  );
}

function CoverageStatusChangeList({
  changes,
  label,
  variant,
}: {
  changes: RetrievalCoverageStatusChange[];
  label: string;
  variant: "success" | "warning";
}) {
  if (!changes.length) return null;
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-semibold text-muted-foreground">{label}:</span>
        {changes.slice(0, 4).map((change) => (
          <Badge key={`${label}-${coverageComparisonKey(change.active)}`} variant={variant}>
            {change.active.label}
          </Badge>
        ))}
        {changes.length > 4 ? <Badge variant="muted">+{changes.length - 4}</Badge> : null}
      </div>
      <div className="grid gap-1">
        {changes.slice(0, 2).map((change) => (
          <div
            className="break-words text-muted-foreground"
            key={`${label}-${coverageComparisonKey(change.active)}-detail`}
          >
            {humanize(change.baseline.status)} to {humanize(change.active.status)} /{" "}
            {change.baseline.selectedCount} to {change.active.selectedCount}
          </div>
        ))}
      </div>
    </div>
  );
}

function CoverageSummaryList({
  items,
  label,
  variant,
}: {
  items: RetrievalCoverageSummary[];
  label: string;
  variant: "warning" | "muted";
}) {
  if (!items.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5">
      <span className="font-semibold text-muted-foreground">{label}:</span>
      {items.slice(0, 4).map((item) => (
        <Badge key={`${label}-${coverageComparisonKey(item)}`} variant={variant}>
          {item.label} / {humanize(item.status)}
        </Badge>
      ))}
      {items.length > 4 ? <Badge variant="muted">+{items.length - 4}</Badge> : null}
    </div>
  );
}

function RunComparisonQualitySignals({
  comparison,
}: {
  comparison: RetrievalQualitySignalComparison;
}) {
  const changed = comparison.added.length + comparison.removed.length;
  const total = changed + comparison.retained.length;
  if (!total) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Quality signals</span>
        <Badge variant="success">none</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Quality signals</span>
        <Badge variant={changed ? "warning" : "success"}>
          {changed ? formatCount(changed, "changed signal") : "stable"}
        </Badge>
      </div>
      <QualitySignalChangeList
        label="Added"
        signals={comparison.added}
        variant="warning"
      />
      <QualitySignalChangeList
        label="Removed"
        signals={comparison.removed}
        variant="success"
      />
      <QualitySignalChangeList
        label="Retained"
        signals={comparison.retained}
        variant="muted"
      />
    </div>
  );
}

function QualitySignalChangeList({
  label,
  signals,
  variant,
}: {
  label: string;
  signals: RetrievalQualitySignalSummary[];
  variant: "success" | "warning" | "muted";
}) {
  if (!signals.length) return null;
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-semibold text-muted-foreground">{label}:</span>
        {signals.slice(0, 4).map((signal) => (
          <Badge key={`${label}-${signal.code}`} variant={variant}>
            {humanize(signal.code)}
          </Badge>
        ))}
        {signals.length > 4 ? <Badge variant="muted">+{signals.length - 4}</Badge> : null}
      </div>
      <div className="grid gap-1">
        {signals.slice(0, 2).map((signal) => (
          <div className="break-words text-muted-foreground" key={`${label}-${signal.code}-message`}>
            {humanize(signal.severity)}: {signal.message}
          </div>
        ))}
      </div>
    </div>
  );
}

function RunComparisonFacetCoverage({
  facetComparisons,
}: {
  facetComparisons: RetrievalFacetComparison[];
}) {
  if (!facetComparisons.length) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Facet coverage</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Facet coverage</span>
        <Badge variant="muted">{formatCount(facetComparisons.length, "facet")}</Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {facetComparisons.map((facet) => (
          <div
            className="grid gap-1 rounded-md bg-muted/40 px-2 py-1.5"
            key={facet.field}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="font-bold">{facet.label}</span>
              <Badge variant={facet.addedValues.length || facet.removedValues.length ? "warning" : "success"}>
                {facet.baselineCount} to {facet.activeCount}
              </Badge>
            </div>
            <FacetValueChange values={facet.addedValues} label="Added" variant="success" />
            <FacetValueChange values={facet.removedValues} label="Removed" variant="warning" />
            <FacetValueChange values={facet.retainedValues} label="Retained" variant="muted" />
          </div>
        ))}
      </div>
    </div>
  );
}

function FacetValueChange({
  label,
  values,
  variant,
}: {
  label: string;
  values: string[];
  variant: "success" | "warning" | "muted";
}) {
  if (!values.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap gap-1">
      <span className="font-semibold text-muted-foreground">{label}:</span>
      {values.slice(0, 4).map((value) => (
        <Badge key={`${label}-${value}`} variant={variant}>
          {value}
        </Badge>
      ))}
      {values.length > 4 ? <Badge variant="muted">+{values.length - 4}</Badge> : null}
    </div>
  );
}

function RunComparisonRulePacks({
  rulePackChanges,
}: {
  rulePackChanges: RetrievalRulePackChange[];
}) {
  const changedCount = rulePackChanges.filter((change) => change.status !== "stable").length;
  if (!rulePackChanges.length) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Rule packs</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-bold text-muted-foreground">Rule packs</span>
        <Badge variant={changedCount ? "warning" : "success"}>
          {changedCount ? formatCount(changedCount, "changed pack") : "stable"}
        </Badge>
      </div>
      <div className="grid gap-1">
        {rulePackChanges.slice(0, 4).map((change) => {
          const activeFingerprint = rulePackFingerprint(change.active);
          const baselineFingerprint = rulePackFingerprint(change.baseline);
          return (
            <div
              className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2 text-xs"
              key={change.name}
            >
              <span className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <span className="break-words font-bold">{change.name}</span>
                <Badge variant={change.status === "stable" ? "success" : "warning"}>
                  {change.status}
                </Badge>
              </span>
              <span className="break-words text-muted-foreground">
                {baselineFingerprint} to {activeFingerprint}
              </span>
            </div>
          );
        })}
        {rulePackChanges.length > 4 ? (
          <div className="text-xs font-semibold text-muted-foreground">
            +{formatCount(rulePackChanges.length - 4, "more rule pack")}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function RunComparisonRankChanges({
  rankChanges,
}: {
  rankChanges: RetrievalRankChange[];
}) {
  if (!rankChanges.length) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Rank movement</span>
        <Badge variant="success">stable</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-bold text-muted-foreground">Rank movement</span>
        <Badge variant="warning">{formatCount(rankChanges.length, "changed rank")}</Badge>
      </div>
      <div className="grid gap-1">
        {rankChanges.slice(0, 4).map((change) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2 text-xs"
            key={change.evidenceId}
          >
            <span className="break-words font-bold">{change.evidenceId}</span>
            <span className="flex min-w-0 flex-wrap gap-1.5 text-muted-foreground">
              <Badge variant={change.rankDelta < 0 ? "success" : "warning"}>
                {change.rankDelta < 0 ? "up" : "down"} {Math.abs(change.rankDelta)}
              </Badge>
              <span>
                #{change.fromRank} to #{change.toRank}
              </span>
            </span>
          </div>
        ))}
        {rankChanges.length > 4 ? (
          <div className="text-xs font-semibold text-muted-foreground">
            +{formatCount(rankChanges.length - 4, "more changed rank")}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function RunComparisonEvidenceChange({
  evidenceIds,
  label,
  variant,
}: {
  evidenceIds: string[];
  label: string;
  variant: "success" | "warning" | "muted";
}) {
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-bold text-muted-foreground">{label}</span>
        <Badge variant={variant}>{evidenceIds.length}</Badge>
      </div>
      {evidenceIds.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {evidenceIds.slice(0, 4).map((evidenceId) => (
            <span
              className="max-w-full break-words rounded-full border border-border bg-background px-2 py-1 text-[11px] font-bold text-muted-foreground"
              key={evidenceId}
            >
              {evidenceId}
            </span>
          ))}
          {evidenceIds.length > 4 ? (
            <span className="rounded-full border border-border bg-background px-2 py-1 text-[11px] font-bold text-muted-foreground">
              +{evidenceIds.length - 4}
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function SearchPresetStrip({
  activePresetId,
  isLoading,
  onApplyPreset,
  presets,
}: {
  activePresetId: string | null;
  isLoading: boolean;
  onApplyPreset: (preset: RetrievalSearchPreset) => void;
  presets: RetrievalSearchPreset[];
}) {
  const [categoryFilter, setCategoryFilter] = React.useState<string | null>(null);
  const [presetSearch, setPresetSearch] = React.useState("");
  const categories = uniqueValues(presets.map((preset) => preset.category));
  const filteredPresets = presets.filter((preset) => {
    if (categoryFilter && preset.category !== categoryFilter) return false;
    return presetMatchesSearch(preset, presetSearch);
  });

  if (isLoading) {
    return (
      <div className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm font-semibold text-muted-foreground">
        Loading retrieval presets
      </div>
    );
  }

  if (!presets.length) {
    return (
      <Notice title="No retrieval presets">
        Add presets under the trusted knowledge directory to seed the query builder.
      </Notice>
    );
  }

  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Search presets
        </div>
        <Badge variant="muted">
          {filteredPresets.length}/{presets.length} data-driven
        </Badge>
      </div>
      <div className="grid gap-2">
        <Input
          aria-label="Filter retrieval presets"
          onChange={(event) => setPresetSearch(event.target.value)}
          placeholder="Filter presets"
          value={presetSearch}
        />
        {categories.length ? (
          <div className="flex min-w-0 flex-wrap gap-2" aria-label="Preset categories">
            <button
              aria-pressed={!categoryFilter}
              className={presetFilterClass(!categoryFilter)}
              onClick={() => setCategoryFilter(null)}
              type="button"
            >
              All
            </button>
            {categories.map((category) => {
              const active = categoryFilter === category;
              return (
                <button
                  aria-pressed={active}
                  className={presetFilterClass(active)}
                  key={category}
                  onClick={() => setCategoryFilter(category)}
                  type="button"
                >
                  {humanize(category)}
                </button>
              );
            })}
          </div>
        ) : null}
      </div>
      <div className="grid gap-2">
        {filteredPresets.length ? null : (
          <Notice title="No matching presets">
            Adjust the preset filter or category to show trusted retrieval examples.
          </Notice>
        )}
        {filteredPresets.map((preset) => {
          const active = activePresetId === preset.preset_id;
          return (
            <button
              aria-pressed={active}
              className={cn(
                "grid min-w-0 gap-1 rounded-md border px-3 py-2 text-left text-sm transition-colors",
                active
                  ? "border-primary bg-primary/10 text-foreground"
                  : "border-border bg-card hover:bg-muted",
              )}
              key={preset.preset_id}
              onClick={() => onApplyPreset(preset)}
              title={preset.description}
              type="button"
            >
              <span className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <span className="flex min-w-0 flex-wrap items-center gap-2">
                  <span className="break-words font-black">{preset.label}</span>
                  {preset.category ? (
                    <span className="rounded-full bg-muted px-2 py-1 text-xs font-bold text-muted-foreground">
                      {humanize(preset.category)}
                    </span>
                  ) : null}
                </span>
                <span className="rounded-full bg-muted px-2 py-1 text-xs font-bold text-muted-foreground">
                  top {preset.top_k}
                </span>
              </span>
              <span className="break-words text-xs leading-5 text-muted-foreground">
                {preset.description}
              </span>
              {preset.target_sources.length || preset.launch_hint_targets.length ? (
                <span className="flex min-w-0 flex-wrap gap-1 pt-1">
                  {preset.target_sources.slice(0, 3).map((source) => (
                    <span
                      className="rounded-full border border-border bg-background px-2 py-1 text-[11px] font-bold text-muted-foreground"
                      key={source}
                    >
                      {source}
                    </span>
                  ))}
                  {preset.launch_hint_targets.slice(0, 2).map((target) => (
                    <span
                      className="rounded-full border border-border bg-background px-2 py-1 text-[11px] font-bold text-muted-foreground"
                      key={target}
                    >
                      {humanize(target)}
                    </span>
                  ))}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function SearchResults({
  activeFilters,
  isSearchPending,
  isStale,
  onApplyFacet,
  onSetJudgment,
  onRestoreSubmittedSearch,
  packageData,
  persistedJudgmentSummary,
  persistedJudgmentEvaluation,
  isJudgmentSyncing,
  relevanceJudgments,
  runId,
  submittedSearchPayload,
}: {
  activeFilters: ActiveFacetFilters;
  isSearchPending: boolean;
  isStale: boolean;
  onApplyFacet: (field: SupportedFilterField, value: string) => void;
  onSetJudgment: (evidence: Evidence, value: RelevanceJudgmentValue) => void;
  onRestoreSubmittedSearch: () => void;
  packageData: RetrievalPackage | undefined;
  persistedJudgmentSummary: RetrievalRelevanceJudgmentSummary | null;
  persistedJudgmentEvaluation: RetrievalJudgmentEvaluationResult | null;
  isJudgmentSyncing: boolean;
  relevanceJudgments: RelevanceJudgmentIndex;
  runId: string | null;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
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

  const resultFilters = submittedSearchPayload
    ? activeFacetFiltersFromPayload(submittedSearchPayload)
    : activeFilters;
  const diversitySelections = diversitySelectionByEvidenceId(packageData);
  const runJudgments = runId
    ? judgmentsForRunHits(runId, packageData.hits, relevanceJudgments)
    : [];
  const judgmentMetrics = relevanceJudgmentMetrics(packageData.hits, runJudgments);

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
          {isStale ? <Badge variant="warning">pending changes</Badge> : null}
          <Badge variant="muted">{packageData.trace.strategy}</Badge>
          <DiversityBadge packageData={packageData} />
          <RerankBadge packageData={packageData} />
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        {submittedSearchPayload ? (
          <SubmittedSearchSummary
            isRestoreDisabled={isSearchPending}
            isStale={isStale}
            onRestore={onRestoreSubmittedSearch}
            payload={submittedSearchPayload}
          />
        ) : null}
        <RelevanceJudgmentSummary
          isSyncing={isJudgmentSyncing}
          metrics={judgmentMetrics}
          packageData={packageData}
          persistedEvaluation={persistedJudgmentEvaluation}
          persistedSummary={persistedJudgmentSummary}
        />
        <ResultFacets
          activeFilters={resultFilters}
          facets={packageData.facets}
          isSearchPending={isSearchPending}
          onApplyFacet={onApplyFacet}
        />
        {packageData.hits.map((hit, index) => (
          <HitCard
            diversitySelection={diversitySelections.get(hit.evidence.evidence_id) ?? null}
            hit={hit}
            index={index}
            judgment={
              runId
                ? relevanceJudgments[
                    relevanceJudgmentKey(runId, hit.evidence.evidence_id)
                  ] ?? null
                : null
            }
            key={hit.evidence.evidence_id}
            onSetJudgment={(value) => onSetJudgment(hit.evidence, value)}
          />
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

function ResultFacets({
  activeFilters,
  facets,
  isSearchPending,
  onApplyFacet,
}: {
  activeFilters: ActiveFacetFilters;
  facets: RetrievalFacets | null | undefined;
  isSearchPending: boolean;
  onApplyFacet: (field: SupportedFilterField, value: string) => void;
}) {
  if (!facets) return null;
  const facetSections: FacetSection[] = [
    { field: "source_type", label: "Source type", values: facets.source_type, formatter: humanize },
    { field: "clinical_domain", label: "Domain", values: facets.clinical_domain, formatter: humanize },
    { field: "standard_system", label: "Standard", values: facets.standard_system, formatter: (value: string) => value },
    { field: "trust_level", label: "Trust", values: facets.trust_level, formatter: humanize },
  ];
  const sections = facetSections.filter((section) => section.values.length > 0);
  if (!sections.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Result facets
        </div>
        <Badge variant="muted">click to refine</Badge>
      </div>
      <div className="grid gap-2 lg:grid-cols-2">
        {sections.map((section) => (
          <div className="grid gap-1.5" key={section.label}>
            <div className="text-xs font-bold text-muted-foreground">{section.label}</div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {section.values.map((bucket) => {
                const applied = activeFilters[section.field] === bucket.value;
                return (
                  <button
                    aria-label={`Filter by ${section.label} ${section.formatter(bucket.value)}`}
                    aria-pressed={applied}
                    className={cn(
                      "inline-flex max-w-full items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-bold transition-colors focus-ring disabled:cursor-not-allowed disabled:opacity-70",
                      applied
                        ? "border-emerald-200 bg-emerald-100 text-emerald-900"
                        : "border-border bg-card text-muted-foreground hover:border-primary/40 hover:bg-primary/10 hover:text-foreground",
                    )}
                    disabled={applied || isSearchPending}
                    key={`${section.label}-${bucket.value}`}
                    onClick={() => onApplyFacet(section.field, bucket.value)}
                    title={
                      applied
                        ? `${section.formatter(bucket.value)} is already applied`
                        : `Apply ${section.label}=${section.formatter(bucket.value)}`
                    }
                    type="button"
                  >
                    {isSearchPending && !applied ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <ListFilter className="h-3 w-3" />
                    )}
                    <span className="break-words">{section.formatter(bucket.value)}</span>
                    <span className="tabular-nums text-foreground">{bucket.count}</span>
                    {applied ? <span>applied</span> : null}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RelevanceJudgmentSummary({
  isSyncing,
  metrics,
  packageData,
  persistedEvaluation,
  persistedSummary,
}: {
  isSyncing: boolean;
  metrics: RelevanceJudgmentMetrics;
  packageData: RetrievalPackage;
  persistedEvaluation: RetrievalJudgmentEvaluationResult | null;
  persistedSummary: RetrievalRelevanceJudgmentSummary | null;
}) {
  const copyEvaluationReport = async () => {
    if (!persistedEvaluation) return;
    await copyTextToClipboard(
      JSON.stringify(
        evaluationReportFromJudgmentSummary(
          persistedEvaluation,
          metrics,
          persistedSummary,
          packageData,
        ),
        null,
        2,
      ),
    );
  };

  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Judgment metrics
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={metrics.judgedCount ? "success" : "muted"}>
            {formatCount(metrics.judgedCount, "judged hit")}
          </Badge>
          {persistedSummary ? (
            <Badge variant={persistedSummary.total_count ? "success" : "muted"}>
              {formatCount(persistedSummary.total_count, "stored label")}
            </Badge>
          ) : null}
          {persistedEvaluation ? (
            <Badge variant={persistedEvaluation.judged_count ? "success" : "warning"}>
              server eval {formatCount(persistedEvaluation.judged_count, "judged")}
            </Badge>
          ) : null}
          {isSyncing ? <Badge variant="warning">syncing</Badge> : null}
          {persistedEvaluation ? (
            <Button
              aria-label="Copy retrieval judgment evaluation report"
              onClick={() => void copyEvaluationReport()}
              size="sm"
              type="button"
              variant="outline"
            >
              <Clipboard className="h-4 w-4" />
              Copy eval
            </Button>
          ) : null}
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <JudgmentMetricCard
          label="Coverage"
          tone={metrics.judgmentCoverage >= 0.5 ? "success" : "warning"}
          value={formatPercent(metrics.judgmentCoverage)}
        />
        <JudgmentMetricCard
          label="Precision@k"
          tone={metrics.precisionAtK >= 0.5 ? "success" : "warning"}
          value={formatPercent(metrics.precisionAtK)}
        />
        <JudgmentMetricCard
          label="Judged precision"
          tone={(metrics.judgedPrecision ?? 0) >= 0.5 ? "success" : "warning"}
          value={formatNullablePercent(metrics.judgedPrecision)}
        />
        <JudgmentMetricCard
          label="nDCG@k"
          tone={(metrics.ndcgAtK ?? 0) >= 0.5 ? "success" : "warning"}
          value={formatNullableDecimal(metrics.ndcgAtK)}
        />
      </div>
      {persistedEvaluation ? (
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          <JudgmentMetricCard
            label="Server coverage"
            tone={persistedEvaluation.coverage_at_k >= 0.5 ? "success" : "warning"}
            value={formatPercent(persistedEvaluation.coverage_at_k)}
          />
          <JudgmentMetricCard
            label="Server HitRate@k"
            tone={persistedEvaluation.hit_rate_at_k >= 1 ? "success" : "warning"}
            value={formatPercent(persistedEvaluation.hit_rate_at_k)}
          />
          <JudgmentMetricCard
            label="Server MAP@k"
            tone={persistedEvaluation.average_precision_at_k >= 0.5 ? "success" : "warning"}
            value={formatDecimal(persistedEvaluation.average_precision_at_k)}
          />
          <JudgmentMetricCard
            label="Server MRR@k"
            tone={persistedEvaluation.mrr_at_k >= 0.5 ? "success" : "warning"}
            value={formatDecimal(persistedEvaluation.mrr_at_k)}
          />
          <JudgmentMetricCard
            label="Server nDCG@k"
            tone={(persistedEvaluation.ndcg_at_k ?? 0) >= 0.5 ? "success" : "warning"}
            value={formatNullableDecimal(persistedEvaluation.ndcg_at_k ?? null)}
          />
          <JudgmentMetricCard
            label="Server unjudged"
            tone={persistedEvaluation.unjudged_count ? "warning" : "success"}
            value={formatCount(persistedEvaluation.unjudged_count, "hit")}
          />
        </div>
      ) : null}
      {persistedEvaluation?.recommendations.length ? (
        <div className="grid gap-2">
          <div className="text-xs font-bold uppercase text-muted-foreground">
            Evaluation recommendations
          </div>
          {persistedEvaluation.recommendations.map((recommendation) => {
            const warning =
              recommendation.severity === "warning" ||
              recommendation.severity === "destructive" ||
              recommendation.severity === "error";
            return (
              <div
                className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
                key={recommendation.rule_id}
              >
                <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                  <span className="flex min-w-0 items-center gap-1.5">
                    {warning ? (
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600" />
                    ) : (
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                    )}
                    <span className="break-words font-bold">
                      {humanize(recommendation.rule_id)}
                    </span>
                  </span>
                  <Badge variant={qualitySignalBadgeVariant(recommendation.severity)}>
                    {recommendation.metric}
                  </Badge>
                </div>
                <div className="break-words text-muted-foreground">
                  {recommendation.message}
                </div>
                <div className="break-words font-semibold text-foreground">
                  {recommendation.suggested_action}
                </div>
                {recommendation.evidence_ids.length ? (
                  <div className="flex min-w-0 flex-wrap gap-1">
                    {recommendation.evidence_ids.slice(0, 4).map((evidenceId) => (
                      <code
                        className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px]"
                        key={`${recommendation.rule_id}-${evidenceId}`}
                      >
                        {evidenceId}
                      </code>
                    ))}
                    {recommendation.evidence_ids.length > 4 ? (
                      <span className="text-xs font-semibold text-muted-foreground">
                        +{recommendation.evidence_ids.length - 4} more
                      </span>
                    ) : null}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}
      {metrics.judgedCount ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          <Badge variant="success">{formatCount(metrics.relevantCount, "relevant")}</Badge>
          <Badge variant="warning">{formatCount(metrics.partialCount, "partial")}</Badge>
          <Badge variant="destructive">
            {formatCount(metrics.notRelevantCount, "not relevant")}
          </Badge>
          <Badge variant="muted">
            average rating {formatNullableDecimal(metrics.averageRating)}
          </Badge>
          {persistedSummary?.latest_updated_at ? (
            <Badge variant="muted">
              stored avg {formatNullableDecimal(persistedSummary.average_rating ?? null)}
            </Badge>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function JudgmentMetricCard({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "success" | "warning";
  value: string;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2">
      <span className="text-xs font-bold text-muted-foreground">{label}</span>
      <Badge variant={tone}>{value}</Badge>
    </div>
  );
}

function SubmittedSearchSummary({
  isRestoreDisabled,
  isStale,
  onRestore,
  payload,
}: {
  isRestoreDisabled: boolean;
  isStale: boolean;
  onRestore: () => void;
  payload: RetrievalSearchPayload;
}) {
  const filters = activeFilterEntries(activeFacetFiltersFromPayload(payload));
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">Submitted search</div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={isStale ? "warning" : "success"}>
            {isStale ? "displayed request" : "current request"}
          </Badge>
          {isStale ? (
            <Button
              disabled={isRestoreDisabled}
              onClick={onRestore}
              size="sm"
              title="Restore submitted search"
              type="button"
              variant="outline"
            >
              <RefreshCw className="h-4 w-4" />
              Restore
            </Button>
          ) : null}
        </div>
      </div>
      <div className="grid gap-2 text-sm">
        <div className="break-words font-semibold">{payload.query}</div>
        <div className="flex min-w-0 flex-wrap gap-1.5">
          <Badge variant="muted">top {payload.top_k}</Badge>
          {payload.schema_id ? <Badge variant="muted">{payload.schema_id}</Badge> : null}
          {payload.detected_format ? <Badge variant="muted">{humanize(payload.detected_format)}</Badge> : null}
          {payload.resource_type ? <Badge variant="muted">{payload.resource_type}</Badge> : null}
          {payload.fields.slice(0, 8).map((field) => (
            <span
              className="max-w-full break-words rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground"
              key={field}
            >
              {field}
            </span>
          ))}
          {payload.fields.length > 8 ? (
            <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
              +{payload.fields.length - 8} fields
            </span>
          ) : null}
        </div>
        {filters.length ? (
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {filters.map((filter) => (
              <span
                className="max-w-full break-words rounded-full border border-primary/20 bg-primary/10 px-2 py-1 text-xs font-bold text-foreground"
                key={filter.field}
              >
                {filter.label}: {filter.displayValue}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function ActiveFilterBar({
  filters,
  isSearchPending,
  onClearAll,
  onRemove,
}: {
  filters: ActiveFilterEntry[];
  isSearchPending: boolean;
  onClearAll: () => void;
  onRemove: (field: SupportedFilterField) => void;
}) {
  if (!filters.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">Active filters</div>
        <Button
          disabled={isSearchPending}
          onClick={onClearAll}
          size="sm"
          type="button"
          variant="ghost"
        >
          Clear all
        </Button>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {filters.map((filter) => (
          <span
            className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-primary/25 bg-primary/10 px-2 py-1 text-xs font-bold text-foreground"
            key={filter.field}
          >
            <span className="min-w-0 break-words">
              {filter.label}: {filter.displayValue}
            </span>
            <button
              aria-label={`Remove ${filter.label} filter`}
              className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-card hover:text-foreground focus-ring disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSearchPending}
              onClick={() => onRemove(filter.field)}
              title={`Remove ${filter.label} filter`}
              type="button"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}

function activeFacetFiltersFromPayload(payload: RetrievalSearchPayload): ActiveFacetFilters {
  return {
    clinical_domain: payload.clinical_domain || undefined,
    standard_system: payload.standard_system || undefined,
    source_type: payload.source_type || undefined,
    trust_level: payload.trust_level || undefined,
  };
}

function activeFilterEntries(filters: ActiveFacetFilters): ActiveFilterEntry[] {
  return Array.from(supportedSuggestionFilterFields)
    .map((field) => {
      const value = filters[field];
      if (!value) return null;
      return {
        field,
        label: filterFieldLabel(field),
        displayValue: formatFilterValue(field, value),
      };
    })
    .filter((entry): entry is ActiveFilterEntry => entry !== null);
}

function filterFieldLabel(field: SupportedFilterField): string {
  if (field === "clinical_domain") return "Domain";
  if (field === "standard_system") return "Standard";
  if (field === "source_type") return "Source";
  return "Trust";
}

function formatFilterValue(field: SupportedFilterField, value: string): string {
  return field === "standard_system" ? value : humanize(value);
}

function coverageSuggestedFilter(
  item: RetrievalCoverage["standard_system"][number],
): CoverageFilterAction | null {
  const suggestedFilter = recordValue(item.suggested_filter);
  for (const [field, rawValue] of Object.entries(suggestedFilter)) {
    const value = stringValue(rawValue, "");
    if (value && isSupportedFilterField(field)) return { field, value };
  }
  return null;
}

function coverageSuggestedAction(item: RetrievalCoverage["standard_system"][number]): string {
  return stringValue(item.suggested_action, item.reason);
}

function isSupportedFilterField(value: string): value is SupportedFilterField {
  return supportedSuggestionFilterFields.has(value as SupportedFilterField);
}

function HitCard({
  diversitySelection,
  hit,
  index,
  judgment,
  onSetJudgment,
}: {
  diversitySelection: DiversitySelectionStack | null;
  hit: RetrievalHit;
  index: number;
  judgment: RelevanceJudgment | null;
  onSetJudgment: (value: RelevanceJudgmentValue) => void;
}) {
  const evidence = hit.evidence;
  const aspectMatches = queryAspectMatchesFromHit(hit);
  const rankingBoostSignals = rankingBoostSignalsFromHit(hit);
  const scoreComponents = scoreComponentsFromHit(hit);
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

      <RelevanceJudgmentControl judgment={judgment} onSetJudgment={onSetJudgment} />

      <div className="grid gap-2 md:grid-cols-3">
        <ScoreMeter label="Lexical" value={hit.lexical_score} />
        <ScoreMeter label="Vector" value={hit.vector_score} />
        <ScoreMeter label="Rerank" value={hit.rerank_score} />
      </div>

      <ScoreExplanation components={scoreComponents} />

      <DiversitySelectionExplanation selection={diversitySelection} />

      <QueryAspectMatchExplanation matches={aspectMatches} />

      {rankingBoostSignals.length ? (
        <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
          <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
            <Gauge className="h-3.5 w-3.5 shrink-0" />
            <span>Ranking signals</span>
          </div>
          <div className="grid gap-1.5">
            {rankingBoostSignals.map((signal) => (
              <div
                className="flex min-w-0 flex-wrap items-center gap-1.5 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs"
                key={signal.ruleId}
              >
                <Badge className="max-w-full break-words" variant="muted">
                  {signal.label}
                </Badge>
                {signal.weight !== null ? (
                  <span className="font-mono font-semibold text-muted-foreground">
                    +{formatScore(signal.weight)}
                  </span>
                ) : null}
                <span className="min-w-0 flex-1 break-words font-semibold text-muted-foreground">
                  {signal.reason}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

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

function RelevanceJudgmentControl({
  judgment,
  onSetJudgment,
}: {
  judgment: RelevanceJudgment | null;
  onSetJudgment: (value: RelevanceJudgmentValue) => void;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Relevance judgment
        </div>
        {judgment ? (
          <Badge variant={judgmentBadgeVariant(judgment.value)}>
            {judgmentLabel(judgment.value)}
          </Badge>
        ) : (
          <Badge variant="muted">unjudged</Badge>
        )}
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {relevanceJudgmentOptions.map((option) => {
          const active = judgment?.value === option.value;
          return (
            <Button
              aria-pressed={active}
              key={option.value}
              onClick={() => onSetJudgment(option.value)}
              size="sm"
              title={active ? "Clear this relevance judgment" : option.description}
              type="button"
              variant={active ? option.activeVariant : "outline"}
            >
              {option.label}
            </Button>
          );
        })}
      </div>
    </div>
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

function ScoreExplanation({ components }: { components: RetrievalScoreComponent[] }) {
  if (!components.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Gauge className="h-3.5 w-3.5 shrink-0" />
        <span>Score explanation</span>
      </div>
      <div className="grid gap-1.5">
        {components.map((component) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs md:grid-cols-[10rem_5rem_minmax(0,1fr)] md:items-center"
            key={component.component}
          >
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <span className="min-w-0 break-words font-bold">{component.label}</span>
              {component.rank ? <Badge variant="muted">rank {component.rank}</Badge> : null}
            </div>
            <span className="font-mono font-semibold tabular-nums text-muted-foreground">
              {formatScore(component.value)}
            </span>
            <span className="min-w-0 break-words font-semibold text-muted-foreground">
              {component.description}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DiversitySelectionExplanation({
  selection,
}: {
  selection: DiversitySelectionStack | null;
}) {
  if (!selection) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Network className="h-3.5 w-3.5 shrink-0" />
        <span>Diversity selection</span>
      </div>
      <div className="grid gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <Badge variant="muted">selected #{selection.selectedRank}</Badge>
          <Badge variant="muted">original #{selection.originalRank}</Badge>
          <span className="font-mono font-semibold text-muted-foreground">
            relevance {formatScore(selection.relevanceScore)}
          </span>
          <span className="font-mono font-semibold text-muted-foreground">
            redundancy {formatScore(selection.redundancyScore)}
          </span>
          <span className="font-mono font-semibold text-muted-foreground">
            MMR {formatScore(selection.selectionScore)}
          </span>
        </div>
        <div className="break-words font-semibold text-muted-foreground">
          {selection.reason}
        </div>
      </div>
    </div>
  );
}

function QueryAspectMatchExplanation({ matches }: { matches: QueryAspectMatchSignal[] }) {
  if (!matches.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <ListFilter className="h-3.5 w-3.5 shrink-0" />
        <span>Aspect support</span>
      </div>
      <div className="grid gap-1.5">
        {matches.map((match) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs"
            key={`${match.aspectId}-${match.ruleId}`}
          >
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge className="max-w-full break-words" variant="success">
                {match.label}
              </Badge>
              <Badge variant="muted">priority {match.priority}</Badge>
              <span className="min-w-0 break-words font-semibold text-muted-foreground">
                {match.reason}
              </span>
            </div>
            {match.matchedTerms.length || Object.keys(match.matchedFilters).length ? (
              <div className="flex min-w-0 flex-wrap gap-1">
                {Object.entries(match.matchedFilters).map(([field, value]) => (
                  <span
                    className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                    key={`${match.aspectId}-${field}`}
                  >
                    {humanize(field)}: {value}
                  </span>
                ))}
                {match.matchedTerms.slice(0, 4).map((term) => (
                  <span
                    className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                    key={`${match.aspectId}-${term}`}
                  >
                    {term}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function TracePanel({
  isSearchPending,
  onApplyCoverageFilter,
  onApplyFilterSuggestion,
  packageData,
}: {
  isSearchPending: boolean;
  onApplyCoverageFilter: (field: SupportedFilterField, value: string) => void;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
  packageData: RetrievalPackage | undefined;
}) {
  const trace = packageData?.trace;
  const stack = packageData ? rankingStackFromPackage(packageData) : null;
  const diversity = packageData ? diversityFromPackage(packageData) : null;
  const qualityPolicy = packageData ? qualityPolicyFromPackage(packageData) : null;
  const queryAnalysis = packageData ? queryAnalysisFromPackage(packageData) : null;
  const coverage = packageData?.coverage;
  const qualitySignals = packageData?.quality_signals ?? [];
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
              label="Framework"
              value={stack ? formatFrameworkStack(stack) : "unknown"}
            />
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
              label="Quality policy"
              value={qualityPolicy ? formatQualityPolicyTrace(qualityPolicy) : "unknown"}
            />
            <TraceFact
              label="Filters"
              value={Object.keys(trace.filters_applied).length ? JSON.stringify(trace.filters_applied) : "none"}
            />
            <QualitySignalList signals={qualitySignals} />
            <QueryAnalysisBlock
              analysis={queryAnalysis}
              appliedFilters={trace.filters_applied}
              isSearchPending={isSearchPending}
              onApplyFilterSuggestion={onApplyFilterSuggestion}
            />
            <CoverageDiagnosticsBlock
              coverage={coverage}
              isSearchPending={isSearchPending}
              onApplyCoverageFilter={onApplyCoverageFilter}
            />
            <QueryVariantList variants={queryVariantsFromTrace(trace)} />
            <TokenList items={trace.safety_flags.map(humanize)} title="Safety flags" tone="warning" />
            <TokenList items={trace.warnings} title="Warnings" tone="warning" />
          </>
        )}
      </CardContent>
    </Card>
  );
}

function QualitySignalList({ signals }: { signals: RetrievalQualitySignal[] }) {
  if (!signals.length) {
    return <TokenList items={[]} title="Retrieval quality" />;
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Retrieval quality
        </div>
        <Badge variant={qualitySignalSummaryVariant(signals)}>
          {formatCount(signals.length, "signal")}
        </Badge>
      </div>
      <div className="grid gap-2">
        {signals.map((signal) => {
          const warning = signal.severity === "warning" || signal.severity === "destructive";
          return (
            <div
              className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
              key={signal.code}
            >
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <span className="flex min-w-0 items-center gap-1.5">
                  {warning ? (
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600" />
                  ) : (
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                  )}
                  <span className="break-words font-bold">{humanize(signal.code)}</span>
                </span>
                <Badge variant={qualitySignalBadgeVariant(signal.severity)}>
                  {humanize(signal.severity)}
                </Badge>
              </div>
              <div className="break-words text-muted-foreground">{signal.message}</div>
              <div className="break-words font-semibold text-foreground">
                {signal.suggested_action}
              </div>
              {signal.evidence_ids.length ? (
                <div className="flex min-w-0 flex-wrap gap-1">
                  {signal.evidence_ids.slice(0, 4).map((evidenceId) => (
                    <code
                      className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px]"
                      key={`${signal.code}-${evidenceId}`}
                    >
                      {evidenceId}
                    </code>
                  ))}
                  {signal.evidence_ids.length > 4 ? (
                    <span className="rounded bg-muted px-1.5 py-1 font-bold text-muted-foreground">
                      +{signal.evidence_ids.length - 4}
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CoverageDiagnosticsBlock({
  coverage,
  isSearchPending,
  onApplyCoverageFilter,
}: {
  coverage: RetrievalCoverage | null | undefined;
  isSearchPending: boolean;
  onApplyCoverageFilter: (field: SupportedFilterField, value: string) => void;
}) {
  const standardItems = coverage?.standard_system ?? [];
  const aspectItems = coverage?.query_aspects ?? [];
  const warningCount = coverage?.warnings.length ?? 0;
  if (!standardItems.length && !aspectItems.length) {
    return <TokenList items={[]} title="Coverage diagnostics" />;
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Coverage diagnostics
        </div>
        <Badge variant={warningCount ? "warning" : "success"}>
          {warningCount ? `${warningCount} gap` : "covered"}
        </Badge>
      </div>
      <CoverageItemList
        isSearchPending={isSearchPending}
        items={standardItems}
        label="Standard coverage"
        onApplyCoverageFilter={onApplyCoverageFilter}
      />
      <CoverageItemList
        isSearchPending={isSearchPending}
        items={aspectItems}
        label="Aspect coverage"
        onApplyCoverageFilter={onApplyCoverageFilter}
      />
    </div>
  );
}

function CoverageItemList({
  isSearchPending,
  items,
  label,
  onApplyCoverageFilter,
}: {
  isSearchPending: boolean;
  items: RetrievalCoverage["standard_system"];
  label: string;
  onApplyCoverageFilter: (field: SupportedFilterField, value: string) => void;
}) {
  if (!items.length) return null;
  return (
    <div className="grid gap-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        {label}
      </div>
      {items.map((item) => {
        const suggestedFilter = coverageSuggestedFilter(item);
        const actionable = item.status !== "covered" && suggestedFilter !== null;
        return (
          <div
            className="grid gap-2 rounded-md border border-border bg-card p-2 text-xs"
            key={`${label}-${item.field}-${item.value}`}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{humanize(item.value)}</span>
              <Badge variant={item.status === "covered" ? "success" : "warning"}>
                {item.status} / {item.selected_count}
              </Badge>
            </div>
            <div className="break-words text-muted-foreground">{item.reason}</div>
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md bg-muted/40 px-2 py-1.5">
              <span className="min-w-0 flex-1 break-words font-semibold text-foreground">
                {coverageSuggestedAction(item)}
              </span>
              {actionable ? (
                <Button
                  disabled={isSearchPending}
                  onClick={() =>
                    onApplyCoverageFilter(suggestedFilter.field, suggestedFilter.value)
                  }
                  size="sm"
                  title={`Apply ${filterFieldLabel(suggestedFilter.field)}=${formatFilterValue(
                    suggestedFilter.field,
                    suggestedFilter.value,
                  )}`}
                  type="button"
                  variant="outline"
                >
                  {isSearchPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ListFilter className="h-4 w-4" />
                  )}
                  Apply {filterFieldLabel(suggestedFilter.field)}
                </Button>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function QueryVariantList({ variants }: { variants: RetrievalQueryVariant[] }) {
  if (!variants.length) {
    return <TokenList items={[]} title="Query rewrites" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Query rewrites
      </div>
      <div className="grid gap-2">
        {variants.map((variant, index) => (
          <div
            className="grid gap-1 rounded-md border border-border bg-card p-2 text-xs"
            key={`${variant.source}-${variant.variant}-${index}`}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <code className="min-w-0 break-words rounded bg-muted px-2 py-1 font-mono">
                {variant.variant}
              </code>
              <Badge variant="muted">{humanize(variant.source)}</Badge>
            </div>
            <div className="break-words font-semibold text-muted-foreground">
              {variant.reason}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function QueryAnalysisBlock({
  analysis,
  appliedFilters,
  isSearchPending,
  onApplyFilterSuggestion,
}: {
  analysis: QueryAnalysisStack | null;
  appliedFilters: Record<string, unknown>;
  isSearchPending: boolean;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
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
      <QueryProfileCard
        appliedFilters={appliedFilters}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilterSuggestion}
        profile={analysis.queryProfile}
      />
      <QueryAspectPlan
        appliedFilters={appliedFilters}
        aspects={analysis.queryAspects}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilterSuggestion}
      />
      <QueryDiagnosticList diagnostics={analysis.diagnostics} />
      <ConceptCandidateList candidates={analysis.conceptCandidates} />
      <SearchHintList hints={analysis.searchHints} />
      <TokenList items={analysis.detectedConcepts.map(humanize)} title="Detected concepts" />
      <TokenList items={analysis.standards} title="Standard cues" />
      <FilterSuggestionList
        isSearchPending={isSearchPending}
        onApplySuggestion={onApplyFilterSuggestion}
        suggestions={analysis.filterSuggestions}
      />
      <TokenList items={analysis.expandedTerms} title="Expanded terms" />
    </div>
  );
}

function QueryAspectPlan({
  appliedFilters,
  aspects,
  isSearchPending,
  onApplyFilter,
}: {
  appliedFilters: Record<string, unknown>;
  aspects: QueryAspectStack[];
  isSearchPending: boolean;
  onApplyFilter: (suggestion: FilterSuggestionStack) => void;
}) {
  if (!aspects.length) {
    return <TokenList items={[]} title="Search aspect plan" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Search aspect plan
        </div>
        <Badge variant="muted">{formatCount(aspects.length, "aspect")}</Badge>
      </div>
      <div className="grid gap-2">
        {aspects.map((aspect) => {
          const filterEntries = queryAspectFilterEntries(aspect, appliedFilters);
          return (
            <div
              className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
              key={aspect.aspectId}
            >
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <span className="break-words font-bold">{aspect.label}</span>
                <Badge variant="muted">priority {aspect.priority}</Badge>
              </div>
              <div className="break-words font-semibold text-foreground">
                {aspect.question}
              </div>
              <div className="break-words text-muted-foreground">
                {aspect.rationale}
              </div>
              {aspect.suggestedTerms.length ? (
                <div className="flex min-w-0 flex-wrap gap-1">
                  {aspect.suggestedTerms.slice(0, 5).map((term) => (
                    <Badge key={`${aspect.aspectId}-${term}`} variant="muted">
                      {term}
                    </Badge>
                  ))}
                  {aspect.suggestedTerms.length > 5 ? (
                    <Badge variant="muted">+{aspect.suggestedTerms.length - 5}</Badge>
                  ) : null}
                </div>
              ) : null}
              {filterEntries.length ? (
                <div className="flex min-w-0 flex-wrap gap-1">
                  {filterEntries.map((entry) => (
                    <Badge
                      key={`${aspect.aspectId}-${entry.field}`}
                      variant={entry.applied ? "success" : "muted"}
                    >
                      {entry.label}={entry.displayValue}
                    </Badge>
                  ))}
                </div>
              ) : null}
              {filterEntries.length ? (
                <div className="flex min-w-0 flex-wrap gap-1.5">
                  {filterEntries.map((entry) =>
                    entry.supported ? (
                      <Button
                        disabled={isSearchPending || entry.applied}
                        key={`${aspect.aspectId}-${entry.field}-${entry.value}-apply`}
                        onClick={() =>
                          onApplyFilter({
                            applied: false,
                            confidence: 1,
                            field: entry.field,
                            reason: `Suggested by search aspect ${aspect.aspectId}.`,
                            value: entry.value,
                          })
                        }
                        size="sm"
                        title={`Apply ${entry.label}=${entry.displayValue}`}
                        type="button"
                        variant={entry.applied ? "secondary" : "outline"}
                      >
                        {entry.applied ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : isSearchPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <ListFilter className="h-4 w-4" />
                        )}
                        {entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`}
                      </Button>
                    ) : (
                      <Badge
                        key={`${aspect.aspectId}-${entry.field}-${entry.value}-unsupported`}
                        variant="warning"
                      >
                        unsupported {humanize(entry.field)}
                      </Badge>
                    ),
                  )}
                </div>
              ) : null}
              <code className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px] text-muted-foreground">
                {aspect.ruleId}
              </code>
            </div>
          );
        })}
      </div>
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

function QueryProfileCard({
  appliedFilters,
  isSearchPending,
  onApplyFilter,
  profile,
}: {
  appliedFilters: Record<string, unknown>;
  isSearchPending: boolean;
  onApplyFilter: (suggestion: FilterSuggestionStack) => void;
  profile: QueryProfileStack | null;
}) {
  if (!profile) {
    return <TokenList items={[]} title="Query profile" />;
  }
  const filterEntries = queryProfileFilterEntries(profile, appliedFilters);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="break-words font-bold">{profile.label}</span>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant="default">{humanize(profile.complexity)}</Badge>
          <Badge variant="muted">{humanize(profile.route)}</Badge>
        </div>
      </div>
      <div className="break-words text-muted-foreground">{profile.description}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant="muted">{humanize(profile.retrievalMode)}</Badge>
        {filterEntries.map((entry) => (
          <Badge
            key={`${entry.field}-${entry.value}`}
            variant={entry.applied ? "success" : "muted"}
          >
            {entry.label}={entry.displayValue}
          </Badge>
        ))}
      </div>
      {filterEntries.length ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {filterEntries.map((entry) =>
            entry.supported ? (
              <Button
                disabled={isSearchPending || entry.applied}
                key={`${entry.field}-${entry.value}-apply`}
                onClick={() =>
                  onApplyFilter({
                    applied: false,
                    confidence: 1,
                    field: entry.field,
                    reason: `Suggested by query profile ${profile.profileId}.`,
                    value: entry.value,
                  })
                }
                size="sm"
                title={`Apply ${entry.label}=${entry.displayValue}`}
                type="button"
                variant={entry.applied ? "secondary" : "outline"}
              >
                {entry.applied ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : isSearchPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ListFilter className="h-4 w-4" />
                )}
                {entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`}
              </Button>
            ) : (
              <Badge key={`${entry.field}-${entry.value}-unsupported`} variant="warning">
                unsupported {humanize(entry.field)}
              </Badge>
            ),
          )}
        </div>
      ) : null}
      {profile.ruleIds.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {profile.ruleIds.map((ruleId) => (
            <code
              className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px]"
              key={ruleId}
            >
              {ruleId}
            </code>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function SearchHintList({ hints }: { hints: SearchHintStack[] }) {
  const [copiedHintKey, setCopiedHintKey] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!copiedHintKey) return;
    const timer = window.setTimeout(() => setCopiedHintKey(null), 1800);
    return () => window.clearTimeout(timer);
  }, [copiedHintKey]);

  const copyHintQuery = async (hintKey: string, query: string) => {
    try {
      await copyTextToClipboard(query);
      setCopiedHintKey(hintKey);
    } catch {
      setCopiedHintKey(null);
    }
  };

  if (!hints.length) {
    return <TokenList items={[]} title="Medical search hints" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Medical search hints
      </div>
      <div className="grid gap-2">
        {hints.map((hint) => {
          const hintKey = `${hint.target}-${hint.query}`;
          const copied = copiedHintKey === hintKey;
          return (
            <div
              className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
              key={hintKey}
            >
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <span className="break-words font-bold">{humanize(hint.target)}</span>
                <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
                  <Badge variant={hint.url ? "success" : "muted"}>
                    {hint.url ? "launchable hint" : "syntax hint"}
                  </Badge>
                  <Button
                    onClick={() => void copyHintQuery(hintKey, hint.query)}
                    size="sm"
                    title="Copy medical search hint"
                    type="button"
                    variant="outline"
                  >
                    {copied ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      <Clipboard className="h-4 w-4" />
                    )}
                    {copied ? "Copied" : "Copy"}
                  </Button>
                  {hint.url ? (
                    <Button asChild size="sm" title="Open medical search hint" variant="outline">
                      <a href={hint.url} rel="noopener noreferrer" target="_blank">
                        <ExternalLink className="h-4 w-4" />
                        Open
                      </a>
                    </Button>
                  ) : null}
                </div>
              </div>
              <code className="block max-h-24 overflow-auto break-words rounded bg-muted px-2 py-1 font-mono text-xs">
                {hint.query}
              </code>
              <div className="break-words text-muted-foreground">{hint.rationale}</div>
              {hint.warnings.length ? (
                <TokenList items={hint.warnings} title="Hint warnings" tone="warning" />
              ) : null}
            </div>
          );
        })}
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
  isSearchPending,
  onApplySuggestion,
  suggestions,
}: {
  isSearchPending: boolean;
  onApplySuggestion: (suggestion: FilterSuggestionStack) => void;
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
        {suggestions.map((suggestion) => {
          const actionable =
            !suggestion.applied && isSupportedFilterField(suggestion.field);
          return (
            <span
              className={cn(
                "inline-flex max-w-full items-center gap-1.5 rounded-full px-2 py-1 text-xs font-bold",
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
              {actionable ? (
                <button
                  aria-label={`Apply ${humanize(suggestion.field)} ${humanize(suggestion.value)} filter`}
                  className="inline-flex h-6 shrink-0 items-center gap-1 rounded-full border border-border bg-muted px-2 text-[11px] font-black text-foreground hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isSearchPending}
                  onClick={() => onApplySuggestion(suggestion)}
                  title={`Apply ${humanize(suggestion.field)}=${humanize(suggestion.value)}`}
                  type="button"
                >
                  {isSearchPending ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <ListFilter className="h-3 w-3" />
                  )}
                  Apply
                </button>
              ) : null}
            </span>
          );
        })}
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
  const [sourceSearch, setSourceSearch] = React.useState("");
  const [sourceTypeFilter, setSourceTypeFilter] = React.useState<string | null>(null);
  const [sourceDomainFilter, setSourceDomainFilter] = React.useState<string | null>(null);
  const [sourceStandardFilter, setSourceStandardFilter] = React.useState<string | null>(null);
  const filteredSources = sources.filter((source) =>
    sourceMatchesInventoryFilters(source, {
      domain: sourceDomainFilter,
      search: sourceSearch,
      standard: sourceStandardFilter,
      type: sourceTypeFilter,
    }),
  );
  const sourceTypeOptions = uniqueValues(sources.map((source) => source.source_type));
  const sourceDomainOptions = uniqueValues(sources.map((source) => source.clinical_domain));
  const sourceStandardOptions = uniqueValues(sources.map((source) => source.standard_system));
  const hasSourceFilters = Boolean(
    sourceSearch.trim() ||
      sourceTypeFilter ||
      sourceDomainFilter ||
      sourceStandardFilter,
  );
  const clearSourceFilters = () => {
    setSourceSearch("");
    setSourceTypeFilter(null);
    setSourceDomainFilter(null);
    setSourceStandardFilter(null);
  };

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70">
        <div className="min-w-0">
          <CardTitle>Trusted sources</CardTitle>
          <CardDescription>
            {isLoading
              ? "Loading inventory"
              : `${formatCount(filteredSources.length, "source")} shown from ${sources.length}`}
          </CardDescription>
        </div>
        {hasSourceFilters ? (
          <Button onClick={clearSourceFilters} size="sm" type="button" variant="outline">
            <X className="h-4 w-4" />
            Clear filters
          </Button>
        ) : null}
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div className="text-xs font-bold uppercase text-muted-foreground">
              Source inventory filters
            </div>
            <Badge variant="muted">
              {filteredSources.length}/{sources.length}
            </Badge>
          </div>
          <Input
            aria-label="Filter trusted sources"
            onChange={(event) => setSourceSearch(event.target.value)}
            placeholder="Filter sources by title, ID, type, domain, or standard"
            value={sourceSearch}
          />
          <SourceFilterChips
            activeValue={sourceTypeFilter}
            formatter={humanize}
            label="Source type"
            onSelect={setSourceTypeFilter}
            values={sourceTypeOptions}
          />
          <SourceFilterChips
            activeValue={sourceDomainFilter}
            formatter={humanize}
            label="Domain"
            onSelect={setSourceDomainFilter}
            values={sourceDomainOptions}
          />
          <SourceFilterChips
            activeValue={sourceStandardFilter}
            formatter={(value) => value}
            label="Standard"
            onSelect={setSourceStandardFilter}
            values={sourceStandardOptions}
          />
        </div>
        <div className="grid gap-3 md:hidden">
          {filteredSources.map((source) => (
            <SourceCard key={source.source_id} source={source} />
          ))}
          {!filteredSources.length ? (
            <div className="rounded-md border border-border p-3 text-sm text-muted-foreground">
              {isLoading
                ? "Loading sources."
                : hasSourceFilters
                  ? "No sources match the current filters."
                  : "No retrieval sources indexed."}
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
            {filteredSources.map((source) => (
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
            {!filteredSources.length ? (
              <TR>
                <TD colSpan={5}>
                  {isLoading
                    ? "Loading sources."
                    : hasSourceFilters
                      ? "No sources match the current filters."
                      : "No retrieval sources indexed."}
                </TD>
              </TR>
            ) : null}
          </TBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function SourceFilterChips({
  activeValue,
  formatter,
  label,
  onSelect,
  values,
}: {
  activeValue: string | null;
  formatter: (value: string) => string;
  label: string;
  onSelect: (value: string | null) => void;
  values: string[];
}) {
  if (!values.length) return null;
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold text-muted-foreground">{label}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <button
          aria-pressed={!activeValue}
          className={sourceFilterChipClass(!activeValue)}
          onClick={() => onSelect(null)}
          type="button"
        >
          All
        </button>
        {values.map((value) => {
          const active = activeValue === value;
          return (
            <button
              aria-pressed={active}
              className={sourceFilterChipClass(active)}
              key={value}
              onClick={() => onSelect(value)}
              type="button"
            >
              {formatter(value)}
            </button>
          );
        })}
      </div>
    </div>
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
  framework: {
    bm25Enabled: boolean | null;
    bm25Weight: number | null;
    candidateTopK: number | null;
    filteredNodeCount: number | null;
    metadataFilterCount: number | null;
    name: string;
    nodeCount: number | null;
    vectorWeight: number | null;
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
  selectedHits: DiversitySelectionStack[];
  selectedSourceCount: number;
  selectionMode: string;
};

type DiversitySelectionStack = {
  evidenceId: string;
  originalRank: number;
  reason: string;
  redundancyScore: number;
  relevanceScore: number;
  selectedRank: number;
  selectionScore: number;
  sourceId: string;
};

type QualityPolicyStack = {
  blockingSeverities: string[];
  reviewScoreBelow: number | null;
  reviewSeverities: string[];
  severityPenalties: Record<string, number>;
  version: string;
};

type QueryAnalysisStack = {
  conceptCandidates: ConceptCandidateStack[];
  detectedConcepts: string[];
  diagnostics: QueryDiagnosticStack[];
  expandedTerms: string[];
  filterSuggestions: FilterSuggestionStack[];
  queryAspects: QueryAspectStack[];
  queryProfile: QueryProfileStack | null;
  ruleIds: string[];
  searchHints: SearchHintStack[];
  standards: string[];
  strategy: string;
  variantCount: number;
};

type QueryAspectStack = {
  aspectId: string;
  label: string;
  priority: number;
  question: string;
  rationale: string;
  ruleId: string;
  suggestedFilters: Record<string, string>;
  suggestedTerms: string[];
};

type QueryProfileStack = {
  complexity: string;
  description: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
  ruleIds: string[];
  suggestedFilters: Record<string, string>;
};

type QueryProfileFilterEntry = {
  applied: boolean;
  displayValue: string;
  field: string;
  label: string;
  supported: boolean;
  value: string;
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
  url: string | null;
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

type RankingBoostSignal = {
  label: string;
  reason: string;
  ruleId: string;
  weight: number | null;
};

type QueryAspectMatchSignal = {
  aspectId: string;
  label: string;
  matchedFilters: Record<string, string>;
  matchedTerms: string[];
  priority: number;
  reason: string;
  ruleId: string;
};

function rankingStackFromPackage(packageData: RetrievalPackage): RankingStack {
  const embedding = recordValue(packageData.handoff_context.embedding);
  const frameworkComponents = recordValue(packageData.handoff_context.framework_components);
  const reranker = recordValue(packageData.handoff_context.reranker);
  const rerankerProvider = stringValue(reranker.provider, "none");
  return {
    embedding: {
      dimensions: numberValue(embedding.dimensions),
      model: stringValue(embedding.model, "unknown"),
      provider: stringValue(embedding.provider, "unknown"),
    },
    framework: {
      bm25Enabled: optionalBooleanValue(frameworkComponents.bm25_enabled),
      bm25Weight: numberValue(frameworkComponents.bm25_weight),
      candidateTopK: numberValue(frameworkComponents.candidate_top_k),
      filteredNodeCount: numberValue(frameworkComponents.filtered_node_count),
      metadataFilterCount: numberValue(frameworkComponents.metadata_filter_count),
      name: stringValue(packageData.handoff_context.framework, "custom"),
      nodeCount: numberValue(frameworkComponents.node_count),
      vectorWeight: numberValue(frameworkComponents.vector_weight),
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
    queryAspects: queryAspectsValue(queryAnalysis.query_aspects),
    queryProfile: queryProfileValue(queryAnalysis.query_profile),
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
    selectedHits: diversitySelectionDetailsValue(diversity.selected_hits),
    selectedSourceCount: numberValue(diversity.selected_source_count) ?? 0,
    selectionMode: stringValue(diversity.selection_mode, "unknown"),
  };
}

function qualityPolicyFromPackage(packageData: RetrievalPackage): QualityPolicyStack {
  const policy = recordValue(packageData.handoff_context.quality_policy);
  return {
    blockingSeverities: stringArrayValue(policy.blocking_severities),
    reviewScoreBelow: numberValue(policy.review_score_below),
    reviewSeverities: stringArrayValue(policy.review_severities),
    severityPenalties: numericRecordValue(policy.severity_penalties),
    version: stringValue(policy.version, "unknown"),
  };
}

function formatEmbeddingStack(stack: RankingStack): string {
  const dimensions = stack.embedding.dimensions ? ` / ${stack.embedding.dimensions}d` : "";
  return `${stack.embedding.provider} / ${stack.embedding.model}${dimensions}`;
}

function formatFrameworkStack(stack: RankingStack): string {
  if (stack.framework.name !== "llamaindex") {
    return stack.framework.name;
  }
  const nodeText = stack.framework.nodeCount === null ? "unknown nodes" : `${stack.framework.nodeCount} nodes`;
  const filterText =
    stack.framework.filteredNodeCount === null
      ? "filtered scope unknown"
      : `${stack.framework.filteredNodeCount} filtered`;
  const metadataFilterText =
    stack.framework.metadataFilterCount === null
      ? "filters unknown"
      : `${stack.framework.metadataFilterCount} metadata filters`;
  const candidateText =
    stack.framework.candidateTopK === null ? "candidate pool unknown" : `top ${stack.framework.candidateTopK}`;
  const bm25Text =
    stack.framework.bm25Enabled === null
      ? "BM25 unknown"
      : stack.framework.bm25Enabled
        ? "BM25 on"
        : "BM25 off";
  const weights =
    stack.framework.vectorWeight === null || stack.framework.bm25Weight === null
      ? "weights unknown"
      : `weights ${stack.framework.vectorWeight.toFixed(2)}:${stack.framework.bm25Weight.toFixed(2)}`;
  return `${stack.framework.name} / ${nodeText} / ${filterText} / ${metadataFilterText} / ${candidateText} / ${bm25Text} / ${weights}`;
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

function formatQualityPolicyTrace(policy: QualityPolicyStack): string {
  const warningPenalty = policy.severityPenalties.warning;
  const destructivePenalty = policy.severityPenalties.destructive;
  const thresholdText =
    policy.reviewScoreBelow === null ? "review threshold unknown" : `review < ${policy.reviewScoreBelow}`;
  const penaltyText = [
    warningPenalty === undefined ? null : `warning -${warningPenalty}`,
    destructivePenalty === undefined ? null : `blocker -${destructivePenalty}`,
  ].filter(Boolean);
  return [policy.version, thresholdText, ...penaltyText].join(" / ");
}

function diversitySelectionByEvidenceId(
  packageData: RetrievalPackage,
): Map<string, DiversitySelectionStack> {
  return new Map(
    diversityFromPackage(packageData).selectedHits.map((selection) => [
      selection.evidenceId,
      selection,
    ]),
  );
}

function diversitySelectionDetailsValue(value: unknown): DiversitySelectionStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      evidenceId: stringValue(item.evidence_id, ""),
      originalRank: numberValue(item.original_rank) ?? 0,
      reason: stringValue(item.reason, "Selected retrieval evidence."),
      redundancyScore: numberValue(item.redundancy_score) ?? 0,
      relevanceScore: numberValue(item.relevance_score) ?? 0,
      selectedRank: numberValue(item.selected_rank) ?? 0,
      selectionScore: numberValue(item.selection_score) ?? 0,
      sourceId: stringValue(item.source_id, ""),
    }))
    .filter((item) => item.evidenceId && item.selectedRank > 0);
}

function queryVariantsFromTrace(trace: RetrievalPackage["trace"]): RetrievalQueryVariant[] {
  const detailedVariants = queryVariantDetailsValue(trace.query_variant_details);
  if (detailedVariants.length) return detailedVariants;
  return trace.query_variants.map((variant) => ({
    metadata: {},
    reason: "Legacy query variant from retrieval trace.",
    source: "legacy_trace",
    variant,
  }));
}

function queryVariantDetailsValue(value: unknown): RetrievalQueryVariant[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      metadata: recordValue(item.metadata),
      reason: stringValue(item.reason, "Query variant used for retrieval."),
      source: stringValue(item.source, "unknown"),
      variant: stringValue(item.variant, ""),
    }))
    .filter((item) => item.variant);
}

function queryProfileValue(value: unknown): QueryProfileStack | null {
  const profile = recordValue(value);
  const profileId = stringValue(profile.profile_id, "");
  if (!profileId) return null;
  return {
    complexity: stringValue(profile.complexity, "unknown"),
    description: stringValue(profile.description, "No query profile description provided."),
    label: stringValue(profile.label, humanize(profileId)),
    profileId,
    retrievalMode: stringValue(profile.retrieval_mode, "unknown"),
    route: stringValue(profile.route, "retrieval"),
    ruleIds: stringArrayValue(profile.rule_ids),
    suggestedFilters: stringRecordValue(profile.suggested_filters),
  };
}

function queryAspectsValue(value: unknown): QueryAspectStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      aspectId: stringValue(item.aspect_id, ""),
      label: stringValue(item.label, "Search aspect"),
      priority: numberValue(item.priority) ?? 100,
      question: stringValue(item.question, "Review this search aspect."),
      rationale: stringValue(item.rationale, "Aspect generated from query analysis."),
      ruleId: stringValue(item.rule_id, ""),
      suggestedFilters: stringRecordValue(item.suggested_filters),
      suggestedTerms: stringArrayValue(item.suggested_terms),
    }))
    .filter((item) => item.aspectId)
    .sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
}

function queryProfileFilterEntries(
  profile: QueryProfileStack,
  appliedFilters: Record<string, unknown>,
): QueryProfileFilterEntry[] {
  return suggestedFilterEntries(profile.suggestedFilters, appliedFilters);
}

function queryAspectFilterEntries(
  aspect: QueryAspectStack,
  appliedFilters: Record<string, unknown>,
): QueryProfileFilterEntry[] {
  return suggestedFilterEntries(aspect.suggestedFilters, appliedFilters);
}

function suggestedFilterEntries(
  suggestedFilters: Record<string, string>,
  appliedFilters: Record<string, unknown>,
): QueryProfileFilterEntry[] {
  return Object.entries(suggestedFilters).map(([field, value]) => {
    const supported = isSupportedFilterField(field);
    return {
      applied: supported && appliedFilterMatches(appliedFilters, field, value),
      displayValue: supported ? formatFilterValue(field, value) : value,
      field,
      label: supported ? filterFieldLabel(field) : humanize(field),
      supported,
      value,
    };
  });
}

function appliedFilterMatches(
  appliedFilters: Record<string, unknown>,
  field: SupportedFilterField,
  value: string,
): boolean {
  const appliedValue = appliedFilters[field];
  if (typeof appliedValue !== "string") return false;
  return appliedValue.toLowerCase() === value.toLowerCase();
}

function scoreComponentsFromHit(hit: RetrievalHit): RetrievalScoreComponent[] {
  return (hit.score_components ?? [])
    .map((component) => ({
      component: stringValue(component.component, ""),
      description: stringValue(component.description, "Score component contribution."),
      label: stringValue(component.label, humanize(component.component)),
      metadata: recordValue(component.metadata),
      rank: typeof component.rank === "number" ? component.rank : null,
      value: numberValue(component.value) ?? 0,
    }))
    .filter((component) => component.component);
}

function rankingBoostSignalsFromHit(hit: RetrievalHit): RankingBoostSignal[] {
  const detailedSignals = rankingBoostDetailsValue(hit.source_locator.ranking_boosts);
  if (detailedSignals.length) return detailedSignals;
  return stringArrayValue(hit.source_locator.ranking_boost_rules).map((ruleId) => ({
    label: formatRankingSignal(ruleId),
    reason: "Ranking boost rule applied.",
    ruleId,
    weight: null,
  }));
}

function queryAspectMatchesFromHit(hit: RetrievalHit): QueryAspectMatchSignal[] {
  const matches = hit.source_locator.query_aspect_matches;
  if (!Array.isArray(matches)) return [];
  return matches
    .map((item) => recordValue(item))
    .map((item) => ({
      aspectId: stringValue(item.aspect_id, ""),
      label: stringValue(item.label, "Search aspect"),
      matchedFilters: stringRecordValue(item.matched_filters),
      matchedTerms: stringArrayValue(item.matched_terms),
      priority: numberValue(item.priority) ?? 100,
      reason: stringValue(item.reason, "Evidence matched this search aspect."),
      ruleId: stringValue(item.rule_id, ""),
    }))
    .filter((item) => item.aspectId && item.ruleId);
}

function rankingBoostDetailsValue(value: unknown): RankingBoostSignal[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => {
      const ruleId = stringValue(item.rule_id, "");
      return {
        label: formatRankingSignal(ruleId),
        reason: stringValue(item.reason, "Ranking boost rule applied."),
        ruleId,
        weight: numberValue(item.weight),
      };
    })
    .filter((item) => item.ruleId);
}

function formatRankingSignal(ruleId: string): string {
  return humanize(ruleId.replace(/^boost_/, ""));
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

function optionalBooleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function stringRecordValue(value: unknown): Record<string, string> {
  const record = recordValue(value);
  return Object.fromEntries(
    Object.entries(record)
      .map(([key, item]) => [key.trim(), typeof item === "string" ? item.trim() : ""])
      .filter(([key, item]) => key && item),
  );
}

function numericRecordValue(value: unknown): Record<string, number> {
  const record = recordValue(value);
  return Object.fromEntries(
    Object.entries(record)
      .map(([key, item]) => [key, numberValue(item)] as const)
      .filter((entry): entry is readonly [string, number] => entry[1] !== null),
  );
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
      url: optionalStringValue(item.url),
      warnings: stringArrayValue(item.warnings),
    }))
    .filter((item) => item.query.length > 0 && item.target !== "medical_search");
}

async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

function diagnosticBadgeVariant(
  severity: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (severity === "warning") return "warning";
  if (severity === "error") return "destructive";
  if (severity === "info") return "muted";
  return "default";
}

function qualitySignalBadgeVariant(
  severity: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (severity === "success") return "success";
  if (severity === "warning") return "warning";
  if (severity === "destructive" || severity === "error") return "destructive";
  if (severity === "info") return "muted";
  return "default";
}

function qualitySignalSummaryVariant(
  signals: RetrievalQualitySignal[],
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (
    signals.some(
      (signal) => signal.severity === "destructive" || signal.severity === "error",
    )
  ) {
    return "destructive";
  }
  if (signals.some((signal) => signal.severity === "warning")) return "warning";
  if (signals.some((signal) => signal.severity === "success")) return "success";
  return "muted";
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

function retrievalPayloadFromForm(
  form: RetrievalFormState,
  overrides: Partial<RetrievalSearchPayload> = {},
): RetrievalSearchPayload {
  return {
    query: form.query.trim(),
    top_k: form.topK,
    schema_id: form.schemaId || null,
    fields: parseFields(form.fields),
    detected_format: form.detectedFormat || null,
    resource_type: form.resourceType || null,
    clinical_domain: form.clinicalDomain || null,
    standard_system: form.standardSystem || null,
    trust_level: form.trustLevel || null,
    source_type: form.sourceType || null,
    filters: {},
    ...overrides,
  };
}

function retrievalSearchSignature(payload: RetrievalSearchPayload): string {
  return JSON.stringify({
    query: payload.query,
    top_k: payload.top_k,
    schema_id: payload.schema_id ?? null,
    fields: payload.fields,
    detected_format: payload.detected_format ?? null,
    resource_type: payload.resource_type ?? null,
    clinical_domain: payload.clinical_domain ?? null,
    standard_system: payload.standard_system ?? null,
    trust_level: payload.trust_level ?? null,
    source_type: payload.source_type ?? null,
    filters: payload.filters ?? {},
  });
}

function createSearchRun(
  payload: RetrievalSearchPayload,
  packageData: RetrievalPackage,
  signature: string,
): RetrievalSearchRun {
  return {
    packageData,
    payload,
    runId: crypto.randomUUID(),
    signature,
    submittedAt: new Date().toISOString(),
    summary: retrievalRunSummary(packageData),
  };
}

function comparisonRunForActive(
  runs: RetrievalSearchRun[],
  activeRunId: string,
  baselineRunId: string | null,
): RetrievalSearchRun | null {
  const activeIndex = runs.findIndex((run) => run.runId === activeRunId);
  if (activeIndex < 0) return null;
  const explicitBaseline = baselineRunId
    ? runs.find((run) => run.runId === baselineRunId && run.runId !== activeRunId)
    : null;
  if (explicitBaseline) return explicitBaseline;
  return (
    runs.slice(activeIndex + 1).find((run) => run.runId !== activeRunId) ??
    runs.find((run) => run.runId !== activeRunId) ??
    null
  );
}

function compareSearchRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalRunComparison {
  const activeEvidenceIds = evidenceIdsFromRun(activeRun);
  const baselineEvidenceIds = evidenceIdsFromRun(baselineRun);
  const activeEvidenceIdSet = new Set(activeEvidenceIds);
  const baselineEvidenceIdSet = new Set(baselineEvidenceIds);
  const addedEvidenceIds = activeEvidenceIds.filter(
    (evidenceId) => !baselineEvidenceIdSet.has(evidenceId),
  );
  const removedEvidenceIds = baselineEvidenceIds.filter(
    (evidenceId) => !activeEvidenceIdSet.has(evidenceId),
  );
  const retainedEvidenceIds = activeEvidenceIds.filter((evidenceId) =>
    baselineEvidenceIdSet.has(evidenceId),
  );
  const rankChanges = rankChangesBetweenRuns(activeRun, baselineRun);
  const rulePackChanges = rulePackChangesBetweenRuns(activeRun, baselineRun);
  const queryProfileChanged = queryProfilesChanged(
    activeRun.summary.queryProfile,
    baselineRun.summary.queryProfile,
  );
  const coverageComparison = coverageComparisonBetweenRuns(activeRun, baselineRun);
  const facetComparisons = facetComparisonsBetweenRuns(activeRun, baselineRun);
  const qualitySignalComparison = qualitySignalComparisonBetweenRuns(
    activeRun,
    baselineRun,
  );
  const queryAspectComparison = queryAspectComparisonBetweenRuns(activeRun, baselineRun);
  const rulePackChanged = rulePackChanges.some((change) => change.status !== "stable");
  const topSourceChanged = activeRun.summary.topSourceId !== baselineRun.summary.topSourceId;

  const comparison: Omit<RetrievalRunComparison, "diagnosis"> = {
    addedEvidenceIds,
    activePayload: activeRun.payload,
    activeQuery: activeRun.payload.query,
    activeRunId: activeRun.runId,
    activeSubmittedAt: activeRun.submittedAt,
    activeSummary: activeRun.summary,
    baselinePayload: baselineRun.payload,
    baselineQuery: baselineRun.payload.query,
    baselineRunId: baselineRun.runId,
    baselineSubmittedAt: baselineRun.submittedAt,
    baselineSummary: baselineRun.summary,
    candidateDelta:
      activeRun.summary.candidateCount - baselineRun.summary.candidateCount,
    coverageComparison,
    facetComparisons,
    hitDelta: activeRun.summary.hitCount - baselineRun.summary.hitCount,
    metrics: comparisonMetrics({
      addedCount: addedEvidenceIds.length,
      baselineCount: baselineEvidenceIds.length,
      rankChanges,
      retainedCount: retainedEvidenceIds.length,
      removedCount: removedEvidenceIds.length,
      activeCount: activeEvidenceIds.length,
    }),
    queryAspectComparison,
    qualityWarningDelta:
      activeRun.summary.qualityWarningCount - baselineRun.summary.qualityWarningCount,
    qualitySignalComparison,
    queryProfileChanged,
    rankChanges,
    removedEvidenceIds,
    retainedEvidenceIds,
    rulePackChanges,
    rulePackChanged,
    topSourceAfter: activeRun.summary.topSourceId,
    topSourceBefore: baselineRun.summary.topSourceId,
    topSourceChanged,
    warningDelta: activeRun.summary.warningCount - baselineRun.summary.warningCount,
  };
  return {
    ...comparison,
    diagnosis: comparisonDiagnosisFromComparison(comparison),
  };
}

function comparisonDiagnosisFromComparison(
  comparison: Omit<RetrievalRunComparison, "diagnosis">,
): RetrievalComparisonDiagnosis[] {
  const diagnosis: RetrievalComparisonDiagnosis[] = [];
  if (comparison.queryProfileChanged) {
    diagnosis.push({
      code: "query_profile_changed",
      message:
        "Query profile, route, retrieval mode, or complexity changed between runs.",
      severity: "warning",
    });
  }
  if (comparison.rulePackChanged) {
    diagnosis.push({
      code: "rule_pack_changed",
      message: "Retrieval rule-pack fingerprints changed between runs.",
      severity: "warning",
    });
  }
  if (
    comparison.queryAspectComparison.added.length ||
    comparison.queryAspectComparison.removed.length
  ) {
    diagnosis.push({
      code: "query_aspect_plan_changed",
      message: "Search aspect coverage plan changed between runs.",
      severity: "warning",
    });
  }
  if (comparison.coverageComparison.regressed.length || comparison.coverageComparison.added.length) {
    diagnosis.push({
      code: "coverage_diagnostics_changed",
      message: "Coverage diagnostics changed between runs.",
      severity: "warning",
    });
  } else if (comparison.coverageComparison.improved.length) {
    diagnosis.push({
      code: "coverage_improved",
      message: "Coverage diagnostics improved between runs.",
      severity: "success",
    });
  }
  if (
    comparison.qualitySignalComparison.added.length ||
    comparison.qualitySignalComparison.removed.length
  ) {
    diagnosis.push({
      code: "quality_signal_changed",
      message: "Package-level quality signals were added or removed.",
      severity: "warning",
    });
  }
  if (
    comparison.facetComparisons.some(
      (facet) => facet.addedValues.length || facet.removedValues.length,
    )
  ) {
    diagnosis.push({
      code: "facet_coverage_changed",
      message:
        "Selected-hit source type, clinical domain, standard, or trust coverage changed.",
      severity: "warning",
    });
  }
  if (comparison.topSourceChanged) {
    diagnosis.push({
      code: "top_source_changed",
      message: "The highest-ranked source changed between runs.",
      severity: "warning",
    });
  }
  if (comparison.rankChanges.length) {
    diagnosis.push({
      code: "rank_movement",
      message: "Retained evidence moved position in the ranked result set.",
      severity: "warning",
    });
  }
  if (comparison.addedEvidenceIds.length || comparison.removedEvidenceIds.length) {
    diagnosis.push({
      code: "evidence_set_changed",
      message: "The retrieved evidence set added or removed source chunks.",
      severity: "warning",
    });
  }
  if (!diagnosis.length) {
    diagnosis.push({
      code: "comparison_stable",
      message:
        "Comparison is stable across query profile, search aspects, rules, quality, facets, evidence, and ranks.",
      severity: "success",
    });
  }
  return diagnosis;
}

function comparisonReportFromComparison(
  comparison: RetrievalRunComparison,
  judgments: RelevanceJudgment[],
) {
  return {
    report_type: "retrieval_run_comparison",
    version: 1,
    generated_at: new Date().toISOString(),
    active: {
      query: comparison.activeQuery,
      submitted_at: comparison.activeSubmittedAt,
      payload: comparison.activePayload,
      summary: comparison.activeSummary,
    },
    baseline: {
      query: comparison.baselineQuery,
      submitted_at: comparison.baselineSubmittedAt,
      payload: comparison.baselinePayload,
      summary: comparison.baselineSummary,
    },
    deltas: {
      candidates: comparison.candidateDelta,
      hits: comparison.hitDelta,
      quality_warnings: comparison.qualityWarningDelta,
      warnings: comparison.warningDelta,
    },
    diagnosis: comparison.diagnosis,
    metrics: comparison.metrics,
    coverage: {
      added: comparison.coverageComparison.added,
      improved: comparison.coverageComparison.improved,
      regressed: comparison.coverageComparison.regressed,
      removed: comparison.coverageComparison.removed,
      retained: comparison.coverageComparison.retained,
    },
    query_aspects: {
      added: comparison.queryAspectComparison.added,
      removed: comparison.queryAspectComparison.removed,
      retained: comparison.queryAspectComparison.retained,
    },
    quality_signals: {
      added: comparison.qualitySignalComparison.added,
      removed: comparison.qualitySignalComparison.removed,
      retained: comparison.qualitySignalComparison.retained,
    },
    facets: comparison.facetComparisons.map((facet) => ({
      field: facet.field,
      label: facet.label,
      active_count: facet.activeCount,
      baseline_count: facet.baselineCount,
      added_values: facet.addedValues,
      removed_values: facet.removedValues,
      retained_values: facet.retainedValues,
    })),
    judgments: judgments.map((judgment) => ({
      doc_id: judgment.evidenceId,
      evidence_id: judgment.evidenceId,
      judged_at: judgment.judgedAt,
      query: judgment.query,
      rating: judgment.rating,
      run_id: judgment.runId,
      value: judgment.value,
    })),
    evidence: {
      added_ids: comparison.addedEvidenceIds,
      removed_ids: comparison.removedEvidenceIds,
      retained_ids: comparison.retainedEvidenceIds,
      rank_changes: comparison.rankChanges,
    },
    top_source: {
      before: comparison.topSourceBefore,
      after: comparison.topSourceAfter,
      changed: comparison.topSourceChanged,
    },
    query_profiles: {
      before: comparison.baselineSummary.queryProfile,
      after: comparison.activeSummary.queryProfile,
      changed: comparison.queryProfileChanged,
    },
    rule_packs: {
      changed: comparison.rulePackChanged,
      changes: comparison.rulePackChanges.map((change) => ({
        name: change.name,
        status: change.status,
        before: change.baseline ?? null,
        after: change.active ?? null,
      })),
    },
  };
}

function evaluationReportFromJudgmentSummary(
  evaluation: RetrievalJudgmentEvaluationResult,
  metrics: RelevanceJudgmentMetrics,
  summary: RetrievalRelevanceJudgmentSummary | null,
  packageData: RetrievalPackage,
) {
  return {
    report_type: "retrieval_judgment_evaluation",
    version: 1,
    generated_at: new Date().toISOString(),
    query: evaluation.query,
    cutoff: evaluation.cutoff,
    ranked_evidence_ids: evaluation.ranked_evidence_ids,
    server_metrics: {
      coverage_at_k: evaluation.coverage_at_k,
      hit_rate_at_k: evaluation.hit_rate_at_k,
      precision_at_k: evaluation.precision_at_k,
      judged_precision: evaluation.judged_precision ?? null,
      average_precision_at_k: evaluation.average_precision_at_k,
      mrr_at_k: evaluation.mrr_at_k,
      ndcg_at_k: evaluation.ndcg_at_k ?? null,
      average_rating: evaluation.average_rating ?? null,
      judged_count: evaluation.judged_count,
      unjudged_count: evaluation.unjudged_count,
      relevant_count: evaluation.relevant_count,
      partial_count: evaluation.partial_count,
      not_relevant_count: evaluation.not_relevant_count,
    },
    local_metrics: {
      average_rating: metrics.averageRating,
      coverage_at_k: metrics.judgmentCoverage,
      precision_at_k: metrics.precisionAtK,
      judged_precision: metrics.judgedPrecision,
      ndcg_at_k: metrics.ndcgAtK,
      judged_count: metrics.judgedCount,
      relevant_count: metrics.relevantCount,
      partial_count: metrics.partialCount,
      not_relevant_count: metrics.notRelevantCount,
      total_hits: metrics.totalHits,
    },
    recommendations: evaluation.recommendations,
    query_profile: queryProfileSummaryFromPackage(packageData),
    retrieval_rule_packs: retrievalRulePacksFromPackage(packageData),
    stored_label_summary: summary,
    unjudged_evidence_ids: evaluation.unjudged_evidence_ids,
    judgment_ids: evaluation.judgment_ids,
  };
}

function retrievalRulePacksFromPackage(packageData: RetrievalPackage): RuntimeRetrievalRulePack[] {
  const rawPacks = packageData.handoff_context.retrieval_rule_packs;
  if (!Array.isArray(rawPacks)) return [];
  return rawPacks
    .map((rawPack) => recordValue(rawPack))
    .map((pack) => ({
      name: stringValue(pack.name, ""),
      status: rulePackStatusValue(pack.status),
      source: stringValue(pack.source, "unknown"),
      env_var: stringValue(pack.env_var, ""),
      configured: booleanValue(pack.configured),
      rule_count: numberValue(pack.rule_count) ?? 0,
      version: optionalStringValue(pack.version),
      content_hash: optionalStringValue(pack.content_hash),
      error: optionalStringValue(pack.error) ?? undefined,
    }))
    .filter((pack) => pack.name && pack.env_var);
}

function queryProfileSummaryFromPackage(packageData: RetrievalPackage): QueryProfileSummary | null {
  const queryProfile = queryAnalysisFromPackage(packageData).queryProfile;
  if (!queryProfile) return null;
  return {
    complexity: queryProfile.complexity,
    label: queryProfile.label,
    profileId: queryProfile.profileId,
    retrievalMode: queryProfile.retrievalMode,
    route: queryProfile.route,
  };
}

function coverageSummariesFromPackage(packageData: RetrievalPackage): RetrievalCoverageSummary[] {
  const coverage = packageData.coverage;
  const standardItems = coverage?.standard_system ?? [];
  const aspectItems = coverage?.query_aspects ?? [];
  return [
    ...standardItems.map((item) => coverageSummaryFromItem(item, "standard")),
    ...aspectItems.map((item) => coverageSummaryFromItem(item, "aspect")),
  ].sort((left, right) => coverageComparisonKey(left).localeCompare(coverageComparisonKey(right)));
}

function coverageSummaryFromItem(
  item: RetrievalCoverage["standard_system"][number],
  group: "aspect" | "standard",
): RetrievalCoverageSummary {
  return {
    field: item.field,
    label: group === "standard" ? item.value : humanize(item.value),
    selectedCount: item.selected_count,
    status: item.status,
    suggestedFilter: stringRecordValue(item.suggested_filter),
    value: item.value,
  };
}

function queryAspectSummariesFromPackage(packageData: RetrievalPackage): QueryAspectSummary[] {
  return queryAnalysisFromPackage(packageData)
    .queryAspects.map((aspect) => ({
      aspectId: aspect.aspectId,
      label: aspect.label,
      priority: aspect.priority,
      question: aspect.question,
      ruleId: aspect.ruleId,
    }))
    .sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
}

function rulePackStatusValue(value: unknown): RuntimeRetrievalRulePack["status"] {
  if (value === "ok" || value === "missing" || value === "error") return value;
  return "error";
}

function judgmentsForComparison(
  comparison: RetrievalRunComparison,
  judgments: RelevanceJudgmentIndex,
): RelevanceJudgment[] {
  const evidenceIds = new Set([
    ...comparison.addedEvidenceIds,
    ...comparison.removedEvidenceIds,
    ...comparison.retainedEvidenceIds,
  ]);
  return Object.values(judgments)
    .filter(
      (judgment) =>
        evidenceIds.has(judgment.evidenceId) &&
        (judgment.runId === comparison.activeRunId ||
          judgment.runId === comparison.baselineRunId),
    )
    .sort((left, right) => left.evidenceId.localeCompare(right.evidenceId));
}

function relevanceJudgmentFromPersisted(
  judgment: RetrievalRelevanceJudgment,
  run: { query: string; runId: string; signature: string },
): RelevanceJudgment {
  return {
    evidenceId: judgment.evidence_id,
    judgedAt: judgment.updated_at,
    judgmentId: judgment.judgment_id,
    query: run.query,
    rating: judgment.rating,
    runId: run.runId,
    searchSignature: run.signature,
    sourceId: judgment.source_id ?? null,
    value: judgment.value,
  };
}

function judgmentsForRunHits(
  runId: string,
  hits: RetrievalHit[],
  judgments: RelevanceJudgmentIndex,
): RelevanceJudgment[] {
  return hits
    .map((hit) => judgments[relevanceJudgmentKey(runId, hit.evidence.evidence_id)] ?? null)
    .filter((judgment): judgment is RelevanceJudgment => judgment !== null);
}

function qualitySummaryTone(
  summary: RetrievalQualitySummary | null,
): "default" | "success" | "warning" | "info" | "neutral" {
  if (!summary) return "neutral";
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked" || summary.status === "review") return "warning";
  return "info";
}

function relevanceJudgmentKey(runId: string, evidenceId: string): string {
  return `${runId}:${evidenceId}`;
}

function relevanceJudgmentMetrics(
  hits: RetrievalHit[],
  judgments: RelevanceJudgment[],
): RelevanceJudgmentMetrics {
  const totalHits = hits.length;
  const ratingsByEvidenceId = new Map(
    judgments.map((judgment) => [
      judgment.evidenceId,
      judgment.rating,
    ]),
  );
  const rankedRatings = hits.map(
    (hit) => ratingsByEvidenceId.get(hit.evidence.evidence_id) ?? 0,
  );
  const judgedRatings = judgments.map((judgment) => judgment.rating);
  const relevantCount = judgments.filter(
    (judgment) => judgment.value === "relevant",
  ).length;
  const partialCount = judgments.filter(
    (judgment) => judgment.value === "partial",
  ).length;
  const notRelevantCount = judgments.filter(
    (judgment) => judgment.value === "not_relevant",
  ).length;
  const positiveJudgments = relevantCount + partialCount;
  const dcg = discountedCumulativeGain(rankedRatings);
  const idealDcg = discountedCumulativeGain(
    [...rankedRatings].sort((left, right) => right - left),
  );

  return {
    averageRating: judgedRatings.length
      ? judgedRatings.reduce((total, rating) => total + rating, 0) / judgedRatings.length
      : null,
    judgedCount: judgments.length,
    judgedPrecision: judgments.length ? positiveJudgments / judgments.length : null,
    judgmentCoverage: totalHits ? judgments.length / totalHits : 0,
    ndcgAtK: idealDcg ? dcg / idealDcg : null,
    notRelevantCount,
    partialCount,
    precisionAtK: totalHits ? positiveJudgments / totalHits : 0,
    relevantCount,
    totalHits,
  };
}

function discountedCumulativeGain(ratings: number[]): number {
  return ratings.reduce((total, rating, index) => {
    if (rating <= 0) return total;
    return total + (2 ** rating - 1) / Math.log2(index + 2);
  }, 0);
}

function relevanceJudgmentRating(value: RelevanceJudgmentValue): number {
  if (value === "relevant") return 3;
  if (value === "partial") return 1;
  return 0;
}

function judgmentLabel(value: RelevanceJudgmentValue): string {
  if (value === "relevant") return "Relevant";
  if (value === "partial") return "Partial";
  return "Not relevant";
}

function judgmentBadgeVariant(
  value: RelevanceJudgmentValue,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (value === "relevant") return "success";
  if (value === "partial") return "warning";
  return "destructive";
}

function comparisonMetrics({
  activeCount,
  addedCount,
  baselineCount,
  rankChanges,
  retainedCount,
  removedCount,
}: {
  activeCount: number;
  addedCount: number;
  baselineCount: number;
  rankChanges: RetrievalRankChange[];
  retainedCount: number;
  removedCount: number;
}): RetrievalRunComparisonMetrics {
  const unionCount = Math.max(0, activeCount + baselineCount - retainedCount);
  const totalRankDelta = rankChanges.reduce(
    (total, change) => total + Math.abs(change.rankDelta),
    0,
  );
  return {
    changedRankCount: rankChanges.length,
    churnRate: unionCount ? (addedCount + removedCount) / unionCount : 0,
    meanAbsoluteRankDelta: rankChanges.length
      ? totalRankDelta / rankChanges.length
      : 0,
    overlapRatio: unionCount ? retainedCount / unionCount : 1,
    sharedCount: retainedCount,
    unionCount,
  };
}

function rankChangesBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalRankChange[] {
  const baselineRanks = new Map(
    baselineRun.packageData.hits.map((hit, index) => [
      hit.evidence.evidence_id,
      index + 1,
    ]),
  );
  return activeRun.packageData.hits
    .map((hit, index) => {
      const evidenceId = hit.evidence.evidence_id;
      const fromRank = baselineRanks.get(evidenceId);
      const toRank = index + 1;
      if (!fromRank || fromRank === toRank) return null;
      return {
        evidenceId,
        fromRank,
        rankDelta: toRank - fromRank,
        toRank,
      };
    })
    .filter((change): change is RetrievalRankChange => Boolean(change))
    .sort((left, right) => Math.abs(right.rankDelta) - Math.abs(left.rankDelta));
}

function rulePackChangesBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalRulePackChange[] {
  const activePacks = retrievalRulePacksFromPackage(activeRun.packageData);
  const baselinePacks = retrievalRulePacksFromPackage(baselineRun.packageData);
  const activeByName = new Map(activePacks.map((pack) => [pack.name, pack]));
  const baselineByName = new Map(baselinePacks.map((pack) => [pack.name, pack]));
  const packNames = uniqueValues([...activeByName.keys(), ...baselineByName.keys()]);
  return packNames.map((name) => {
    const active = activeByName.get(name);
    const baseline = baselineByName.get(name);
    let status: RetrievalRulePackChange["status"] = "stable";
    if (active && !baseline) status = "added";
    else if (!active && baseline) status = "removed";
    else if (rulePackFingerprint(active) !== rulePackFingerprint(baseline)) {
      status = "changed";
    }
    return { active, baseline, name, status };
  });
}

function rulePackFingerprint(pack?: RuntimeRetrievalRulePack): string {
  if (!pack) return "missing";
  if (pack.content_hash) return pack.content_hash;
  if (pack.version) return pack.version;
  return `${pack.status}:${pack.rule_count}`;
}

function queryProfilesChanged(
  active: QueryProfileSummary | null,
  baseline: QueryProfileSummary | null,
): boolean {
  return (
    active?.profileId !== baseline?.profileId ||
    active?.retrievalMode !== baseline?.retrievalMode ||
    active?.route !== baseline?.route
  );
}

function coverageComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalCoverageComparison {
  const activeCoverage = activeRun.summary.coverage;
  const baselineCoverage = baselineRun.summary.coverage;
  const activeByKey = new Map(activeCoverage.map((item) => [coverageComparisonKey(item), item]));
  const baselineByKey = new Map(
    baselineCoverage.map((item) => [coverageComparisonKey(item), item]),
  );
  const retained: RetrievalCoverageSummary[] = [];
  const improved: RetrievalCoverageStatusChange[] = [];
  const regressed: RetrievalCoverageStatusChange[] = [];
  for (const item of activeCoverage) {
    const baseline = baselineByKey.get(coverageComparisonKey(item));
    if (!baseline) continue;
    const change = { active: item, baseline };
    const activeRank = coverageStatusRank(item);
    const baselineRank = coverageStatusRank(baseline);
    if (activeRank > baselineRank) improved.push(change);
    else if (activeRank < baselineRank) regressed.push(change);
    else retained.push(item);
  }
  return {
    added: activeCoverage.filter((item) => !baselineByKey.has(coverageComparisonKey(item))),
    improved,
    regressed,
    removed: baselineCoverage.filter((item) => !activeByKey.has(coverageComparisonKey(item))),
    retained,
  };
}

function coverageStatusRank(item: RetrievalCoverageSummary): number {
  if (item.status === "covered") return 2;
  if (item.status === "partial") return 1;
  return 0;
}

function coverageComparisonKey(item: RetrievalCoverageSummary): string {
  return `${item.field}:${item.value}`;
}

function facetComparisonsBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalFacetComparison[] {
  return Array.from(supportedSuggestionFilterFields).map((field) => {
    const activeValues = facetValuesFromRun(activeRun, field);
    const baselineValues = facetValuesFromRun(baselineRun, field);
    const activeSet = new Set(activeValues);
    const baselineSet = new Set(baselineValues);
    return {
      activeCount: activeValues.length,
      addedValues: activeValues.filter((value) => !baselineSet.has(value)),
      baselineCount: baselineValues.length,
      field,
      label: filterFieldLabel(field),
      removedValues: baselineValues.filter((value) => !activeSet.has(value)),
      retainedValues: activeValues.filter((value) => baselineSet.has(value)),
    };
  });
}

function facetValuesFromRun(
  run: RetrievalSearchRun,
  field: SupportedFilterField,
): string[] {
  const facets = run.packageData.facets;
  if (!facets) return [];
  return (facets[field] ?? [])
    .map((bucket) => bucket.value)
    .filter(Boolean)
    .sort((left, right) => left.localeCompare(right));
}

function qualitySignalComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalQualitySignalComparison {
  const activeSignals = qualitySignalSummariesFromRun(activeRun);
  const baselineSignals = qualitySignalSummariesFromRun(baselineRun);
  const activeByCode = new Map(activeSignals.map((signal) => [signal.code, signal]));
  const baselineByCode = new Map(baselineSignals.map((signal) => [signal.code, signal]));
  return {
    added: activeSignals.filter((signal) => !baselineByCode.has(signal.code)),
    removed: baselineSignals.filter((signal) => !activeByCode.has(signal.code)),
    retained: activeSignals.filter((signal) => baselineByCode.has(signal.code)),
  };
}

function queryAspectComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalQueryAspectComparison {
  const activeAspects = activeRun.summary.queryAspects;
  const baselineAspects = baselineRun.summary.queryAspects;
  const activeById = new Map(activeAspects.map((aspect) => [aspect.aspectId, aspect]));
  const baselineById = new Map(baselineAspects.map((aspect) => [aspect.aspectId, aspect]));
  return {
    added: activeAspects.filter((aspect) => !baselineById.has(aspect.aspectId)),
    removed: baselineAspects.filter((aspect) => !activeById.has(aspect.aspectId)),
    retained: activeAspects.filter((aspect) => baselineById.has(aspect.aspectId)),
  };
}

function qualitySignalSummariesFromRun(
  run: RetrievalSearchRun,
): RetrievalQualitySignalSummary[] {
  return (run.packageData.quality_signals ?? [])
    .map((signal) => ({
      code: signal.code,
      message: signal.message,
      severity: signal.severity,
      suggestedAction: signal.suggested_action,
    }))
    .filter((signal) => signal.code)
    .sort((left, right) => left.code.localeCompare(right.code));
}

function evidenceIdsFromRun(run: RetrievalSearchRun): string[] {
  return run.packageData.hits.map((hit) => hit.evidence.evidence_id);
}

function retrievalRunSummary(packageData: RetrievalPackage): RetrievalRunSummary {
  const rulePacks = retrievalRulePacksFromPackage(packageData);
  return {
    candidateCount: packageData.trace.candidates_seen,
    coverage: coverageSummariesFromPackage(packageData),
    hitCount: packageData.hits.length,
    qualityWarningCount: qualityWarningCount(packageData.quality_signals ?? []),
    queryAspects: queryAspectSummariesFromPackage(packageData),
    queryProfile: queryProfileSummaryFromPackage(packageData),
    rulePackCount: rulePacks.length,
    rulePackFingerprint: rulePacks
      .map((pack) => `${pack.name}:${rulePackFingerprint(pack)}`)
      .join("|"),
    topSourceId: packageData.hits[0]?.evidence.source_id ?? null,
    warningCount: packageData.trace.warnings.length,
  };
}

function qualityWarningCount(signals: RetrievalQualitySignal[]): number {
  return signals.filter((signal) =>
    ["destructive", "error", "warning"].includes(signal.severity),
  ).length;
}

function searchRunSummaryVariant(
  summary: RetrievalRunSummary,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (summary.qualityWarningCount > 0 || summary.warningCount > 0) return "warning";
  if (summary.hitCount > 0) return "success";
  return "destructive";
}

function deltaBadgeVariant(
  delta: number,
  positiveIsGood: boolean,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (delta === 0) return "muted";
  const good = positiveIsGood ? delta > 0 : delta < 0;
  return good ? "success" : "warning";
}

function formatSignedDelta(delta: number): string {
  return delta > 0 ? `+${delta}` : String(delta);
}

function formatPercent(value: number): string {
  if (!Number.isFinite(value)) return "n/a";
  return `${Math.round(value * 100)}%`;
}

function formatDecimal(value: number): string {
  if (!Number.isFinite(value)) return "n/a";
  return value.toFixed(1);
}

function formatNullablePercent(value: number | null): string {
  return value === null ? "n/a" : formatPercent(value);
}

function formatNullableDecimal(value: number | null): string {
  return value === null ? "n/a" : formatDecimal(value);
}

function formatRunTime(submittedAt: string): string {
  const date = new Date(submittedAt);
  if (Number.isNaN(date.getTime())) return "recent";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
}

function presetFilterClass(active: boolean) {
  return cn(
    "rounded-full border px-3 py-1 text-xs font-bold transition-colors",
    active
      ? "border-primary bg-primary/10 text-primary"
      : "border-border bg-background text-muted-foreground hover:bg-muted",
  );
}

function presetMatchesSearch(preset: RetrievalSearchPreset, search: string) {
  const normalizedSearch = search.trim().toLowerCase();
  if (!normalizedSearch) return true;

  return [
    preset.label,
    preset.description,
    preset.query,
    preset.category,
    preset.schema_id,
    preset.detected_format,
    preset.resource_type,
    preset.clinical_domain,
    preset.standard_system,
    preset.source_type,
    ...preset.fields,
    ...preset.target_sources,
    ...preset.launch_hint_targets,
  ].some((value) => value?.toLowerCase().includes(normalizedSearch));
}

function sourceFilterChipClass(active: boolean) {
  return cn(
    "rounded-full border px-2.5 py-1 text-xs font-bold transition-colors",
    active
      ? "border-primary bg-primary/10 text-primary"
      : "border-border bg-background text-muted-foreground hover:bg-muted",
  );
}

function sourceMatchesInventoryFilters(
  source: RetrievalSource,
  filters: {
    domain: string | null;
    search: string;
    standard: string | null;
    type: string | null;
  },
) {
  if (filters.type && source.source_type !== filters.type) return false;
  if (filters.domain && source.clinical_domain !== filters.domain) return false;
  if (filters.standard && source.standard_system !== filters.standard) return false;

  const normalizedSearch = filters.search.trim().toLowerCase();
  if (!normalizedSearch) return true;
  return [
    source.source_id,
    source.title,
    source.source_type,
    source.clinical_domain,
    source.standard_system,
    source.source_version,
    source.trust_level,
  ].some((value) => value?.toLowerCase().includes(normalizedSearch));
}

function mergeSearchOptions(
  options: RetrievalSearchOption[],
  additionalValues: Array<string | null | undefined>,
  currentValue: string,
) {
  const merged = new Map<string, RetrievalSearchOption>();
  for (const option of options) {
    if (!option.value) continue;
    merged.set(option.value, option);
  }
  for (const value of [...additionalValues, currentValue]) {
    if (!value || merged.has(value)) continue;
    merged.set(value, { value, label: humanize(value) });
  }
  return Array.from(merged.values()).sort((left, right) =>
    left.label.localeCompare(right.label),
  );
}

function uniqueNumberValues(values: Array<number | null | undefined>) {
  return Array.from(
    new Set(values.filter((value): value is number => typeof value === "number" && value > 0)),
  ).sort((left, right) => left - right);
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
