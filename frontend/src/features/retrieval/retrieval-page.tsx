import * as React from "react";
import {
  AlertTriangle,
  ExternalLink,
  FileSearch,
  Loader2,
  RefreshCw,
  Search,
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
import { HelpTooltip } from "../../components/ui/help-tooltip";
import { PageHeader } from "../../components/layout/page-header";
import { Notice } from "../../components/ui/notice";
import {
  useRetrievalReindexMutation,
  useDeleteRetrievalJudgmentMutation,
  useRetrievalIntegrityQuery,
  useRetrievalJudgmentEvaluationQuery,
  useRetrievalJudgmentMutation,
  useRetrievalJudgmentSummaryQuery,
  useRetrievalJudgmentsQuery,
  useRetrievalPlanQuery,
  useRetrievalPresetsQuery,
  useRetrievalSearchOptionsQuery,
  useRetrievalSearchMutation,
  useRetrievalSourcesQuery,
  useRuntimeConfigQuery,
  useSchemasQuery,
  workflowErrorMessage,
} from "../../lib/server-state";
import { cn, humanize } from "../../lib/utils";
import { ActiveFilterBar } from "./components/active-filter-bar";
import { EvidencePackBuckets } from "./components/evidence-pack-buckets";
import { EvidenceInterpretationPanel } from "./components/evidence-interpretation-panel";
import { EvidenceReadinessPanel } from "./components/evidence-readiness-panel";
import { EvidenceSupportMatrix } from "./components/evidence-support-matrix";
import { RetrievalFirstRunGuide } from "./components/first-run-guide";
import { HitCard } from "./components/hit-card";
import { RelevanceJudgmentSummary } from "./components/judgment-evaluation-panels";
import { NoResultRemediationPanel } from "./components/no-result-remediation-panel";
import {
  QualitySignalList,
  qualitySignalBadgeVariant,
} from "./components/quality-signal-list";
import { RankedEvidenceTriage } from "./components/ranked-evidence-triage";
import { RetrievalInlineGuide } from "./components/retrieval-inline-guide";
import { RetrievalReviewPathPanel } from "./components/retrieval-review-path";
import {
  GraphPanel,
  IntegrityPanel,
  RetrievalRuntimeStatusStrip,
  RuntimeDiversityBadge,
  RuntimeRerankBadge,
} from "./components/retrieval-runtime-status";
import type { QueryAnalysisBlockView } from "./components/query-analysis-block";
import {
  RetrievalSummaryStrip,
  type RetrievalSummaryStripViewModel,
} from "./components/retrieval-summary-strip";
import {
  RetrievalSearchCockpit,
} from "./components/retrieval-search-cockpit";
import {
  RetrievalTracePanel,
  type RetrievalTracePanelView,
} from "./components/retrieval-trace-panel";
import {
  SearchRunComparisonPanel,
} from "./components/search-run-comparison-panel";
import { RecommendedActionsPanel } from "./components/recommended-actions-panel";
import { ResultFacets } from "./components/result-facets";
import { SearchAnswerCard } from "./components/search-answer-card";
import {
  type QueryHealthItem,
  type SearchReadinessChecklistItem,
} from "./components/search-cockpit-panels";
import type {
  FilterSuggestionStack,
  QueryAspectStack,
} from "./components/search-plan-detail-panels";
import {
  SearchPlanPreview,
  type SearchPlanPreviewView,
} from "./components/search-plan-preview";
import { SearchPresetStrip } from "./components/search-preset-strip";
import { SearchRunHistory } from "./components/search-run-history";
import { SectionHelpText } from "./components/section-help-text";
import { SourceInventoryPanel } from "./components/source-inventory-panel";
import {
  type DiversitySelectionStack,
  type DiversityStack,
} from "./components/source-diversity-panel";
import { SourceScopePicker } from "./components/source-scope-picker";
import {
  type SearchPlanFilterAction,
  type SearchPlanFilterField,
} from "./components/strategy-standard-panels";
import { SubmittedSearchSummary } from "./components/submitted-search-summary";
import { TokenList } from "./components/token-list";
import {
  comparisonOperatorSummary,
  comparisonRecommendedActionSummary,
  comparisonReportFromComparison,
  comparisonReportRecommendedActions,
  type RetrievalComparisonOperatorSummary,
  type RetrievalComparisonRecommendedAction,
  type RetrievalComparisonRecommendedActionSummary,
} from "./model/retrieval-comparison-diagnosis";
import {
  evidenceSignalsFromHit,
  evidenceSupportMatrixRows,
  evidenceSupportStatus,
  evidenceSupportSummary,
  hitMatchExplanation,
  provenanceEntriesFromEvidence,
  type EvidenceProvenanceEntry,
  type EvidenceSupportMatrixRow,
  type EvidenceSupportSummary,
} from "./model/retrieval-evidence-model";
import {
  compareSearchRuns,
  comparisonRulePackChangeViews,
  type RetrievalRunComparison,
} from "./model/retrieval-run-comparison";
import { retrievalSearchCockpitView } from "./model/retrieval-cockpit-view-model";
import {
  medicalSearchHintReport,
  retrievalDiversityReport,
  retrievalInterpretationReport,
  retrievalSearchPlanPreviewReport,
  retrievalStandardSearchPlanReport,
} from "./model/retrieval-report-model";
import {
  plannedTaskSearchOverrides,
  retrievalPayloadFromForm,
  retrievalSearchSignature,
  type RetrievalFormState,
} from "./model/retrieval-search-payload";
import {
  queryAnalysisFromPackage,
  queryAnalysisFromPlan,
  queryVariantsFromAnalysis,
  queryVariantsFromTrace,
  searchPlanCoverageSummary,
  searchPlanRiskSignals,
  searchPlanTaskSummary,
  type QueryAnalysisStack,
  type QueryDiagnosticStack,
  type QueryProfileStack,
} from "./model/retrieval-query-analysis";
import {
  diversityFromPackage,
  formatDiversityTrace,
  formatEmbeddingStack,
  formatFrameworkStack,
  formatQualityPolicyTrace,
  formatRerankerStack,
  formatSourceCoverage,
  fusionDiagnosticsFromPackage,
  hybridStackValue,
  qualityPolicyFromPackage,
  rankingStackFromPackage,
  type RetrievalRankingStack,
} from "./model/retrieval-runtime-stack";
import {
  conceptGroundingSummariesFromPackage,
  correctiveActionSummaryFromPackage,
  coverageSummariesFromPackage,
  queryAspectSummariesFromPackage,
  queryProfileSummaryFromPackage,
  retrievalRulePacksFromPackage,
  retrievalRunSummary,
  serverSearchSignatureFromPackage,
  type CorrectiveActionSummary,
  type RetrievalRunSummary,
  type RetrievalSearchRun,
} from "./model/retrieval-run-summary";
import { searchRunRemediationSummary } from "./model/search-run-presentation";
import type {
  Evidence,
  RetrievalEvidenceBucket,
  RetrievalGraphContext,
  RetrievalHit,
  RetrievalIntegrityReport,
  RetrievalPackage,
  RetrievalCoverage,
  RetrievalJudgmentEvaluationResult,
  RetrievalQualitySummary,
  RetrievalRecommendedAction,
  RetrievalRelevanceJudgment,
  RetrievalRelevanceJudgmentSummary,
  RetrievalSearchPayload,
  RetrievalSearchOption,
  RetrievalSearchPreset,
  RetrievalSearchTask,
  RetrievalSource,
  RuntimeConfig,
} from "../../types";

type SupportedFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";
type FacetFilterField = Exclude<SupportedFilterField, "source_id">;
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
const supportedSuggestionFilterFields = new Set<SupportedFilterField>([
  "clinical_domain",
  "source_id",
  "standard_system",
  "source_type",
  "trust_level",
]);
const facetFilterFields: FacetFilterField[] = [
  "clinical_domain",
  "standard_system",
  "source_type",
  "trust_level",
];
const searchRunHistoryLimit = 6;
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
  const [sourceId, setSourceId] = React.useState("");
  const [topK, setTopK] = React.useState(5);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [planControlNotice, setPlanControlNotice] = React.useState<string | null>(null);
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
  const [planPayload, setPlanPayload] = React.useState<RetrievalSearchPayload | null>(null);

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
    return baselineRun
      ? compareSearchRuns(
          activeRun,
          baselineRun,
          facetFilterFields.map((field) => ({
            field,
            label: filterFieldLabel(field),
          })),
        )
      : null;
  }, [activeRun, comparisonBaselineRunId, searchRuns]);
  const comparisonJudgments = React.useMemo(
    () =>
      activeRunComparison
        ? judgmentsForComparison(activeRunComparison, relevanceJudgments)
        : [],
    [activeRunComparison, relevanceJudgments],
  );
  const comparisonRecommendedActions = React.useMemo(
    () =>
      activeRunComparison
        ? comparisonReportRecommendedActions(activeRunComparison, comparisonJudgments)
        : [],
    [activeRunComparison, comparisonJudgments],
  );
  const comparisonActionSummary = React.useMemo(
    () => comparisonRecommendedActionSummary(comparisonRecommendedActions),
    [comparisonRecommendedActions],
  );
  const comparisonOperatorView = React.useMemo(
    () =>
      activeRunComparison
        ? comparisonOperatorSummary(activeRunComparison, comparisonRecommendedActions)
        : null,
    [activeRunComparison, comparisonRecommendedActions],
  );
  const comparisonReportJson = React.useMemo(
    () =>
      activeRunComparison
        ? JSON.stringify(
            comparisonReportFromComparison(
              activeRunComparison,
              comparisonJudgments,
              comparisonRecommendedActions,
            ),
            null,
            2,
          )
        : "",
    [activeRunComparison, comparisonJudgments, comparisonRecommendedActions],
  );
  const comparisonRulePackViews = React.useMemo(
    () =>
      activeRunComparison
        ? comparisonRulePackChangeViews(activeRunComparison.rulePackChanges)
        : [],
    [activeRunComparison],
  );
  const packageData = activeRun?.packageData ?? searchMutation.data;
  const tracePanelView = React.useMemo(
    () => retrievalTracePanelView(packageData),
    [packageData],
  );
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
  const selectedSource = sourceId
    ? sources.find((source) => source.source_id === sourceId) ?? null
    : null;
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
  const runtimeStatusView = packageData
    ? (() => {
        const ranking = rankingStackFromPackage(packageData);
        const diversity = diversityFromPackage(packageData);
        return {
          graphEdgeCount: graphContext?.edges.length ?? null,
          graphNodeCount: graphContext?.nodes.length ?? null,
          graphTripleCount: graphContext?.triples.length ?? null,
          integrityStatus: integrityQuery.data?.status ?? "loading",
          rerankerEnabled: ranking.reranker.enabled,
          retrievalMode: humanize(ranking.framework.name || packageData.trace.strategy),
          sourceCoverageLabel: formatSourceCoverage(diversity),
          sourceDiversityEnabled: diversity.enabled,
        };
      })()
    : null;
  const activeFacetFilters: ActiveFacetFilters = {
    clinical_domain: clinicalDomain || undefined,
    standard_system: standardSystem || undefined,
    source_type: sourceType || undefined,
    trust_level: trustLevel || undefined,
    source_id: sourceId || undefined,
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
    sourceId,
    topK,
  };
  const currentSearchSignature = retrievalSearchSignature(retrievalPayloadFromForm(formState));
  const submittedSearchSignature = submittedSearchPayload
    ? retrievalSearchSignature(submittedSearchPayload)
    : null;
  const planQuery = useRetrievalPlanQuery(planPayload);
  const isSearchResultStale = Boolean(
    packageData &&
      submittedSearchSignature &&
      currentSearchSignature !== submittedSearchSignature,
  );
  const isPlanForCurrentSearch = Boolean(
    planPayload && retrievalSearchSignature(planPayload) === currentSearchSignature,
  );
  const currentPlanData = isPlanForCurrentSearch ? planQuery.data : undefined;
  const currentPlanPayload = isPlanForCurrentSearch ? planPayload : null;
  const packageDataForPlanPreview = isSearchResultStale ? undefined : packageData;
  const planPreviewView = React.useMemo<SearchPlanPreviewView | null>(() => {
    if (!packageDataForPlanPreview && !currentPlanData) return null;
    const analysis = packageDataForPlanPreview
      ? queryAnalysisFromPackage(packageDataForPlanPreview)
      : queryAnalysisFromPlan(currentPlanData!);
    return {
      analysis,
      coverageSummary: searchPlanCoverageSummary(analysis),
      planSummary: currentPlanData?.summary ?? null,
      profile: analysis.queryProfile,
      qualitySummary: packageDataForPlanPreview?.quality_summary ?? null,
      riskSignals: searchPlanRiskSignals(analysis),
      taskSummary: searchPlanTaskSummary(analysis),
      variants: packageDataForPlanPreview
        ? queryVariantsFromTrace(packageDataForPlanPreview.trace)
        : queryVariantsFromAnalysis(analysis),
    };
  }, [currentPlanData, packageDataForPlanPreview]);
  const copyPlanPreview = React.useCallback(async () => {
    await copyTextToClipboard(
      JSON.stringify(
        retrievalSearchPlanPreviewReport(
          packageDataForPlanPreview,
          packageDataForPlanPreview ? submittedSearchPayload : currentPlanPayload,
          currentPlanData,
        ),
        null,
        2,
      ),
    );
  }, [
    currentPlanData,
    currentPlanPayload,
    packageDataForPlanPreview,
    submittedSearchPayload,
  ]);

  const executeSearch = async (overrides: Partial<RetrievalSearchPayload> = {}) => {
    const payload = retrievalPayloadFromForm(formState, overrides);
    if (!payload.query) {
      setFormError("Enter a retrieval query before searching.");
      return;
    }
    setFormError(null);
    setPlanControlNotice(null);
    const packageResult = await searchMutation.mutateAsync(payload);
    const signature = serverSearchSignatureFromPackage(packageResult) ?? retrievalSearchSignature(payload);
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

  const markCustomSearch = () => {
    setActivePresetId(null);
    setPlanControlNotice(null);
  };

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
    setPlanControlNotice(null);
    setActivePresetId(preset.preset_id);
  }, []);

  React.useEffect(() => {
    if (didApplyInitialPreset || !presets.length) return;
    applyPreset(presets[0]);
    setDidApplyInitialPreset(true);
  }, [applyPreset, didApplyInitialPreset, presets]);

  React.useEffect(() => {
    const payload = retrievalPayloadFromForm(formState);
    if (!payload.query) {
      setPlanPayload(null);
      return;
    }
    const timeoutId = window.setTimeout(() => {
      setPlanPayload(payload);
    }, 400);
    return () => window.clearTimeout(timeoutId);
  }, [currentSearchSignature]);

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

  const applyFilterControl = (
    field: SupportedFilterField,
    value: string,
  ): Partial<RetrievalSearchPayload> => {
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
    } else if (field === "source_id") {
      setSourceId(value);
      overrides.filters = { source_id: value };
    }
    return overrides;
  };

  const applySearchFilter = (field: SupportedFilterField, value: string) => {
    markCustomSearch();
    const overrides = applyFilterControl(field, value);
    void executeSearch(overrides);
  };

  const runPlannedTask = (task: RetrievalSearchTask) => {
    markCustomSearch();
    const overrides = plannedTaskSearchOverrides(task);
    setQuery(task.query);
    if (overrides.clinical_domain !== undefined) {
      setClinicalDomain(overrides.clinical_domain ?? "");
    }
    if (overrides.standard_system !== undefined) {
      setStandardSystem(overrides.standard_system ?? "");
    }
    if (overrides.source_type !== undefined) {
      setSourceType(overrides.source_type ?? "");
    }
    if (overrides.trust_level !== undefined) {
      setTrustLevel(overrides.trust_level ?? "");
    }
    if (overrides.filters?.source_id !== undefined) {
      setSourceId(overrides.filters.source_id ?? "");
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
    } else if (field === "source_id") {
      setSourceId("");
      overrides.filters = { source_id: null };
    }
    if (packageData) void executeSearch(overrides);
  };

  const clearAllSearchFilters = () => {
    markCustomSearch();
    setClinicalDomain("");
    setStandardSystem("");
    setSourceType("");
    setSourceId("");
    setTrustLevel("");
    if (packageData) {
      void executeSearch({
        clinical_domain: null,
        standard_system: null,
        source_type: null,
        trust_level: null,
        filters: { source_id: null },
      });
    }
  };

  const applySourceIdFilter = (nextSourceId: string) => {
    markCustomSearch();
    setSourceId(nextSourceId);
    if (packageData) {
      void executeSearch({ filters: { source_id: nextSourceId } });
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
    setSourceId(payload.filters?.source_id ?? "");
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

  const applyPlanFilterSuggestion = (suggestion: FilterSuggestionStack) => {
    if (!isSupportedFilterField(suggestion.field)) return;
    markCustomSearch();
    const overrides = applyFilterControl(suggestion.field, suggestion.value);
    if (packageDataForPlanPreview) {
      void executeSearch(overrides);
    } else {
      setPlanControlNotice(
        `${filterFieldLabel(suggestion.field)} set to ${formatFilterValue(suggestion.field, suggestion.value)}. Run search to refresh evidence.`,
      );
    }
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

      <RetrievalInlineGuide />

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
                <span className="inline-flex items-center gap-1.5">
                  Query
                  <HelpTooltip label="Retrieval query help">
                    Ask for the evidence you need, not a diagnosis. Include the data operation, field names, standard, or validation issue when known.
                  </HelpTooltip>
                </span>
                <Textarea
                  className="min-h-24 resize-y"
                  onChange={(event) => {
                    markCustomSearch();
                    setQuery(event.target.value);
                    if (formError) setFormError(null);
                  }}
                  placeholder="Example: explain missing units for lab_result_v1 glucose CSV fields"
                  value={query}
                />
              </Label>

              <Label>
                <span className="inline-flex items-center gap-1.5">
                  Fields
                  <HelpTooltip label="Retrieval fields help">
                    Optional comma-separated dataset fields. Field names help retrieval match schema rules and PHI-sensitive columns.
                  </HelpTooltip>
                </span>
                <Textarea
                  className="min-h-16 resize-y"
                  onChange={(event) => {
                    markCustomSearch();
                    setFields(event.target.value);
                  }}
                  placeholder="date, patient_id, lab_name, value, unit"
                  value={fields}
                />
              </Label>

              <div className="grid gap-3 sm:grid-cols-2">
                <Label>
                  <span className="inline-flex items-center gap-1.5">
                    Schema
                    <HelpTooltip label="Schema filter help">
                      Limits retrieval to evidence related to a known OJTFlow schema. Leave blank for broad discovery.
                    </HelpTooltip>
                  </span>
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
                  <span className="inline-flex items-center gap-1.5">
                    Top K
                    <HelpTooltip label="Top K help">
                      Number of ranked evidence hits to return. Use more for exploration and fewer for focused review.
                    </HelpTooltip>
                  </span>
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
                  <span className="inline-flex items-center gap-1.5">
                    Format
                    <HelpTooltip label="Format filter help">
                      Narrows search to evidence about a source data format such as CSV, JSON, Markdown, PDF text, or FHIR-like JSON.
                    </HelpTooltip>
                  </span>
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
                  <span className="inline-flex items-center gap-1.5">
                    Resource
                    <HelpTooltip label="Resource filter help">
                      Optional healthcare resource type, for example Observation. Useful for FHIR-like mapping questions.
                    </HelpTooltip>
                  </span>
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
                  <span className="inline-flex items-center gap-1.5">
                    Domain
                    <HelpTooltip label="Clinical domain help">
                      Narrows evidence to a clinical data area such as laboratory, medication, or observation.
                    </HelpTooltip>
                  </span>
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
                  <span className="inline-flex items-center gap-1.5">
                    Standard
                    <HelpTooltip label="Standard filter help">
                      Narrows evidence to a terminology or data standard such as UCUM, LOINC, SNOMED, or FHIR when available.
                    </HelpTooltip>
                  </span>
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
                  <span className="inline-flex items-center gap-1.5">
                    Trust
                    <HelpTooltip label="Trust filter help">
                      Controls source trust level. Approved is safer for governed workflows; broader trust may help exploration.
                    </HelpTooltip>
                  </span>
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
                  <span className="inline-flex items-center gap-1.5">
                    Source type
                    <HelpTooltip label="Source type filter help">
                      Narrows evidence by source class, such as schema, terminology, policy, corpus document, or locator.
                    </HelpTooltip>
                  </span>
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

              <SourceScopePicker
                isSearchPending={searchMutation.isPending}
                onClear={() => {
                  markCustomSearch();
                  setSourceId("");
                  if (packageData) void executeSearch({ filters: { source_id: null } });
                }}
                onSelect={(nextSourceId) => {
                  markCustomSearch();
                  setSourceId(nextSourceId);
                }}
                selectedSource={selectedSource}
                sourceId={sourceId}
                sources={sources}
              />

              <ActiveFilterBar
                filters={activeFilterEntries(activeFacetFilters)}
                isSearchPending={searchMutation.isPending}
                onClearAll={clearAllSearchFilters}
                onRemove={clearSearchFilter}
              />

              {planControlNotice ? (
                <Notice title="Plan filter applied">
                  {planControlNotice}
                </Notice>
              ) : null}

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
          <SearchPlanPreview
            copyTextToClipboard={copyTextToClipboard}
            formatCount={formatCount}
            formatFilterValue={formatMaybeSupportedFilterValue}
            isSearchPending={searchMutation.isPending}
            isPlanLoading={planQuery.isFetching}
            isSupportedFilterField={isSupportedFilterField}
            onApplyFilterSuggestion={applyPlanFilterSuggestion}
            onCopyPlan={copyPlanPreview}
            onRunTask={runPlannedTask}
            planError={planQuery.isError ? workflowErrorMessage(planQuery.error) : null}
            qualitySummaryBadgeVariant={qualitySummaryBadgeVariant}
            useCopyFeedback={useCopyFeedback}
            view={planPreviewView}
          />
          <SearchRunHistory
            activeRunId={activeRunId}
            comparisonBaselineRunId={comparisonBaselineRunId}
            comparisonNode={
              activeRunComparison && comparisonOperatorView ? (
                <SearchRunComparisonPanel
                  actionSummary={comparisonActionSummary}
                  comparison={activeRunComparison}
                  copyTextToClipboard={copyTextToClipboard}
                  deltaBadgeVariant={deltaBadgeVariant}
                  formatCount={formatCount}
                  formatDecimal={formatDecimal}
                  formatPercent={formatPercent}
                  formatSignedDelta={formatSignedDelta}
                  operatorSummary={comparisonOperatorView}
                  readinessLabel={readinessGlanceLabel(activeRunComparison)}
                  recommendedActions={comparisonRecommendedActions}
                  reportJson={comparisonReportJson}
                  rulePackChanges={comparisonRulePackViews}
                />
              ) : null
            }
            isSearchPending={searchMutation.isPending}
            onClear={clearSearchRuns}
            onRestore={restoreSearchRun}
            onSetComparisonBaseline={setComparisonBaselineRunId}
            runs={searchRuns}
          />
        </div>

        <div className="grid min-w-0 gap-5">
          {runtimeStatusView ? (
            <RetrievalRuntimeStatusStrip view={runtimeStatusView} />
          ) : null}
          <SearchResults
            activeFilters={activeFacetFilters}
            isSearchPending={searchMutation.isPending}
            isStale={isSearchResultStale}
            onApplyFacet={applySearchFilter}
            onClearAllFilters={clearAllSearchFilters}
            onClearFilter={clearSearchFilter}
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
            <RetrievalTracePanel
              activeFilters={
                submittedSearchPayload
                  ? activeFilterEntries(activeFacetFiltersFromPayload(submittedSearchPayload))
                  : activeFilterEntries(activeFacetFilters)
              }
              filterFieldLabel={filterFieldLabel}
              formatCount={formatCount}
              formatFilterValue={formatFilterValue}
              getActionFilter={recommendedActionFilter}
              getActionSourceLabel={recommendedActionSourceLabel}
              getCoverageSuggestedAction={coverageSuggestedAction}
              getCoverageSuggestedFilter={coverageSuggestedFilter}
              isSearchPending={searchMutation.isPending}
              isSuggestionSupported={isSupportedFilterField}
              onApplyCoverageFilter={applySearchFilter}
              onClearAllFilters={clearAllSearchFilters}
              onClearSourceScope={() => clearSearchFilter("source_id")}
              onApplyFilterSuggestion={applyFilterSuggestion}
              view={tracePanelView}
            />
            <GraphPanel graphContext={graphContext} />
          </div>
          <IntegrityPanel
            checks={
              integrityQuery.data ? prioritizedIntegrityChecks(integrityQuery.data) : []
            }
            formatCount={formatCount}
            formatHash={shortHash}
            includeCorpus={includeCorpusIntegrity}
            integrityBadgeVariant={integrityBadgeVariant}
            isFetching={integrityQuery.isFetching}
            onRefresh={() => void integrityQuery.refetch()}
            onToggleCorpus={() => setIncludeCorpusIntegrity((current) => !current)}
            report={integrityQuery.data}
          />
          <SourceInventoryPanel
            isLoading={sourcesQuery.isLoading}
            onUseSource={applySourceIdFilter}
            sources={sources}
          />
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
  const summary: RetrievalSummaryStripViewModel = {
    coverageSupporting: diversity
      ? `${diversity.selectedSourceCount} selected unique sources`
      : embeddingProvider
        ? `${embeddingProvider} embeddings`
        : "Runtime loading",
    coverageValue: diversity ? formatSourceCoverage(diversity) : graph?.nodes.length ?? 0,
    hitSupporting: packageData ? packageData.trace.strategy : "No search yet",
    hitValue: packageData?.hits.length ?? 0,
    readinessSupporting: qualitySummary?.top_action ?? "Run search to assess package quality",
    readinessTone: qualitySummaryTone(qualitySummary),
    readinessValue: qualitySummary ? `${qualitySummary.score}/100` : "n/a",
    rerankerEnabled,
    rerankerSupporting: rerankerProvider
      ? rerankerEnabled
        ? `${rerankerProvider} second stage`
        : `${rerankerProvider} disabled`
      : "Runtime loading",
    sourceCount: sources.length,
    sourcesLoading,
  };
  return <RetrievalSummaryStrip summary={summary} />;
}

function qualitySummaryBadgeVariant(
  summary: RetrievalQualitySummary,
): "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
}

function SearchResults({
  activeFilters,
  isSearchPending,
  isStale,
  onApplyFacet,
  onClearAllFilters,
  onClearFilter,
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
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
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
          <RetrievalFirstRunGuide />
        </CardContent>
      </Card>
    );
  }

  const resultFilters = submittedSearchPayload
    ? activeFacetFiltersFromPayload(submittedSearchPayload)
    : activeFilters;
  const resultFilterEntries = activeFilterEntries(resultFilters);
  const diversitySelections = diversitySelectionByEvidenceId(packageData);
  const diversity = diversityFromPackage(packageData);
  const ranking = rankingStackFromPackage(packageData);
  const runJudgments = runId
    ? judgmentsForRunHits(runId, packageData.hits, relevanceJudgments)
    : [];
  const judgmentMetrics = relevanceJudgmentMetrics(packageData.hits, runJudgments);
  const requiredBuckets = (packageData.evidence_buckets ?? []).filter(
    (bucket) => bucket.required,
  );
  const coveredRequiredBuckets = requiredBuckets.filter((bucket) => bucket.hit_count > 0);
  const cockpitView = retrievalSearchCockpitView(packageData, submittedSearchPayload);
  const cockpitReportJson = JSON.stringify(
    retrievalCockpitReportFromPackage(packageData, submittedSearchPayload),
    null,
    2,
  );

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70">
        <div>
          <CardTitle>Ranked evidence</CardTitle>
          <CardDescription>
            {formatCount(packageData.hits.length, "hit")} from{" "}
            {formatCount(packageData.trace.candidates_seen, "candidate")}.{" "}
            The retrieval stack combines lexical search, vector search, and optional
            reranking. How many independent sources survived source-diversity selection
            is shown in the diversity badges. Concepts and query aspects detected from the search are listed in query analysis.
          </CardDescription>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          {isStale ? <Badge variant="warning">pending changes</Badge> : null}
          <Badge variant="muted">{packageData.trace.strategy}</Badge>
          <RuntimeDiversityBadge
            enabled={diversity.enabled}
            sourceCoverageLabel={formatSourceCoverage(diversity)}
          />
          <RuntimeRerankBadge enabled={ranking.reranker.enabled} />
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        <RankedEvidenceTriage
          view={{
            candidateCount: packageData.trace.candidates_seen,
            coveredRequiredBucketCount: coveredRequiredBuckets.length,
            hitCount: packageData.hits.length,
            isStale,
            judgedCount: judgmentMetrics.judgedCount,
            qualitySummary: packageData.quality_summary ?? null,
            requiredBucketCount: requiredBuckets.length,
          }}
        />
        <RetrievalSearchCockpit
          copyTextToClipboard={copyTextToClipboard}
          filterFieldLabel={filterFieldLabel}
          getSuggestedFilterAction={suggestedFilterAction}
          isSearchPending={isSearchPending}
          onApplyFilter={onApplyFacet}
          onClearAllFilters={onClearAllFilters}
          onClearSourceScope={() => onClearFilter("source_id")}
          reportJson={cockpitReportJson}
          view={cockpitView}
        />
        <SearchAnswerCard
          packageData={packageData}
          submittedSearchPayload={submittedSearchPayload}
        />
        <RetrievalReviewPathPanel packageData={packageData} />
        <EvidenceInterpretationPanel packageData={packageData} />
        {submittedSearchPayload ? (
          <SubmittedSearchSummary
            filters={activeFilterEntries(activeFacetFiltersFromPayload(submittedSearchPayload))}
            isRestoreDisabled={isSearchPending}
            isStale={isStale}
            onRestore={onRestoreSubmittedSearch}
            payload={submittedSearchPayload}
          />
        ) : null}
        <RelevanceJudgmentSummary
          copyTextToClipboard={copyTextToClipboard}
          evaluationReportJson={
            persistedJudgmentEvaluation
              ? JSON.stringify(
                  evaluationReportFromJudgmentSummary(
                    persistedJudgmentEvaluation,
                    judgmentMetrics,
                    persistedJudgmentSummary,
                    packageData,
                  ),
                  null,
                  2,
                )
              : null
          }
          formatCount={formatCount}
          formatDecimal={formatDecimal}
          formatNullableDecimal={formatNullableDecimal}
          formatNullablePercent={formatNullablePercent}
          formatPercent={formatPercent}
          isSyncing={isJudgmentSyncing}
          metrics={judgmentMetrics}
          persistedEvaluation={persistedJudgmentEvaluation}
          persistedSummary={persistedJudgmentSummary}
          qualitySignalBadgeVariant={qualitySignalBadgeVariant}
        />
        <EvidenceReadinessPanel
          filterFieldLabel={filterFieldLabel}
          formatFilterValue={formatFilterValue}
          getBucketSuggestedFilter={bucketSuggestedFilter}
          isSearchPending={isSearchPending}
          onApplyBucketFilter={onApplyFacet}
          packageData={packageData}
        />
        <RecommendedActionsPanel
          activeFilters={resultFilterEntries}
          actions={packageData.recommended_actions ?? []}
          filterFieldLabel={filterFieldLabel}
          formatFilterValue={formatFilterValue}
          getActionFilter={recommendedActionFilter}
          getActionSourceLabel={recommendedActionSourceLabel}
          isSearchPending={isSearchPending}
          onApplyFilter={onApplyFacet}
          onClearAllFilters={onClearAllFilters}
          onClearSourceScope={() => onClearFilter("source_id")}
        />
        <EvidencePackBuckets buckets={packageData.evidence_buckets ?? []} />
        <EvidenceSupportMatrix
          formatCount={formatCount}
          formatScore={formatScore}
          humanize={humanize}
          judgmentBadgeVariant={judgmentBadgeVariant}
          judgmentLabel={judgmentLabel}
          rows={evidenceSupportMatrixRows({
            formatConfidence,
            packageData,
            relevanceJudgments,
            runId,
            standardSystemValue: optionalStringValue,
            summaryForHit: evidenceSupportSummaryForHit,
          })}
          supportStatusBadgeVariant={supportStatusBadgeVariant}
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
            evidenceBuckets={packageData.evidence_buckets ?? []}
            formatClaim={formatClaim}
            formatConfidence={formatConfidence}
            formatCount={formatCount}
            formatScore={formatScore}
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
            judgmentLabel={judgmentLabel}
            recommendedActions={packageData.recommended_actions ?? []}
            onSetJudgment={(value) => onSetJudgment(hit.evidence, value)}
          />
        ))}
        {!packageData.hits.length ? (
          <NoResultRemediationPanel
            candidateCount={packageData.trace.candidates_seen}
            filterFieldLabel={filterFieldLabel}
            isSearchPending={isSearchPending}
            missingBucketCount={(packageData.evidence_buckets ?? []).filter(
              (bucket) => bucket.required && bucket.hit_count === 0,
            ).length}
            onApplyFacet={onApplyFacet}
            onClearAllFilters={onClearAllFilters}
            onClearFilter={onClearFilter}
            submittedFilters={
              submittedSearchPayload
                ? activeFilterEntries(activeFacetFiltersFromPayload(submittedSearchPayload))
                : []
            }
            suggestedAction={firstSupportedRecommendedAction(
              packageData.recommended_actions ?? [],
            )}
          />
        ) : null}
      </CardContent>
    </Card>
  );
}

function firstSupportedRecommendedAction(
  actions: RetrievalRecommendedAction[],
): CoverageFilterAction | null {
  for (const action of actions) {
    const filterAction = recommendedActionFilter(action);
    if (filterAction) return filterAction;
  }
  return null;
}

function queryHealthItems(
  payload: RetrievalSearchPayload | null,
  packageData: RetrievalPackage,
): QueryHealthItem[] {
  const analysis = queryAnalysisFromPackage(packageData);
  const queryTerms = payload?.query.trim().split(/\s+/).filter(Boolean) ?? [];
  const fields = payload?.fields ?? [];
  const filterCount = payload ? activeFilterEntries(activeFacetFiltersFromPayload(payload)).length : 0;
  const hasClinicalContext = Boolean(
    payload?.schema_id ||
      payload?.detected_format ||
      payload?.resource_type ||
      payload?.clinical_domain ||
      payload?.standard_system ||
      fields.length,
  );
  const exactSource = payload?.filters?.source_id ?? "";
  const hitCount = packageData.hits.length;
  const candidateCount = packageData.trace.candidates_seen;
  const topK = payload?.top_k ?? hitCount;
  const qualityStatus = packageData.quality_summary?.status ?? null;
  const warningCount =
    packageData.trace.warnings.length +
    packageData.trace.safety_flags.length +
    (packageData.quality_signals ?? []).filter((signal) => signal.severity !== "info").length;

  return [
    {
      code: "query_specificity",
      description:
        queryTerms.length >= 3
          ? "The query has enough wording to guide hybrid search and reranking."
          : "The query is short. Add the data type, issue, standard, or expected field names if results look broad.",
      label: "Query specificity",
      status: queryTerms.length >= 3 ? "ok" : "review",
    },
    {
      code: "clinical_context",
      description: hasClinicalContext
        ? "Schema, format, resource, domain, standard, or field context is present."
        : "No clinical data context is set. Add schema, format, resource, fields, or standard filters for safer grounding.",
      label: "Clinical context",
      status: hasClinicalContext ? "ok" : "review",
    },
    {
      code: "scope",
      description: exactSource
        ? `Exact source scope is active for ${exactSource}. Clear it before judging corpus-wide coverage.`
        : filterCount >= 3
          ? "Multiple filters are active. If evidence is sparse, loosen scope before concluding no evidence exists."
          : filterCount > 0
            ? "Some filters are active. Confirm they match the operational question."
            : "No source filters are active. This is good for discovery but may need narrowing for audit review.",
      label: "Search scope",
      status: exactSource || filterCount >= 3 ? "review" : "info",
    },
    {
      code: "result_coverage",
      description:
        hitCount === 0
          ? "No ranked evidence returned. Broaden scope, check source inventory, or apply backend recommendations."
          : hitCount < Math.min(topK, 3) && candidateCount > hitCount
            ? "Only a small ranked set survived selection. Inspect filters, readiness gaps, and reranker state."
            : `${hitCount} ranked hit(s) from ${candidateCount} candidate(s). Inspect readiness before individual claims.`,
      label: "Result coverage",
      status: hitCount === 0 ? "blocked" : hitCount < Math.min(topK, 3) ? "review" : "ok",
    },
    {
      code: "readiness",
      description: qualityStatus
        ? `Backend readiness is ${humanize(qualityStatus)}${
            packageData.quality_summary ? ` at ${packageData.quality_summary.score}/100` : ""
          }.`
        : "No readiness score returned. Treat this package as unreviewed.",
      label: "Readiness",
      status:
        qualityStatus === "ready"
          ? "ok"
          : qualityStatus === "blocked"
            ? "blocked"
            : qualityStatus
              ? "review"
              : "info",
    },
    {
      code: "safety",
      description: warningCount
        ? `${warningCount} warning or safety signal(s) were reported. Review these before using the evidence downstream.`
        : "No retrieval warnings or safety flags were reported for this package.",
      label: "Safety signals",
      status: warningCount ? "review" : "ok",
    },
    ...queryDiagnosticHealthItems(analysis.diagnostics),
  ];
}

function searchReadinessChecklist({
  diversity,
  packageData,
  queryHealth,
  requiredBuckets,
  topAction,
}: {
  diversity: DiversityStack;
  packageData: RetrievalPackage;
  queryHealth: QueryHealthItem[];
  requiredBuckets: RetrievalEvidenceBucket[];
  topAction: RetrievalRecommendedAction | null;
}): SearchReadinessChecklistItem[] {
  const blockedHealthCount = queryHealth.filter((item) => item.status === "blocked").length;
  const reviewHealthCount = queryHealth.filter((item) => item.status === "review").length;
  const missingRequiredBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const qualitySummary = packageData.quality_summary ?? null;
  const warningCount =
    packageData.trace.warnings.length +
    packageData.trace.safety_flags.length +
    (packageData.quality_signals ?? []).filter((signal) => signal.severity !== "info").length;

  return [
    {
      code: "query_health",
      detail:
        blockedHealthCount > 0
          ? `${formatCount(blockedHealthCount, "blocked check")} must be fixed before relying on results.`
          : reviewHealthCount > 0
            ? `${formatCount(reviewHealthCount, "review check")} need operator attention.`
            : "Query wording, context, scope, and result coverage are acceptable for inspection.",
      label: "Query health",
      status: blockedHealthCount > 0 ? "blocked" : reviewHealthCount > 0 ? "review" : "ok",
    },
    {
      code: "evidence_classes",
      detail: requiredBuckets.length
        ? `${requiredBuckets.length - missingRequiredBuckets.length}/${requiredBuckets.length} required evidence classes covered.`
        : "No required evidence-bucket policy is configured for this package.",
      label: "Evidence classes",
      status: missingRequiredBuckets.length ? "review" : "ok",
    },
    {
      code: "source_spread",
      detail: diversity.enabled
        ? `${formatCount(diversity.selectedSourceCount, "selected source")} from ${formatCount(diversity.candidateSourceCount, "candidate source")}; ${formatCount(diversity.duplicateSelectedSourceCount, "duplicate selected source")}.`
        : "Source diversity selection is disabled for this run.",
      label: "Source spread",
      status: diversity.enabled
        ? diversity.selectedSourceCount > 1 || packageData.hits.length <= 1
          ? "ok"
          : "review"
        : "review",
    },
    {
      code: "governance",
      detail: topAction
        ? `Next action: ${topAction.title}.`
        : qualitySummary
          ? `Readiness ${humanize(qualitySummary.status)} at ${qualitySummary.score}/100 with ${formatCount(warningCount, "warning signal")}.`
          : `No readiness score; ${formatCount(warningCount, "warning signal")} reported.`,
      label: "Governance",
      status:
        qualitySummary?.status === "blocked"
          ? "blocked"
          : topAction || warningCount > 0 || qualitySummary?.status === "review"
            ? "review"
            : "ok",
    },
  ];
}

function queryDiagnosticHealthItems(diagnostics: QueryDiagnosticStack[]): QueryHealthItem[] {
  return diagnostics
    .filter((diagnostic) => diagnostic.severity !== "info")
    .map((diagnostic) => ({
      code: `diagnostic_${diagnostic.code}`,
      description: `${diagnostic.message} Action: ${diagnostic.suggestedAction}`,
      label:
        diagnostic.code === "overconstrained_metadata_filters"
          ? "Filter over-constraint"
          : humanize(diagnostic.code),
      status:
        diagnostic.severity === "error" || diagnostic.severity === "destructive"
          ? "blocked"
          : "review",
    }));
}

function recommendedActionFilter(
  action: RetrievalRecommendedAction,
): CoverageFilterAction | null {
  if (action.action_type !== "apply_filter") return null;
  return suggestedFilterAction(action.suggested_filter);
}

function recommendedActionSourceLabel(action: RetrievalRecommendedAction): string | null {
  const source = stringValue(action.metadata.corrective_rule_source, "");
  if (!source) return null;
  if (source === "query_diagnostic") return "query diagnostic";
  if (source === "quality_signal") return "quality signal";
  return humanize(source);
}

function bucketSuggestedFilter(bucket: RetrievalEvidenceBucket): CoverageFilterAction | null {
  return suggestedFilterAction(bucket.suggested_filter);
}

function suggestedFilterAction(value: unknown): CoverageFilterAction | null {
  const suggestedFilter = recordValue(value);
  for (const [field, rawValue] of Object.entries(suggestedFilter)) {
    const filterValue = stringValue(rawValue, "");
    if (filterValue && isSupportedFilterField(field)) {
      return { field, value: filterValue };
    }
  }
  return null;
}

function activeFacetFiltersFromPayload(payload: RetrievalSearchPayload): ActiveFacetFilters {
  return {
    clinical_domain: payload.clinical_domain || undefined,
    standard_system: payload.standard_system || undefined,
    source_type: payload.source_type || undefined,
    trust_level: payload.trust_level || undefined,
    source_id: payload.filters?.source_id || undefined,
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
  if (field === "source_id") return "Source ID";
  if (field === "standard_system") return "Standard";
  if (field === "source_type") return "Source";
  return "Trust";
}

function formatFilterValue(field: SupportedFilterField, value: string): string {
  return field === "standard_system" || field === "source_id" ? value : humanize(value);
}

function formatMaybeSupportedFilterValue(field: string, value: string): string {
  return isSupportedFilterField(field) ? formatFilterValue(field, value) : value;
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

function retrievalTracePanelView(
  packageData: RetrievalPackage | undefined,
): RetrievalTracePanelView | null {
  if (!packageData) return null;
  const trace = packageData.trace;
  const stack = rankingStackFromPackage(packageData);
  const diversity = diversityFromPackage(packageData);
  const qualityPolicy = qualityPolicyFromPackage(packageData);
  const queryAnalysis = queryAnalysisFromPackage(packageData);
  const searchSignature = serverSearchSignatureFromPackage(packageData);
  return {
    coverage: packageData.coverage,
    facts: [
      { label: "Strategy", value: trace.strategy },
      { label: "Candidates", value: String(trace.candidates_seen) },
      { label: "Framework", value: formatFrameworkStack(stack) },
      { label: "Embedding", value: formatEmbeddingStack(stack) },
      { label: "Reranker", value: formatRerankerStack(stack) },
      { label: "Diversity", value: formatDiversityTrace(diversity) },
      { label: "Quality policy", value: formatQualityPolicyTrace(qualityPolicy) },
      {
        label: "Search signature",
        value: searchSignature ? formatShortSignature(searchSignature) : "unknown",
      },
    ],
    filtersApplied: trace.filters_applied,
    qualitySignals: packageData.quality_signals ?? [],
    queryAnalysis: queryAnalysisBlockView(queryAnalysis, trace.filters_applied),
    queryVariants: queryVariantsFromTrace(trace),
    recommendedActions: packageData.recommended_actions ?? [],
    safetyFlags: trace.safety_flags.map(humanize),
    warnings: trace.warnings,
  };
}

function queryAnalysisBlockView(
  analysis: QueryAnalysisStack | null,
  appliedFilters: Record<string, unknown>,
): QueryAnalysisBlockView | null {
  if (!analysis) {
    return null;
  }
  return {
    ...analysis,
    queryAspects: analysis.queryAspects.map((aspect) => ({
      ...aspect,
      filterEntries: queryAspectFilterEntries(aspect, appliedFilters),
    })),
    queryProfileFilterEntries: analysis.queryProfile
      ? queryProfileFilterEntries(analysis.queryProfile, appliedFilters)
      : [],
    queryProfileRouteHelpText:
      "The backend route chosen for this query, such as broad, structured, or safety-sensitive search. Use this to confirm the search behavior matches the question.",
  };
}

type RankingStack = RetrievalRankingStack;

type QueryProfileFilterEntry = {
  applied: boolean;
  displayValue: string;
  field: string;
  label: string;
  supported: boolean;
  value: string;
};

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

function evidenceSupportSummaryForHit(
  hit: RetrievalHit,
  provenanceEntries: EvidenceProvenanceEntry[],
): EvidenceSupportSummary {
  return evidenceSupportSummary({
    hit,
    provenanceEntries,
    signals: evidenceSignalsFromHit(hit),
  });
}

function supportStatusBadgeVariant(
  status: EvidenceSupportMatrixRow["supportStatus"],
): "success" | "warning" | "destructive" | "muted" {
  if (status === "strong") return "success";
  if (status === "partial") return "warning";
  return "destructive";
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

function useCopyFeedback(timeoutMs = 1800) {
  const [copiedKey, setCopiedKey] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!copiedKey) return;
    const timer = window.setTimeout(() => setCopiedKey(null), timeoutMs);
    return () => window.clearTimeout(timer);
  }, [copiedKey, timeoutMs]);

  const markCopied = React.useCallback((key: string) => {
    setCopiedKey(key);
  }, []);

  const clearCopied = React.useCallback(() => {
    setCopiedKey(null);
  }, []);

  return { clearCopied, copiedKey, markCopied };
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

function prioritizedIntegrityChecks(report: RetrievalIntegrityReport) {
  const nonOk = report.checks.filter((check) => check.status !== "ok");
  const source = nonOk.length ? nonOk : report.checks;
  return source.slice(0, nonOk.length ? 12 : 8);
}

function shortHash(value: string | null | undefined) {
  return value ? value.slice(0, 12) : "-";
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

function retrievalCockpitReportFromPackage(
  packageData: RetrievalPackage,
  submittedSearchPayload: RetrievalSearchPayload | null,
) {
  const analysis = queryAnalysisFromPackage(packageData);
  const ranking = rankingStackFromPackage(packageData);
  const conceptGrounding = conceptGroundingSummariesFromPackage(packageData);
  const coverage = coverageSummariesFromPackage(packageData);
  const diversity = diversityFromPackage(packageData);
  const rulePacks = retrievalRulePacksFromPackage(packageData);
  const queryHealth = queryHealthItems(submittedSearchPayload, packageData);
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const readinessChecklist = searchReadinessChecklist({
    diversity,
    packageData,
    queryHealth,
    requiredBuckets,
    topAction: (packageData.recommended_actions ?? [])[0] ?? null,
  });
  const runSummary = retrievalRunSummary(packageData);
  return {
    report_type: "retrieval_cockpit",
    version: 1,
    generated_at: new Date().toISOString(),
    query: submittedSearchPayload?.query ?? null,
    submitted_payload: submittedSearchPayload,
    search_signature: serverSearchSignatureFromPackage(packageData),
    retrieval: {
      strategy: packageData.trace.strategy,
      candidates_seen: packageData.trace.candidates_seen,
      hit_count: packageData.hits.length,
      top_evidence_ids: packageData.hits
        .slice(0, 10)
        .map((hit) => hit.evidence.evidence_id),
      filters_applied: packageData.trace.filters_applied,
      safety_flags: packageData.trace.safety_flags,
      warnings: packageData.trace.warnings,
    },
    evidence_hits: retrievalCockpitEvidenceHitReports(packageData),
    query_analysis: {
      query_health: queryHealth,
      strategy: analysis.strategy,
      query_profile: queryProfileSummaryFromPackage(packageData),
      variant_count: analysis.variantCount,
      standards: analysis.standards,
      detected_concepts: analysis.detectedConcepts,
      expanded_terms: analysis.expandedTerms,
      query_aspects: queryAspectSummariesFromPackage(packageData),
      diagnostics: analysis.diagnostics.map((diagnostic) => ({
        code: diagnostic.code,
        severity: diagnostic.severity,
        message: diagnostic.message,
        suggested_action: diagnostic.suggestedAction,
        metadata: diagnostic.metadata,
      })),
      rule_ids: analysis.ruleIds,
      medical_search_hints: medicalSearchHintReport(packageData),
    },
    ranking_stack: {
      embedding: ranking.embedding,
      framework: ranking.framework,
      reranker: ranking.reranker,
      hybrid_label: hybridStackValue(ranking),
      fusion_diagnostics: packageData.trace.fusion_diagnostics ?? {},
    },
    strategy_recommendations: (packageData.strategy_recommendations ?? []).map(
      (recommendation) => ({
        recommendation_id: recommendation.recommendation_id,
        title: recommendation.title,
        technique: recommendation.technique,
        status: recommendation.status,
        rationale: recommendation.rationale,
        source_signal_codes: recommendation.source_signal_codes,
        suggested_filters: recommendation.suggested_filters,
        metadata: recommendation.metadata,
      }),
    ),
    standard_search_plan: retrievalStandardSearchPlanReport(packageData),
    evidence_readiness: {
      readiness_checklist: readinessChecklist,
      quality_summary: packageData.quality_summary ?? null,
      quality_signals: packageData.quality_signals ?? [],
      evidence_buckets: packageData.evidence_buckets ?? [],
      coverage_gaps: coverage,
      concept_grounding: conceptGrounding,
      diversity: retrievalDiversityReport(packageData),
    },
    recommended_action_summary: packageData.recommended_action_summary ?? null,
    remediation_summary:
      runSummary.remediationSummary ?? searchRunRemediationSummary(runSummary),
    interpretation: retrievalInterpretationReport(packageData),
    recommended_actions: packageData.recommended_actions ?? [],
    facets: packageData.facets ?? null,
    graph_context: packageData.handoff_context.graph_context ?? null,
    retrieval_rule_packs: rulePacks.map((pack) => ({
      name: pack.name,
      status: pack.status,
      source: pack.source,
      env_var: pack.env_var,
      configured: pack.configured,
      rule_count: pack.rule_count,
      version: pack.version ?? null,
      content_hash: pack.content_hash ?? null,
    })),
  };
}

function retrievalCockpitEvidenceHitReports(packageData: RetrievalPackage) {
  const buckets = packageData.evidence_buckets ?? [];
  return packageData.hits.map((hit, index) => {
    const provenanceEntries = provenanceEntriesFromEvidence(hit.evidence);
    const signals = evidenceSignalsFromHit(hit);
    return {
      rank: index + 1,
      evidence_id: hit.evidence.evidence_id,
      source_id: hit.evidence.source_id,
      source_type: hit.evidence.source_type,
      trust_level: hit.evidence.trust_level,
      confidence: hit.evidence.confidence ?? null,
      score: hit.score,
      support_summary: evidenceSupportSummaryForHit(hit, provenanceEntries),
      match_explanation: hitMatchExplanation({
        buckets,
        hit,
        provenanceEntries,
        signals,
      }),
    };
  });
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
    evaluation_readiness: evaluation.evaluation_readiness,
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

function readinessGlanceLabel(comparison: RetrievalRunComparison): string {
  const beforeStatus = humanize(
    comparison.baselineSummary.qualitySummary?.status ?? "unknown",
  );
  const afterStatus = humanize(
    comparison.activeSummary.qualitySummary?.status ?? "unknown",
  );
  const statusLabel =
    beforeStatus === afterStatus ? afterStatus : `${beforeStatus} -> ${afterStatus}`;
  const scoreLabel =
    comparison.qualityScoreDelta === null
      ? "score n/a"
      : formatSignedDelta(comparison.qualityScoreDelta);

  return `${statusLabel} / ${scoreLabel}`;
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

function formatShortSignature(signature: string): string {
  const digest = signature.includes(":") ? signature.split(":").pop() ?? signature : signature;
  return `sig ${digest.slice(0, 10)}`;
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
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
