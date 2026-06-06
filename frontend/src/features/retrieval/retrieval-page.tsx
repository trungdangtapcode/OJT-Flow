import * as React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clipboard,
  ExternalLink,
  FileSearch,
  Gauge,
  ListFilter,
  Loader2,
  RefreshCw,
  Search,
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
import {
  EvidenceUseGuidancePanel,
  EvidenceUsabilitySummaryPanel,
  HitMatchExplanationPanel,
} from "./components/evidence-interpretation-guidance";
import { EvidenceReadinessPanel } from "./components/evidence-readiness-panel";
import {
  EvidenceProvenanceSummary,
  SnippetBlock,
  type EvidenceProvenanceEntryView,
} from "./components/evidence-provenance-snippet";
import {
  EvidenceSupportMatrix,
  type EvidenceSupportMatrixRowView,
} from "./components/evidence-support-matrix";
import { RetrievalFirstRunGuide } from "./components/first-run-guide";
import {
  HitEvidenceAuditStrip,
  type HitEvidenceAuditSummary,
} from "./components/hit-evidence-audit-strip";
import {
  ConceptMatchExplanation,
  DiversitySelectionExplanation,
  QueryAspectMatchExplanation,
  ScoreExplanation,
  ScoreMeter,
} from "./components/hit-explanation-panels";
import { RelevanceJudgmentSummary } from "./components/judgment-evaluation-panels";
import { NoResultRemediationPanel } from "./components/no-result-remediation-panel";
import {
  QualitySignalList,
  qualitySignalBadgeVariant,
} from "./components/quality-signal-list";
import { RankedEvidenceTriage } from "./components/ranked-evidence-triage";
import { RelevanceJudgmentControl } from "./components/relevance-judgment-control";
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
  CockpitMetricCard,
  QueryHealthPanel,
  SearchReadinessChecklist,
  type QueryHealthItem,
  type SearchReadinessChecklistItem,
} from "./components/search-cockpit-panels";
import type {
  FilterSuggestionStack,
  QueryAspectStack,
  SearchHintStack,
} from "./components/search-plan-detail-panels";
import {
  SearchPlanPreview,
  type SearchPlanPreviewView,
} from "./components/search-plan-preview";
import {
  type SearchPlanCoverageSummaryView,
} from "./components/search-plan-summary-panels";
import { SearchPresetStrip } from "./components/search-preset-strip";
import { SearchRunHistory } from "./components/search-run-history";
import { SectionHelpText } from "./components/section-help-text";
import { SourceInventoryPanel } from "./components/source-inventory-panel";
import {
  SourceDiversityPanel,
  type DiversitySelectionStack,
  type DiversityStack,
} from "./components/source-diversity-panel";
import { SourceScopePicker } from "./components/source-scope-picker";
import {
  StandardSearchPlanPanel,
  StrategyRecommendationsPanel,
} from "./components/strategy-standard-panels";
import { SubmittedSearchSummary } from "./components/submitted-search-summary";
import { TokenList } from "./components/token-list";
import { searchRunRemediationSummary } from "./model/search-run-presentation";
import type {
  Evidence,
  RetrievalEvidenceBucket,
  RetrievalGraphContext,
  RetrievalHit,
  RetrievalInterpretation,
  RetrievalIntegrityReport,
  RetrievalPackage,
  RetrievalPlan,
  RetrievalCoverage,
  RetrievalJudgmentEvaluationResult,
  RetrievalQualitySummary,
  RetrievalQualitySignal,
  RetrievalQueryVariant,
  RetrievalRecommendedAction,
  RetrievalRelevanceJudgment,
  RetrievalRelevanceJudgmentSummary,
  RetrievalScoreComponent,
  RetrievalPlanRiskSignal,
  RetrievalSearchPayload,
  RetrievalSearchOption,
  RetrievalSearchPreset,
  RetrievalSearchTask,
  RetrievalPlanTaskSummary,
  RetrievalSource,
  RuntimeRetrievalRulePack,
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
  sourceId: string;
  topK: number;
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
  conceptGrounding: ConceptGroundingSummary[];
  correctiveActionSummary: CorrectiveActionSummary;
  coverage: RetrievalCoverageSummary[];
  diversity: DiversityStack;
  hitCount: number;
  qualitySummary: RetrievalQualitySummary | null;
  qualityWarningCount: number;
  queryAspects: QueryAspectSummary[];
  queryProfile: QueryProfileSummary | null;
  rulePackCount: number;
  rulePackFingerprint: string;
  serverSignature: string | null;
  remediationSummary: string | null;
  topSourceId: string | null;
  warningCount: number;
};
type CorrectiveActionSummary = {
  count: number;
  highestPriority: number | null;
  highestSeverity: string | null;
  topActionTitle: string | null;
  applyFilterCount: number;
  broadenQueryCount: number;
  actionTypeCounts: Record<string, number>;
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
type ConceptGroundingSummary = {
  code: string | null;
  conceptId: string;
  displayName: string;
  evidenceCount: number;
  standardSystem: string;
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
  conceptGroundingComparison: RetrievalConceptGroundingComparison;
  coverageComparison: RetrievalCoverageComparison;
  diagnosis: RetrievalComparisonDiagnosis[];
  facetComparisons: RetrievalFacetComparison[];
  hitDelta: number;
  metrics: RetrievalRunComparisonMetrics;
  queryAspectComparison: RetrievalQueryAspectComparison;
  qualityScoreDelta: number | null;
  qualitySummaryChanged: boolean;
  qualityWarningDelta: number;
  qualitySignalComparison: RetrievalQualitySignalComparison;
  queryProfileChanged: boolean;
  rankChanges: RetrievalRankChange[];
  removedEvidenceIds: string[];
  retainedEvidenceIds: string[];
  rulePackChanges: RetrievalRulePackChange[];
  rulePackChanged: boolean;
  sourceDiversityComparison: RetrievalSourceDiversityComparison;
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
type RetrievalComparisonRecommendedAction = {
  action: string;
  priority: number;
  reason: string;
  severity: "success" | "warning" | "destructive" | "muted";
  source: string;
};
type EvidenceSupportSummary = HitEvidenceAuditSummary;
type EvidenceSupportMatrixRow = EvidenceSupportMatrixRowView;
type EvidenceUseGuidance = {
  action: string;
  reasons: string[];
  status: EvidenceSupportMatrixRow["supportStatus"];
  title: string;
};
type EvidenceUsabilitySummary = {
  checks: string[];
  headline: string;
  limitation: string;
  recommendation: string;
  status: EvidenceSupportMatrixRow["supportStatus"];
};
type RetrievalComparisonRecommendedActionSummary = {
  action_count: number;
  badge_variant: "success" | "warning" | "destructive";
  highest_priority: number | null;
  highest_severity: "success" | "warning" | "destructive";
  source_count: number;
  source_counts: Record<string, number>;
  sources: string[];
};
type RetrievalComparisonOperatorSummary = {
  bullets: string[];
  headline: string;
  reviewFocus: string[];
  status: "stable" | "review" | "improved";
};
type RetrievalQueryAspectComparison = {
  added: QueryAspectSummary[];
  removed: QueryAspectSummary[];
  retained: QueryAspectSummary[];
};
type RetrievalConceptGroundingComparison = {
  added: ConceptGroundingSummary[];
  removed: ConceptGroundingSummary[];
  retained: ConceptGroundingSummary[];
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
  field: FacetFilterField;
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
type RetrievalSourceDiversityComparison = {
  active: DiversityStack;
  activeSelectedSourceIds: string[];
  addedSourceIds: string[];
  baseline: DiversityStack;
  baselineSelectedSourceIds: string[];
  candidateSourceDelta: number;
  duplicateSelectedSourceDelta: number;
  lambdaChanged: boolean;
  removedSourceIds: string[];
  retainedSourceIds: string[];
  selectedSourceDelta: number;
  selectionModeChanged: boolean;
  sourceOverlapRatio: number;
};
type RetrievalRankChange = {
  evidenceId: string;
  fromRank: number;
  rankDelta: number;
  toRank: number;
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
    return baselineRun ? compareSearchRuns(activeRun, baselineRun) : null;
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
          isSearchPending={isSearchPending}
          onClearAllFilters={onClearAllFilters}
          onClearFilter={onClearFilter}
          onApplyFilter={onApplyFacet}
          packageData={packageData}
          submittedSearchPayload={submittedSearchPayload}
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
          rows={evidenceSupportMatrixRows(packageData, relevanceJudgments, runId)}
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

function searchAnswerFallbackRemediation(packageData: RetrievalPackage): string {
  const topAction = packageData.recommended_actions?.[0];
  if (topAction) return `${topAction.title}: ${topAction.description}`;
  const qualityAction = packageData.quality_summary?.top_action;
  if (qualityAction) return qualityAction;
  if (!packageData.hits.length) return "Broaden search scope or inspect source inventory.";
  return "Review the top evidence hit, readiness score, and source provenance before using this package.";
}

function retrievalSearchPlanPreviewReport(
  packageData: RetrievalPackage | undefined,
  submittedSearchPayload: RetrievalSearchPayload | null,
  planData: RetrievalPlan | undefined,
) {
  const analysis = packageData
    ? queryAnalysisFromPackage(packageData)
    : queryAnalysisFromPlan(planData!);
  return {
    report_type: "retrieval_search_plan_preview",
    version: 1,
    generated_at: new Date().toISOString(),
    submitted_payload: submittedSearchPayload,
    plan_query: planData?.query ?? null,
    search_signature:
      packageData ? serverSearchSignatureFromPackage(packageData) : planData?.search_signature ?? null,
    route: {
      strategy: packageData?.trace.strategy ?? analysis.strategy,
      profile: analysis.queryProfile,
      quality_summary: packageData?.quality_summary ?? null,
    },
    query_planning: {
      detected_concepts: analysis.detectedConcepts,
      standards: analysis.standards,
      rule_ids: analysis.ruleIds,
      aspects: analysis.queryAspects,
      retrieval_tasks: analysis.retrievalTasks,
      coverage_summary: searchPlanCoverageSummary(analysis),
      task_summary: searchPlanTaskSummary(analysis),
      risk_signals: searchPlanRiskSignals(analysis),
      diagnostics: analysis.diagnostics,
      filter_suggestions: analysis.filterSuggestions,
      rewrites: packageData ? queryVariantsFromTrace(packageData.trace) : queryVariantsFromAnalysis(analysis),
    },
    medical_search_hints: analysis.searchHints,
    standard_search_plan: packageData ? retrievalStandardSearchPlanReport(packageData) : null,
    trace: {
      candidates_seen: packageData?.trace.candidates_seen ?? null,
      filters_applied: packageData?.trace.filters_applied ?? planData?.query.filters ?? {},
      warnings: packageData?.trace.warnings ?? [],
      safety_flags: packageData?.trace.safety_flags ?? [],
    },
  };
}

function retrievalInterpretationReport(packageData: RetrievalPackage) {
  const backendInterpretation = packageData.interpretation ?? null;
  if (backendInterpretation) {
    return {
      source: "backend",
      ...backendInterpretation,
    };
  }

  const topHit = packageData.hits[0] ?? null;
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingRequiredBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  return {
    source: "frontend_fallback",
    status: topHit
      ? missingRequiredBuckets.length
        ? "support_gaps"
        : "ready_to_review"
      : "no_ranked_evidence",
    summary: packageData.remediation_summary ?? searchAnswerFallbackRemediation(packageData),
    top_evidence_id: topHit?.evidence.evidence_id ?? null,
    top_source_id: topHit?.evidence.source_id ?? null,
    top_score_driver: optionalStringValue(topHit?.match_explanation?.top_score_driver) ?? null,
    support_status: optionalStringValue(topHit?.match_explanation?.support_status) ?? null,
    matched_terms: topHit?.matched_terms.slice(0, 6) ?? [],
    concept_labels: stringArrayValue(topHit?.match_explanation?.concept_labels).slice(0, 4),
    aspect_labels: stringArrayValue(topHit?.match_explanation?.aspect_labels).slice(0, 4),
    required_bucket_count: requiredBuckets.length,
    covered_required_bucket_count: requiredBuckets.length - missingRequiredBuckets.length,
    missing_required_buckets: missingRequiredBuckets.map((bucket) => bucket.label),
    warning_count:
      (packageData.trace.warnings?.length ?? 0) +
      (packageData.coverage?.warnings?.length ?? 0),
    next_action_title: packageData.recommended_actions?.[0]?.title ?? null,
    next_action_detail: packageData.recommended_actions?.[0]?.description ?? null,
    metadata: {
      compatibility_fallback: true,
    },
  };
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

function RetrievalSearchCockpit({
  isSearchPending,
  onClearAllFilters,
  onClearFilter,
  onApplyFilter,
  packageData,
  submittedSearchPayload,
}: {
  isSearchPending: boolean;
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
  onApplyFilter: (field: SupportedFilterField, value: string) => void;
  packageData: RetrievalPackage;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const copyKey = "retrieval-cockpit-report";
  const analysis = queryAnalysisFromPackage(packageData);
  const ranking = rankingStackFromPackage(packageData);
  const fusionDiagnostics = fusionDiagnosticsFromPackage(packageData);
  const diversity = diversityFromPackage(packageData);
  const qualitySummary = packageData.quality_summary ?? null;
  const correctiveSummary = packageData.recommended_action_summary ?? null;
  const topAction = (packageData.recommended_actions ?? [])[0] ?? null;
  const topFilterAction = topAction ? recommendedActionFilter(topAction) : null;
  const topBroadeningAction = topAction?.action_type === "broaden_query";
  const strategyRecommendations = packageData.strategy_recommendations ?? [];
  const standardSearchPlan = packageData.standard_search_plan ?? null;
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const coveredRequiredBuckets = requiredBuckets.filter((bucket) => bucket.hit_count > 0);
  const coverageSummaries = coverageSummariesFromPackage(packageData);
  const conceptGrounding = conceptGroundingSummariesFromPackage(packageData);
  const queryProfile = analysis.queryProfile;
  const strategy = packageData.trace.strategy;
  const activeFilters = submittedSearchPayload
    ? activeFilterEntries(activeFacetFiltersFromPayload(submittedSearchPayload))
    : [];
  const queryHealth = queryHealthItems(submittedSearchPayload, packageData);
  const readinessChecklist = searchReadinessChecklist({
    diversity,
    packageData,
    queryHealth,
    requiredBuckets,
    topAction,
  });
  const routeLabel = queryProfile
    ? `${queryProfile.label} / ${humanize(queryProfile.retrievalMode)}`
    : humanize(strategy);
  const reportCopied = copiedKey === copyKey;
  const copyReport = async () => {
    await copyTextToClipboard(
      JSON.stringify(
        retrievalCockpitReportFromPackage(packageData, submittedSearchPayload),
        null,
        2,
      ),
    );
    markCopied(copyKey);
  };

  return (
    <section
      aria-label="Retrieval cockpit"
      className="grid gap-3 rounded-md border border-border bg-muted/20 p-3"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Search cockpit
          </div>
          <div className="mt-1 break-words text-lg font-black leading-tight">
            {routeLabel}
          </div>
          <div className="mt-1 flex min-w-0 flex-wrap gap-1.5">
            <Badge variant="muted">{humanize(strategy)}</Badge>
            <Badge variant="muted">
              {formatCount(packageData.trace.candidates_seen, "candidate")}
            </Badge>
            <Badge variant="muted">{formatCount(packageData.hits.length, "hit")}</Badge>
            {ranking.framework.bm25Enabled !== null ? (
              <Badge variant={ranking.framework.bm25Enabled ? "success" : "muted"}>
                BM25 {ranking.framework.bm25Enabled ? "on" : "off"}
              </Badge>
            ) : null}
            <Badge variant={ranking.reranker.enabled ? "success" : "muted"}>
              rerank {ranking.reranker.enabled ? "on" : "off"}
            </Badge>
            {activeFilters.map((filter) => (
              <Badge key={filter.field} variant="muted">
                {filter.label}: {filter.displayValue}
              </Badge>
            ))}
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Button
            aria-label="Copy retrieval cockpit report"
            onClick={() => void copyReport()}
            size="sm"
            type="button"
            variant="outline"
          >
            {reportCopied ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}
            {reportCopied ? "Copied" : "Copy cockpit JSON"}
          </Button>
          <HelpTooltip label="Cockpit JSON report help">
            Copies the current retrieval package summary: submitted payload, route, ranking stack, readiness, evidence buckets, compact hits, actions, and rule-pack fingerprints.
          </HelpTooltip>
          {qualitySummary ? (
            <Badge variant={qualitySummaryBadgeVariant(qualitySummary)}>
              {humanize(qualitySummary.status)} {qualitySummary.score}/100
            </Badge>
          ) : null}
          <Badge
            variant={
              requiredBuckets.length && coveredRequiredBuckets.length < requiredBuckets.length
                ? "warning"
                : "success"
            }
          >
            {requiredBuckets.length
              ? `${coveredRequiredBuckets.length}/${requiredBuckets.length} required buckets`
              : "no required buckets"}
          </Badge>
          <Badge variant={coverageSummaries.length ? "warning" : "success"}>
            {coverageSummaries.length
              ? formatCount(coverageSummaries.length, "coverage gap")
              : "coverage ok"}
          </Badge>
        </div>
      </div>

      <QueryHealthPanel
        activeFilters={activeFilters}
        isSearchPending={isSearchPending}
        items={queryHealth}
        onClearAllFilters={onClearAllFilters}
        onClearSourceScope={() => onClearFilter("source_id")}
      />

      <SearchReadinessChecklist items={readinessChecklist} />

      <div className="grid gap-2 lg:grid-cols-5">
        <CockpitMetricCard
          helpText="The backend route chosen for this query, such as broad, structured, or safety-sensitive search. Use this to confirm the search behavior matches the question."
          label="Retrieval route"
          supporting={queryProfile ? humanize(queryProfile.route) : analysis.strategy}
          tone="info"
          value={queryProfile ? humanize(queryProfile.complexity) : "standard"}
        />
        <CockpitMetricCard
          helpText="The retrieval stack combines lexical search, vector search, and optional reranking. Stronger stacks usually improve recall and ordering, but still need evidence review."
          label="Hybrid stack"
          supporting={`${ranking.embedding.provider} / ${ranking.embedding.model}`}
          tone="success"
          value={hybridStackValue(ranking)}
        />
        <CockpitMetricCard
          helpText="Whether lexical and vector retrieval agree on the same top candidates. Low agreement means inspect query wording, filters, and reranking before trusting order."
          label="Fusion agreement"
          supporting={fusionDiagnostics.interpretation}
          tone={fusionDiagnostics.tone}
          value={fusionDiagnostics.label}
        />
        <CockpitMetricCard
          helpText="How many independent sources survived source-diversity selection. Low spread can mean the answer depends on one source family."
          label="Evidence spread"
          supporting={
            diversity.enabled
              ? `${formatCount(diversity.selectedSourceCount, "selected source")}`
              : "source diversity disabled"
          }
          tone={diversity.enabled ? "success" : "warning"}
          value={formatSourceCoverage(diversity)}
        />
        <CockpitMetricCard
          helpText="Concepts and query aspects detected from the search. Good grounding means the result matched the intended medical data concept, not just similar words."
          label="Grounding"
          supporting={formatCount(analysis.queryAspects.length, "query aspect")}
          tone={conceptGrounding.length ? "success" : "warning"}
          value={formatCount(conceptGrounding.length, "concept")}
        />
      </div>

      <StrategyRecommendationsPanel
        getSuggestedFilterAction={suggestedFilterAction}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        recommendations={strategyRecommendations}
      />

      <StandardSearchPlanPanel
        getSuggestedFilterAction={suggestedFilterAction}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        plan={standardSearchPlan}
      />

      <SourceDiversityPanel diversity={diversity} isSearchPending={isSearchPending} />

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.75fr)]">
        <div className="grid gap-2 rounded-md border border-border bg-card p-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Query transformation
            </div>
            <Badge variant="muted">
              {formatCount(analysis.variantCount, "variant")}
            </Badge>
          </div>
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {analysis.standards.slice(0, 8).map((standard) => (
              <Badge key={standard} variant="success">
                {standard}
              </Badge>
            ))}
            {analysis.detectedConcepts.slice(0, 8).map((concept) => (
              <Badge key={concept} variant="muted">
                {humanize(concept)}
              </Badge>
            ))}
            {analysis.expandedTerms.slice(0, 10).map((term) => (
              <span
                className="max-w-full break-words rounded-full border border-border bg-muted px-2.5 py-1 text-xs font-bold text-muted-foreground"
                key={term}
              >
                {term}
              </span>
            ))}
          </div>
          {analysis.queryAspects.length ? (
            <div className="grid gap-1.5">
              {analysis.queryAspects.slice(0, 3).map((aspect) => (
                <div
                  className="grid gap-1 rounded-md border border-border bg-muted/25 px-3 py-2 text-xs"
                  key={aspect.aspectId}
                >
                  <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                    <Badge variant="muted">P{aspect.priority}</Badge>
                    <span className="break-words font-black">{aspect.label}</span>
                  </div>
                  <div className="break-words text-muted-foreground">
                    {aspect.question}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div className="grid gap-2 rounded-md border border-border bg-card p-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Next best action
            </div>
            {correctiveSummary ? (
              <Badge variant={correctiveSummary.count ? "warning" : "success"}>
                {formatCount(correctiveSummary.count, "action")}
              </Badge>
            ) : null}
          </div>
          <div className="break-words text-sm font-black">
            {topAction?.title ?? qualitySummary?.top_action ?? "No corrective action required"}
          </div>
          <div className="break-words text-sm leading-6 text-muted-foreground">
            {topAction?.description ??
              "Review the ranked evidence, source provenance, and judgment metrics before using the package downstream."}
          </div>
          {topFilterAction ? (
            <Button
              disabled={isSearchPending}
              onClick={() => onApplyFilter(topFilterAction.field, topFilterAction.value)}
              size="sm"
              type="button"
              variant="outline"
            >
              <ListFilter className="h-4 w-4" />
              Apply {filterFieldLabel(topFilterAction.field)}
            </Button>
          ) : null}
          {topBroadeningAction ? (
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {activeFilters.some((filter) => filter.field === "source_id") ? (
                <Button
                  disabled={isSearchPending}
                  onClick={() => onClearFilter("source_id")}
                  size="sm"
                  title="Clear exact source scope and rerun search"
                  type="button"
                  variant="outline"
                >
                  <X className="h-4 w-4" />
                  Clear source scope
                </Button>
              ) : null}
              <Button
                disabled={isSearchPending || !activeFilters.length}
                onClick={onClearAllFilters}
                size="sm"
                title="Clear all active metadata filters and rerun search"
                type="button"
                variant="outline"
              >
                <ListFilter className="h-4 w-4" />
                Broaden search
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function hybridStackValue(ranking: RankingStack): string {
  const lexical = ranking.framework.bm25Enabled ? "BM25" : "FTS";
  const vector = ranking.embedding.provider === "deterministic" ? "hash" : "vector";
  const rerank = ranking.reranker.enabled ? "+ rerank" : "";
  return `${lexical} + ${vector} ${rerank}`.trim();
}

function fusionDiagnosticsFromPackage(packageData: RetrievalPackage): {
  interpretation: string;
  label: string;
  tone: "success" | "warning" | "info";
} {
  const diagnostics = recordValue(packageData.trace.fusion_diagnostics);
  const overlapRatio = numberValue(diagnostics.top_overlap_ratio);
  const rankDelta = numberValue(diagnostics.mean_selected_rank_delta);
  const interpretation = stringValue(diagnostics.interpretation, "fusion diagnostics unavailable");
  if (overlapRatio === null) {
    return {
      interpretation,
      label: "unreported",
      tone: "info",
    };
  }
  const rankDeltaText = rankDelta === null ? "rank delta unknown" : `delta ${formatDecimal(rankDelta)}`;
  return {
    interpretation: `${humanize(interpretation)} / ${rankDeltaText}`,
    label: formatPercent(overlapRatio),
    tone: overlapRatio >= 0.75 ? "success" : overlapRatio <= 0.25 ? "warning" : "info",
  };
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

function recommendedActionTypeCounts(
  actions: RetrievalRecommendedAction[],
): Record<string, number> {
  return actions.reduce<Record<string, number>>((counts, action) => {
    counts[action.action_type] = (counts[action.action_type] ?? 0) + 1;
    return counts;
  }, {});
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

function HitCard({
  diversitySelection,
  evidenceBuckets,
  hit,
  index,
  judgment,
  recommendedActions,
  onSetJudgment,
}: {
  diversitySelection: DiversitySelectionStack | null;
  evidenceBuckets: RetrievalEvidenceBucket[];
  hit: RetrievalHit;
  index: number;
  judgment: RelevanceJudgment | null;
  recommendedActions: RetrievalRecommendedAction[];
  onSetJudgment: (value: RelevanceJudgmentValue) => void;
}) {
  const evidence = hit.evidence;
  const aspectMatches = queryAspectMatchesFromHit(hit);
  const conceptMatches = conceptMatchesFromHit(hit);
  const provenanceEntries = provenanceEntriesFromEvidence(evidence);
  const rankingBoostSignals = rankingBoostSignalsFromHit(hit);
  const scoreComponents = scoreComponentsFromHit(hit);
  const supportSummary = evidenceSupportSummary(hit, provenanceEntries);
  const matchExplanation = hitMatchExplanation({
    aspectMatches,
    buckets: evidenceBuckets,
    conceptMatches,
    hit,
    provenanceEntries,
    rankingBoostSignals,
    scoreComponents,
  });
  const usabilitySummary = evidenceUsabilitySummary(
    supportSummary,
    matchExplanation,
    judgment,
  );
  const { copiedKey, markCopied } = useCopyFeedback();
  const evidenceCopyKey = `evidence-report-${evidence.source_id}-${index}`;
  const evidenceCopied = copiedKey === evidenceCopyKey;

  const copyEvidenceReport = async () => {
    await copyTextToClipboard(
      JSON.stringify(
        evidenceReportFromHit(
          hit,
          provenanceEntries,
          matchExplanation,
          judgment,
          recommendedActions,
        ),
        null,
        2,
      ),
    );
    markCopied(evidenceCopyKey);
  };
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
          <Button
            aria-label={`Copy evidence report for ${evidence.source_id}`}
            onClick={() => void copyEvidenceReport()}
            size="sm"
            type="button"
            variant="outline"
          >
            {evidenceCopied ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}
            {evidenceCopied ? "Copied" : "Copy evidence JSON"}
          </Button>
          <HelpTooltip label="Evidence JSON report help">
            Copies this evidence hit with identity, score details, provenance, match explanation, bucket support, locators, and snippet context.
          </HelpTooltip>
        </div>
      </div>

      {hit.snippet ? (
        <SnippetBlock formatClaim={formatClaim} snippet={hit.snippet} />
      ) : null}

      <p className="break-words text-sm leading-6 text-muted-foreground">
        {formatClaim(evidence.claim)}
      </p>

      <HitEvidenceAuditStrip formatCount={formatCount} summary={supportSummary} />

      <EvidenceUsabilitySummaryPanel summary={usabilitySummary} />

      <EvidenceUseGuidancePanel
        guidance={evidenceUseGuidance(supportSummary, matchExplanation, judgment)}
      />

      <HitMatchExplanationPanel explanation={matchExplanation} formatCount={formatCount} />

      <EvidenceProvenanceSummary
        entries={provenanceEntries}
        formatCount={formatCount}
      />

      <RelevanceJudgmentControl
        judgment={judgment}
        onSetJudgment={onSetJudgment}
      />

      <div className="grid gap-2 md:grid-cols-3">
        <ScoreMeter formatScore={formatScore} label="Lexical" value={hit.lexical_score} />
        <ScoreMeter formatScore={formatScore} label="Vector" value={hit.vector_score} />
        <ScoreMeter formatScore={formatScore} label="Rerank" value={hit.rerank_score} />
      </div>

      <ScoreExplanation components={scoreComponents} formatScore={formatScore} />

      <DiversitySelectionExplanation
        formatScore={formatScore}
        selection={diversitySelection}
      />

      <ConceptMatchExplanation matches={conceptMatches} />

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
  };
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

type QualityPolicyStack = {
  blockingSeverities: string[];
  conceptGroundingRequirements: {
    minConfidence: number | null;
    requireDetectedConcepts: boolean | null;
  };
  provenanceRequirements: {
    locatorAnyKeys: string[];
    requireSourceVersion: boolean | null;
    sourceTypes: string[];
  };
  rankingThresholds: Record<string, number>;
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
  queryVariantTexts: string[];
  queryVariants: RetrievalQueryVariant[];
  planCoverageSummary: SearchPlanCoverageStack | null;
  planRiskSignals: RetrievalPlanRiskSignal[];
  planTaskSummary: RetrievalPlanTaskSummary | null;
  retrievalTasks: RetrievalSearchTask[];
  ruleIds: string[];
  searchHints: SearchHintStack[];
  standards: string[];
  strategy: string;
  variantCount: number;
};

type SearchPlanCoverageStack = SearchPlanCoverageSummaryView;

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

type SearchHintParameterExample = {
  example: string;
  matchedDatasetField: boolean;
  name: string;
  targetField: string;
};

type SearchHintLineageFollowup = {
  parameter: string;
  purpose: string;
};

type QueryDiagnosticStack = {
  code: string;
  metadata: Record<string, unknown>;
  message: string;
  severity: string;
  suggestedAction: string;
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

type ConceptMatchSignal = {
  clinicalDomain: string | null;
  code: string | null;
  conceptId: string;
  confidence: number;
  displayName: string;
  matchedAliases: string[];
  matchedFields: string[];
  matchedTerms: string[];
  reason: string;
  standardSystem: string;
};
type EvidenceProvenanceEntry = EvidenceProvenanceEntryView;
type HitMatchExplanation = {
  aspectIds: string[];
  aspectLabels: string[];
  bucketIds: string[];
  bucketLabels: string[];
  conceptIds: string[];
  conceptLabels: string[];
  matchedTerms: string[];
  provenanceCount: number;
  provenanceFields: string[];
  rankingSignalCount: number;
  rankingSignalRuleIds: string[];
  supportStatus: EvidenceSupportMatrixRow["supportStatus"];
  topScoreComponent: {
    component: string;
    label: string;
    rank: number | null;
    value: number;
  } | null;
  topScoreDriver: string | null;
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
  return queryAnalysisStackFromRecord(queryAnalysis);
}

function queryAnalysisFromPlan(planData: RetrievalPlan): QueryAnalysisStack {
  return queryAnalysisStackFromRecord(
    recordValue(planData.query_analysis),
    planCoverageSummaryValue(planData.coverage_summary),
    planTaskSummaryValue(planData.task_summary),
    planRiskSignalsValue(planData.risk_signals),
  );
}

function queryAnalysisStackFromRecord(
  queryAnalysis: Record<string, unknown>,
  planCoverageSummary: SearchPlanCoverageStack | null = null,
  planTaskSummary: RetrievalPlanTaskSummary | null = null,
  planRiskSignals: RetrievalPlanRiskSignal[] = [],
): QueryAnalysisStack {
  return {
    conceptCandidates: conceptCandidatesValue(queryAnalysis.concept_candidates),
    detectedConcepts: stringArrayValue(queryAnalysis.detected_concepts),
    diagnostics: queryDiagnosticsValue(queryAnalysis.diagnostics),
    expandedTerms: stringArrayValue(queryAnalysis.expanded_terms),
    filterSuggestions: filterSuggestionsValue(queryAnalysis.filter_suggestions),
    queryAspects: queryAspectsValue(queryAnalysis.query_aspects),
    queryProfile: queryProfileValue(queryAnalysis.query_profile),
    queryVariantTexts: stringArrayValue(queryAnalysis.query_variants),
    queryVariants: queryVariantDetailsValue(queryAnalysis.query_variant_details),
    planCoverageSummary,
    planRiskSignals,
    planTaskSummary,
    retrievalTasks: retrievalTasksValue(queryAnalysis.retrieval_tasks),
    ruleIds: stringArrayValue(queryAnalysis.rule_ids),
    searchHints: searchHintsValue(queryAnalysis.search_hints),
    standards: stringArrayValue(queryAnalysis.standards),
    strategy: stringValue(queryAnalysis.strategy, "unknown"),
    variantCount: stringArrayValue(queryAnalysis.query_variants).length,
  };
}

function searchPlanCoverageSummary(analysis: QueryAnalysisStack): SearchPlanCoverageStack {
  if (analysis.planCoverageSummary) return analysis.planCoverageSummary;
  const localTasks = analysis.retrievalTasks.filter((task) => task.target === "local_corpus");
  const externalTasks = analysis.retrievalTasks.filter(
    (task) => task.target === "external_medical_index",
  );
  const standards = uniqueValues([
    ...analysis.standards,
    ...analysis.retrievalTasks.flatMap((task) => task.standards),
  ]);
  const filterKeys = new Set<string>();
  for (const suggestion of analysis.filterSuggestions) {
    filterKeys.add(`${suggestion.field}:${suggestion.value}`);
  }
  for (const task of analysis.retrievalTasks) {
    for (const [field, value] of Object.entries(task.suggested_filters)) {
      filterKeys.add(`${field}:${value}`);
    }
  }
  const warnings = uniqueValues([
    ...analysis.diagnostics
      .filter((diagnostic) => diagnostic.severity !== "info")
      .map((diagnostic) => diagnostic.code),
    ...analysis.retrievalTasks.flatMap((task) => task.warnings),
  ]);
  return {
    externalTaskCount: externalTasks.length,
    filterCount: filterKeys.size,
    localTaskCount: localTasks.length,
    ready: localTasks.some((task) => task.required) && standards.length > 0,
    requiredLocalTaskCount: localTasks.filter((task) => task.required).length,
    standards,
    nextAction: fallbackPlanCoverageNextAction({
      externalTaskCount: externalTasks.length,
      filterCount: filterKeys.size,
      ready: localTasks.some((task) => task.required) && standards.length > 0,
      requiredLocalTaskCount: localTasks.filter((task) => task.required).length,
      standardCount: standards.length,
    }),
    summary: `${localTasks.filter((task) => task.required).length}/${localTasks.length} required local task(s), ${externalTasks.length} external follow-up(s), ${standards.length} standard(s), and ${filterKeys.size} suggested filter(s).`,
    warnings,
  };
}

function searchPlanTaskSummary(analysis: QueryAnalysisStack): RetrievalPlanTaskSummary {
  if (analysis.planTaskSummary) return analysis.planTaskSummary;
  const runnableLocal = analysis.retrievalTasks.filter(
    (task) => task.target === "local_corpus" && task.action_type === "run_local_search",
  );
  const requiredRunnableLocal = runnableLocal.filter((task) => task.required);
  const externalOpen = analysis.retrievalTasks.filter(
    (task) => task.target === "external_medical_index" && task.action_type === "open_external_url",
  );
  const externalCopy = analysis.retrievalTasks.filter(
    (task) => task.target === "external_medical_index" && task.action_type === "copy_query",
  );
  const blockedTasks = analysis.retrievalTasks.filter(
    (task) => !["run_local_search", "open_external_url", "copy_query"].includes(task.action_type),
  );
  const manualFollowupCount = externalOpen.length + externalCopy.length;
  return {
    total_task_count: analysis.retrievalTasks.length,
    runnable_local_count: runnableLocal.length,
    required_runnable_local_count: requiredRunnableLocal.length,
    external_open_count: externalOpen.length,
    external_copy_count: externalCopy.length,
    manual_followup_count: manualFollowupCount,
    blocked_task_count: blockedTasks.length,
    primary_action: requiredRunnableLocal.length
      ? "Run required local search tasks first, then review external follow-ups."
      : runnableLocal.length
        ? "Run the local search task, then review external follow-ups."
        : manualFollowupCount
          ? "Review external medical search follow-ups before trusting the plan."
          : "Add a more specific healthcare query before executing retrieval.",
    summary: `${runnableLocal.length} local runnable task(s), ${manualFollowupCount} external/manual follow-up(s), and ${blockedTasks.length} blocked task(s).`,
  };
}

function planTaskSummaryValue(value: unknown): RetrievalPlanTaskSummary | null {
  const summary = recordValue(value);
  const rawSummary = optionalStringValue(summary.summary);
  if (!rawSummary) return null;
  return {
    total_task_count: numberValue(summary.total_task_count) ?? 0,
    runnable_local_count: numberValue(summary.runnable_local_count) ?? 0,
    required_runnable_local_count: numberValue(summary.required_runnable_local_count) ?? 0,
    external_open_count: numberValue(summary.external_open_count) ?? 0,
    external_copy_count: numberValue(summary.external_copy_count) ?? 0,
    manual_followup_count: numberValue(summary.manual_followup_count) ?? 0,
    blocked_task_count: numberValue(summary.blocked_task_count) ?? 0,
    primary_action: stringValue(
      summary.primary_action,
      "Review the plan, then run local evidence search.",
    ),
    summary: rawSummary,
  };
}

function planCoverageSummaryValue(value: unknown): SearchPlanCoverageStack | null {
  const summary = recordValue(value);
  const rawSummary = optionalStringValue(summary.summary);
  if (!rawSummary) return null;
  return {
    externalTaskCount: numberValue(summary.external_task_count) ?? 0,
    filterCount: numberValue(summary.filter_count) ?? 0,
    localTaskCount: numberValue(summary.local_task_count) ?? 0,
    ready: booleanValue(summary.ready),
    requiredLocalTaskCount: numberValue(summary.required_local_task_count) ?? 0,
    standards: stringArrayValue(summary.standards),
    nextAction: stringValue(summary.next_action, "Review the plan, then run local evidence search."),
    summary: rawSummary,
    warnings: stringArrayValue(summary.warnings),
  };
}

function fallbackPlanCoverageNextAction({
  externalTaskCount,
  filterCount,
  ready,
  requiredLocalTaskCount,
  standardCount,
}: {
  externalTaskCount: number;
  filterCount: number;
  ready: boolean;
  requiredLocalTaskCount: number;
  standardCount: number;
}): string {
  if (!ready && standardCount === 0) {
    return "Add a healthcare standard, schema, resource type, field list, or clinical domain.";
  }
  if (!ready && requiredLocalTaskCount === 0) {
    return "Refine the query until the plan has at least one required local corpus task.";
  }
  if (filterCount > 0) return "Review suggested filters, then run the local evidence search.";
  if (externalTaskCount > 0) {
    return "Run local evidence search, then inspect external follow-up tasks if coverage is incomplete.";
  }
  return "Run local evidence search.";
}

function searchPlanRiskSignals(analysis: QueryAnalysisStack): RetrievalPlanRiskSignal[] {
  if (analysis.planRiskSignals.length) return analysis.planRiskSignals;
  const coverage = searchPlanCoverageSummary(analysis);
  const signals: RetrievalPlanRiskSignal[] = [];
  if (!coverage.ready) {
    signals.push({
      code: "coverage_not_ready",
      message: "The plan needs more detail before review-grade search.",
      metadata: {
        local_task_count: coverage.localTaskCount,
        standard_count: coverage.standards.length,
      },
      severity: "warning",
      source: "frontend_compatibility_fallback",
      suggested_action:
        "Add a standard, field list, resource type, schema, or clinical domain before relying on the search.",
    });
  }
  signals.push(
    ...analysis.diagnostics
      .filter((diagnostic) => diagnostic.severity !== "info")
      .map((diagnostic) => ({
        code: `diagnostic_${diagnostic.code}`,
        message: diagnostic.message,
        metadata: diagnostic.metadata,
        severity: diagnostic.severity,
        source: "query_diagnostic",
        suggested_action: diagnostic.suggestedAction,
      })),
  );
  return signals.slice(0, 6);
}

function planRiskSignalsValue(value: unknown): RetrievalPlanRiskSignal[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      code: stringValue(item.code, ""),
      message: stringValue(item.message, "Plan risk signal unavailable."),
      metadata: recordValue(item.metadata),
      severity: stringValue(item.severity, "info"),
      source: stringValue(item.source, "plan"),
      suggested_action: stringValue(item.suggested_action, "Review this plan before running search."),
    }))
    .filter((item) => item.code);
}

function diversityFromPackage(packageData: RetrievalPackage): DiversityStack {
  const diversity = recordValue(packageData.diversity ?? packageData.handoff_context.diversity);
  return {
    candidateSourceCount: numberValue(diversity.candidate_source_count) ?? 0,
    duplicateSelectedSourceCount:
      numberValue(diversity.duplicate_selected_source_count) ?? 0,
    enabled: booleanValue(diversity.enabled),
    lambda: numberValue(diversity.lambda_value) ?? numberValue(diversity.lambda),
    selectedHits: diversitySelectionDetailsValue(diversity.selected_hits),
    selectedSourceCount: numberValue(diversity.selected_source_count) ?? 0,
    selectionMode: stringValue(diversity.selection_mode, "unknown"),
  };
}

function qualityPolicyFromPackage(packageData: RetrievalPackage): QualityPolicyStack {
  const policy = recordValue(packageData.handoff_context.quality_policy);
  const conceptGroundingRequirements = recordValue(
    policy.concept_grounding_requirements,
  );
  const provenanceRequirements = recordValue(policy.provenance_requirements);
  return {
    blockingSeverities: stringArrayValue(policy.blocking_severities),
    conceptGroundingRequirements: {
      minConfidence: numberValue(conceptGroundingRequirements.min_confidence),
      requireDetectedConcepts: optionalBooleanValue(
        conceptGroundingRequirements.require_detected_concepts,
      ),
    },
    provenanceRequirements: {
      locatorAnyKeys: stringArrayValue(provenanceRequirements.locator_any_keys),
      requireSourceVersion: optionalBooleanValue(
        provenanceRequirements.require_source_version,
      ),
      sourceTypes: stringArrayValue(provenanceRequirements.source_types),
    },
    rankingThresholds: numericRecordValue(policy.ranking_thresholds),
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
  const minTopMatchedTerms = policy.rankingThresholds.min_top_matched_terms;
  const thresholdText =
    policy.reviewScoreBelow === null ? "review threshold unknown" : `review < ${policy.reviewScoreBelow}`;
  const matchText =
    minTopMatchedTerms === undefined
      ? null
      : `top match >= ${minTopMatchedTerms}`;
  const conceptText =
    policy.conceptGroundingRequirements.requireDetectedConcepts === true
      ? `concepts >= ${(policy.conceptGroundingRequirements.minConfidence ?? 0).toFixed(2)}`
      : null;
  const provenanceText = policy.provenanceRequirements.sourceTypes.length
    ? `provenance ${policy.provenanceRequirements.sourceTypes.length} source types`
    : null;
  const penaltyText = [
    warningPenalty === undefined ? null : `warning -${warningPenalty}`,
    destructivePenalty === undefined ? null : `blocker -${destructivePenalty}`,
  ].filter(Boolean);
  return [policy.version, thresholdText, matchText, conceptText, provenanceText, ...penaltyText]
    .filter(Boolean)
    .join(" / ");
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

function queryVariantsFromAnalysis(analysis: QueryAnalysisStack): RetrievalQueryVariant[] {
  const variants = analysis.queryVariants;
  if (variants.length) return variants;
  return analysis.queryVariantTexts.map((variant) => ({
    metadata: {},
    reason: "Query variant from retrieval plan analysis.",
    source: "query_analysis",
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

function retrievalTasksValue(value: unknown): RetrievalSearchTask[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => {
      const target = stringValue(item.target, "local_corpus");
      const metadata = recordValue(item.metadata);
      return {
        action_type: retrievalTaskActionTypeValue(item.action_type, target, metadata),
        aspect_id: optionalStringValue(item.aspect_id),
        label: stringValue(item.label, "Retrieval task"),
        metadata,
        priority: numberValue(item.priority) ?? 100,
        query: stringValue(item.query, ""),
        query_variants: stringArrayValue(item.query_variants),
        rationale: stringValue(item.rationale, "Generated from query analysis."),
        required: booleanValue(item.required),
        search_hint_target: optionalStringValue(item.search_hint_target),
        standards: stringArrayValue(item.standards),
        suggested_filters: stringRecordValue(item.suggested_filters),
        target: target === "external_medical_index" ? "external_medical_index" : "local_corpus",
        task_id: stringValue(item.task_id, ""),
        warnings: stringArrayValue(item.warnings),
      } satisfies RetrievalSearchTask;
    })
    .filter((item) => item.task_id && item.query)
    .sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
}

function retrievalTaskActionTypeValue(
  value: unknown,
  target: string,
  metadata: Record<string, unknown>,
): RetrievalSearchTask["action_type"] {
  const action = stringValue(value, "");
  if (
    action === "run_local_search" ||
    action === "open_external_url" ||
    action === "copy_query"
  ) {
    return action;
  }
  if (target === "external_medical_index") {
    return optionalStringValue(metadata.url) ? "open_external_url" : "copy_query";
  }
  return "run_local_search";
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

function hitMatchExplanation({
  aspectMatches,
  buckets,
  conceptMatches,
  hit,
  provenanceEntries,
  rankingBoostSignals,
  scoreComponents,
}: {
  aspectMatches: QueryAspectMatchSignal[];
  buckets: RetrievalEvidenceBucket[];
  conceptMatches: ConceptMatchSignal[];
  hit: RetrievalHit;
  provenanceEntries: EvidenceProvenanceEntry[];
  rankingBoostSignals: RankingBoostSignal[];
  scoreComponents: RetrievalScoreComponent[];
}): HitMatchExplanation {
  const evidenceId = hit.evidence.evidence_id;
  const bucketLabels = buckets
    .filter((bucket) => bucket.evidence_ids.includes(evidenceId))
    .map((bucket) => bucket.label);
  const matchedBuckets = buckets.filter((bucket) => bucket.evidence_ids.includes(evidenceId));
  const topComponent = [...scoreComponents].sort(
    (left, right) => Math.abs(right.value) - Math.abs(left.value),
  )[0];
  const supportSummary = evidenceSupportSummary(hit, provenanceEntries);
  const backendExplanation = recordValue(hit.match_explanation);
  const backendTopComponent = recordValue(backendExplanation.top_score_component);
  return {
    aspectIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.aspect_ids).slice(0, 8),
      uniqueValues(aspectMatches.map((match) => match.aspectId)).slice(0, 8),
    ),
    aspectLabels: nonEmptyStringArray(
      stringArrayValue(backendExplanation.aspect_labels).slice(0, 4),
      uniqueValues(aspectMatches.map((match) => match.label)).slice(0, 4),
    ),
    bucketIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.bucket_ids).slice(0, 8),
      uniqueValues(matchedBuckets.map((bucket) => bucket.bucket_id)).slice(0, 8),
    ),
    bucketLabels: nonEmptyStringArray(
      stringArrayValue(backendExplanation.bucket_labels).slice(0, 4),
      uniqueValues(bucketLabels).slice(0, 4),
    ),
    conceptIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.concept_ids).slice(0, 8),
      uniqueValues(conceptMatches.map((match) => match.conceptId)).slice(0, 8),
    ),
    conceptLabels: nonEmptyStringArray(
      stringArrayValue(backendExplanation.concept_labels).slice(0, 4),
      uniqueValues(
        conceptMatches.map((match) =>
          match.code ? `${match.standardSystem} ${match.code}` : match.displayName,
        ),
      ).slice(0, 4),
    ),
    matchedTerms: nonEmptyStringArray(
      stringArrayValue(backendExplanation.matched_terms).slice(0, 6),
      uniqueValues(hit.matched_terms).slice(0, 6),
    ),
    provenanceCount:
      numberValue(backendExplanation.provenance_count) ?? provenanceEntries.length,
    provenanceFields: nonEmptyStringArray(
      stringArrayValue(backendExplanation.provenance_fields).slice(0, 12),
      uniqueValues(provenanceEntries.map((entry) => entry.label)).slice(0, 12),
    ),
    rankingSignalCount:
      numberValue(backendExplanation.ranking_signal_count) ?? rankingBoostSignals.length,
    rankingSignalRuleIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.ranking_signal_rule_ids).slice(0, 12),
      uniqueValues(rankingBoostSignals.map((signal) => signal.ruleId)).slice(0, 12),
    ),
    supportStatus:
      hitSupportStatusValue(backendExplanation.support_status) ??
      evidenceSupportStatus(supportSummary),
    topScoreComponent: backendTopComponent.component
      ? {
          component: stringValue(backendTopComponent.component, ""),
          label: stringValue(backendTopComponent.label, "Score component"),
          rank: numberValue(backendTopComponent.rank),
          value: numberValue(backendTopComponent.value) ?? 0,
        }
      : topComponent
      ? {
          component: topComponent.component,
          label: topComponent.label,
          rank: topComponent.rank ?? null,
          value: topComponent.value,
        }
      : null,
    topScoreDriver:
      optionalStringValue(backendExplanation.top_score_driver) ??
      (topComponent ? `${topComponent.label} ${formatSignedDelta(topComponent.value)}` : null),
  };
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

function conceptMatchesFromHit(hit: RetrievalHit): ConceptMatchSignal[] {
  const matches = hit.source_locator.concept_matches;
  if (!Array.isArray(matches)) return [];
  return matches
    .map((item) => recordValue(item))
    .map((item) => ({
      clinicalDomain: optionalStringValue(item.clinical_domain),
      code: optionalStringValue(item.code),
      conceptId: stringValue(item.concept_id, ""),
      confidence: numberValue(item.confidence) ?? 0,
      displayName: stringValue(item.display_name, "Medical concept"),
      matchedAliases: stringArrayValue(item.matched_aliases),
      matchedFields: stringArrayValue(item.matched_fields),
      matchedTerms: stringArrayValue(item.matched_terms),
      reason: stringValue(item.reason, "Evidence supports this detected concept."),
      standardSystem: stringValue(item.standard_system, "unknown"),
    }))
    .filter((item) => item.conceptId && item.standardSystem !== "unknown");
}

function provenanceEntriesFromEvidence(evidence: Evidence): EvidenceProvenanceEntry[] {
  const locator = evidence.locator;
  const entries: EvidenceProvenanceEntry[] = [];
  const sourceVersion = optionalStringValue(evidence.source_version);
  if (sourceVersion) entries.push({ href: null, label: "Version", value: sourceVersion });
  const locatorFields: Array<[string, string]> = [
    ["Standard", "standard"],
    ["System", "standard_system"],
    ["URL", "url"],
    ["Path", "path"],
    ["API", "api"],
    ["PMID", "pmid"],
    ["DOI", "doi"],
    ["Resource", "resource"],
    ["Table", "table"],
    ["Document", "document_id"],
    ["Chunk", "chunk_id"],
  ];
  for (const [label, key] of locatorFields) {
    const value = locatorSummaryValue(locator[key]);
    if (value) {
      entries.push({ href: provenanceHrefForLocator(key, value), label, value });
    }
  }
  return uniqueProvenanceEntries(entries).slice(0, 8);
}

function provenanceHrefForLocator(key: string, value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if ((key === "url" || key === "api") && /^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }
  if (key === "doi") return `https://doi.org/${encodeURIComponent(trimmed)}`;
  if (key === "pmid" && /^[0-9]+$/.test(trimmed)) {
    return `https://pubmed.ncbi.nlm.nih.gov/${trimmed}/`;
  }
  return null;
}

function locatorSummaryValue(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) return value.trim();
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (Array.isArray(value)) {
    const items = value
      .map(locatorSummaryValue)
      .filter((item): item is string => Boolean(item));
    return items.length ? items.slice(0, 3).join(", ") : null;
  }
  return null;
}

function uniqueProvenanceEntries(
  entries: EvidenceProvenanceEntry[],
): EvidenceProvenanceEntry[] {
  const seen = new Set<string>();
  return entries.filter((entry) => {
    const key = `${entry.label}:${entry.value}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function evidenceReportFromHit(
  hit: RetrievalHit,
  provenanceEntries: EvidenceProvenanceEntry[],
  matchExplanation: HitMatchExplanation,
  judgment: RelevanceJudgment | null = null,
  recommendedActions: RetrievalRecommendedAction[] = [],
) {
  const correctiveActions = correctiveActionReportContext(hit, recommendedActions);
  const supportSummary = evidenceSupportSummary(hit, provenanceEntries);
  return {
    report_type: "retrieval_evidence_hit",
    version: 1,
    generated_at: new Date().toISOString(),
    evidence: {
      evidence_id: hit.evidence.evidence_id,
      source_id: hit.evidence.source_id,
      source_type: hit.evidence.source_type,
      source_version: hit.evidence.source_version ?? null,
      trust_level: hit.evidence.trust_level,
      confidence: hit.evidence.confidence ?? null,
      claim: formatClaim(hit.evidence.claim),
    },
    support_summary: supportSummary,
    usability_summary: evidenceUsabilitySummary(
      supportSummary,
      matchExplanation,
      judgment,
    ),
    match_explanation: matchExplanation,
    ranking: {
      score: hit.score,
      lexical_score: hit.lexical_score,
      vector_score: hit.vector_score,
      rerank_score: hit.rerank_score,
      matched_terms: hit.matched_terms,
      score_components: scoreComponentsFromHit(hit),
      ranking_boosts: rankingBoostSignalsFromHit(hit),
    },
    grounding: {
      concept_matches: conceptMatchesFromHit(hit),
      query_aspect_matches: queryAspectMatchesFromHit(hit),
    },
    provenance: {
      summary: provenanceEntries,
      locator: hit.evidence.locator,
      source_locator: hit.source_locator,
    },
    corrective_actions: correctiveActions,
    snippet: hit.snippet,
  };
}

function correctiveActionReportContext(
  hit: RetrievalHit,
  actions: RetrievalRecommendedAction[],
) {
  return {
    related_to_evidence: actions
      .filter((action) => action.evidence_ids.includes(hit.evidence.evidence_id))
      .slice(0, 6)
      .map(correctiveActionReportItem),
    package_top_actions: actions.slice(0, 6).map(correctiveActionReportItem),
  };
}

function correctiveActionReportItem(action: RetrievalRecommendedAction) {
  return {
    action_id: action.action_id,
    priority: action.priority,
    severity: action.severity,
    action_type: action.action_type,
    title: action.title,
    description: action.description,
    suggested_filter: action.suggested_filter,
    source_signal_codes: action.source_signal_codes,
    evidence_ids: action.evidence_ids,
    metadata: action.metadata,
  };
}

function evidenceSupportSummary(
  hit: RetrievalHit,
  provenanceEntries: EvidenceProvenanceEntry[],
): EvidenceSupportSummary {
  return {
    aspect_count: queryAspectMatchesFromHit(hit).length,
    concept_count: conceptMatchesFromHit(hit).length,
    matched_term_count: hit.matched_terms.length,
    provenance_field_count: provenanceEntries.length,
    ranking_signal_count: rankingBoostSignalsFromHit(hit).length,
  };
}

function evidenceSupportMatrixRows(
  packageData: RetrievalPackage,
  relevanceJudgments: RelevanceJudgmentIndex,
  runId: string | null,
): EvidenceSupportMatrixRow[] {
  const bucketLabelsByEvidenceId = evidenceBucketLabelsByEvidenceId(
    packageData.evidence_buckets ?? [],
  );
  return packageData.hits.map((hit, index) => {
    const provenanceEntries = provenanceEntriesFromEvidence(hit.evidence);
    const summary = evidenceSupportSummary(hit, provenanceEntries);
    const judgment = runId
      ? relevanceJudgments[relevanceJudgmentKey(runId, hit.evidence.evidence_id)] ?? null
      : null;
    return {
      aspectCount: summary.aspect_count,
      bucketLabels: bucketLabelsByEvidenceId.get(hit.evidence.evidence_id) ?? [],
      conceptCount: summary.concept_count,
      confidenceLabel: formatConfidence(hit.evidence.confidence),
      evidenceId: hit.evidence.evidence_id,
      judgment,
      matchedTermCount: summary.matched_term_count,
      provenanceCount: summary.provenance_field_count,
      rank: index + 1,
      score: hit.score,
      sourceId: hit.evidence.source_id,
      sourceType: String(hit.evidence.source_type),
      standardSystem: optionalStringValue(hit.evidence.locator.standard_system),
      supportStatus: evidenceSupportStatus(summary),
    };
  });
}

function evidenceBucketLabelsByEvidenceId(
  buckets: RetrievalEvidenceBucket[],
): Map<string, string[]> {
  const labelsByEvidenceId = new Map<string, string[]>();
  for (const bucket of buckets) {
    for (const evidenceId of bucket.evidence_ids ?? []) {
      const labels = labelsByEvidenceId.get(evidenceId) ?? [];
      labels.push(bucket.label);
      labelsByEvidenceId.set(evidenceId, labels);
    }
  }
  return labelsByEvidenceId;
}

function evidenceSupportStatus(
  summary: EvidenceSupportSummary,
): EvidenceSupportMatrixRow["supportStatus"] {
  if (
    summary.matched_term_count > 0 &&
    summary.provenance_field_count > 0 &&
    (summary.concept_count > 0 || summary.aspect_count > 0)
  ) {
    return "strong";
  }
  if (summary.matched_term_count > 0 || summary.provenance_field_count > 0) {
    return "partial";
  }
  return "weak";
}

function evidenceUseGuidance(
  summary: EvidenceSupportSummary,
  explanation: HitMatchExplanation,
  judgment: RelevanceJudgment | null,
): EvidenceUseGuidance {
  const reasons = evidenceUseGuidanceReasons(summary, explanation, judgment);
  if (explanation.supportStatus === "strong" && judgment?.value !== "not_relevant") {
    return {
      action:
        "Good candidate for evidence review. Confirm the claim and provenance before using it in a workflow explanation.",
      reasons,
      status: "strong",
      title: "Use with provenance check",
    };
  }
  if (explanation.supportStatus === "partial") {
    return {
      action:
        "Needs review before use. It has some support, but missing grounding or traceability can make the explanation weak.",
      reasons,
      status: "partial",
      title: "Review before relying on it",
    };
  }
  return {
    action:
      "Treat as weak support. Broaden or adjust the query, inspect source scope, or mark the hit not relevant if it does not answer the submitted question.",
    reasons,
    status: "weak",
    title: "Weak evidence support",
  };
}

function evidenceUsabilitySummary(
  summary: EvidenceSupportSummary,
  explanation: HitMatchExplanation,
  judgment: RelevanceJudgment | null,
): EvidenceUsabilitySummary {
  const status = evidenceSupportStatus(summary);
  const guidance = evidenceUseGuidance(summary, explanation, judgment);
  const traceability =
    summary.provenance_field_count > 0
      ? `${formatCount(summary.provenance_field_count, "provenance field")}`
      : "missing provenance";
  const grounding =
    summary.concept_count > 0 || summary.aspect_count > 0
      ? `${formatCount(
          summary.concept_count + summary.aspect_count,
          "grounding signal",
        )}`
      : "missing medical grounding";
  const judgmentLabelText = judgment
    ? `operator judged ${judgmentLabel(judgment.value)}`
    : "not operator-judged";
  const headline =
    status === "strong"
      ? "This result has enough support signals for operator evidence review."
      : status === "partial"
        ? "This result has partial support and needs review before use."
        : "This result is weak support for the submitted search.";
  const limitation =
    status === "strong"
      ? "Still verify the claim text and source locator before using it in an explanation."
      : summary.provenance_field_count === 0
        ? "Traceability is limited because no provenance field is available."
        : "Medical grounding or exact query support is incomplete.";

  return {
    checks: [
      `${formatCount(summary.matched_term_count, "matched term")}`,
      traceability,
      grounding,
      judgmentLabelText,
      explanation.bucketLabels.length
        ? "evidence bucket matched"
        : "not in evidence bucket",
    ],
    headline,
    limitation,
    recommendation: guidance.action,
    status,
  };
}

function evidenceUseGuidanceReasons(
  summary: EvidenceSupportSummary,
  explanation: HitMatchExplanation,
  judgment: RelevanceJudgment | null,
): string[] {
  const reasons: string[] = [];
  if (summary.matched_term_count > 0) reasons.push("terms matched");
  else reasons.push("no exact terms");
  if (summary.provenance_field_count > 0) reasons.push("provenance present");
  else reasons.push("missing provenance");
  if (summary.concept_count > 0) reasons.push("concept grounded");
  if (summary.aspect_count > 0) reasons.push("query aspect supported");
  if (summary.concept_count === 0 && summary.aspect_count === 0) {
    reasons.push("missing medical grounding");
  }
  if (summary.ranking_signal_count > 0) reasons.push("ranking rule support");
  if (judgment) reasons.push(`judged ${judgmentLabel(judgment.value)}`);
  else reasons.push("unjudged");
  if (explanation.bucketLabels.length) reasons.push("evidence bucket matched");
  else reasons.push("not in evidence bucket");
  return reasons.slice(0, 8);
}

function supportStatusBadgeVariant(
  status: EvidenceSupportMatrixRow["supportStatus"],
): "success" | "warning" | "destructive" | "muted" {
  if (status === "strong") return "success";
  if (status === "partial") return "warning";
  return "destructive";
}

function hitSupportStatusValue(
  value: unknown,
): EvidenceSupportMatrixRow["supportStatus"] | null {
  return value === "strong" || value === "partial" || value === "weak" ? value : null;
}

function nonEmptyStringArray(values: string[], fallback: string[]): string[] {
  return values.length ? values : fallback;
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
      metadata: recordValue(item.metadata),
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
      metadata: recordValue(item.metadata),
      query: stringValue(item.query, ""),
      rationale: stringValue(item.rationale, "Generated from deterministic query analysis."),
      target: stringValue(item.target, "medical_search"),
      url: optionalStringValue(item.url),
      warnings: stringArrayValue(item.warnings),
    }))
    .filter((item) => item.query.length > 0 && item.target !== "medical_search");
}

function searchHintParameterExamples(value: unknown): SearchHintParameterExample[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      example: stringValue(item.example, ""),
      matchedDatasetField: Boolean(item.matched_dataset_field),
      name: stringValue(item.name, ""),
      targetField: stringValue(item.target_field, ""),
    }))
    .filter((item) => item.name && item.example);
}

function searchHintLineageFollowup(value: unknown): SearchHintLineageFollowup[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      parameter: stringValue(item.parameter, ""),
      purpose: stringValue(item.purpose, ""),
    }))
    .filter((item) => item.parameter && item.purpose);
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
    filters: {
      source_id: form.sourceId || null,
    },
    ...overrides,
  };
}

function plannedTaskSearchOverrides(task: RetrievalSearchTask): Partial<RetrievalSearchPayload> {
  const overrides: Partial<RetrievalSearchPayload> = {
    query: task.query,
  };
  for (const [field, value] of Object.entries(task.suggested_filters)) {
    if (!isSupportedFilterField(field)) continue;
    if (field === "source_id") {
      overrides.filters = { ...(overrides.filters ?? {}), source_id: value };
    } else {
      overrides[field] = value;
    }
  }
  return overrides;
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
    source_id: payload.filters?.source_id ?? null,
    filters: payload.filters ?? {},
  });
}

function serverSearchSignatureFromPackage(packageData: RetrievalPackage): string | null {
  return optionalStringValue(packageData.handoff_context.search_signature);
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

function comparisonRulePackChangeViews(rulePackChanges: RetrievalRulePackChange[]) {
  return rulePackChanges.map((change) => ({
    activeFingerprint: rulePackFingerprint(change.active),
    baselineFingerprint: rulePackFingerprint(change.baseline),
    name: change.name,
    status: change.status,
  }));
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
  const conceptGroundingComparison = conceptGroundingComparisonBetweenRuns(
    activeRun,
    baselineRun,
  );
  const queryAspectComparison = queryAspectComparisonBetweenRuns(activeRun, baselineRun);
  const sourceDiversityComparison = sourceDiversityComparisonBetweenRuns(
    activeRun,
    baselineRun,
  );
  const rulePackChanged = rulePackChanges.some((change) => change.status !== "stable");
  const topSourceChanged = activeRun.summary.topSourceId !== baselineRun.summary.topSourceId;
  const qualitySummaryChanged =
    qualitySummaryFingerprint(activeRun.summary.qualitySummary) !==
    qualitySummaryFingerprint(baselineRun.summary.qualitySummary);
  const qualityScoreDelta =
    activeRun.summary.qualitySummary && baselineRun.summary.qualitySummary
      ? activeRun.summary.qualitySummary.score - baselineRun.summary.qualitySummary.score
      : null;

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
    conceptGroundingComparison,
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
    qualityScoreDelta,
    qualitySummaryChanged,
    qualityWarningDelta:
      activeRun.summary.qualityWarningCount - baselineRun.summary.qualityWarningCount,
    qualitySignalComparison,
    queryProfileChanged,
    rankChanges,
    removedEvidenceIds,
    retainedEvidenceIds,
    rulePackChanges,
    rulePackChanged,
    sourceDiversityComparison,
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
  if (
    comparison.conceptGroundingComparison.added.length ||
    comparison.conceptGroundingComparison.removed.length
  ) {
    diagnosis.push({
      code: "concept_grounding_changed",
      message: "Controlled medical concept grounding changed between runs.",
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
  if (comparison.qualitySummaryChanged) {
    diagnosis.push({
      code: "quality_summary_changed",
      message: "Readiness status, score, or top action changed between runs.",
      severity: comparison.qualityScoreDelta !== null && comparison.qualityScoreDelta > 0
        ? "success"
        : "warning",
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
  if (
    comparison.sourceDiversityComparison.selectionModeChanged ||
    comparison.sourceDiversityComparison.lambdaChanged
  ) {
    diagnosis.push({
      code: "source_diversity_policy_changed",
      message: "Source-diversity selection mode or lambda changed between runs.",
      severity: "warning",
    });
  }
  if (comparison.sourceDiversityComparison.duplicateSelectedSourceDelta > 0) {
    diagnosis.push({
      code: "source_diversity_regressed",
      message: "The active run selected more duplicate evidence from already selected sources.",
      severity: "warning",
    });
  } else if (
    comparison.sourceDiversityComparison.selectedSourceDelta > 0 ||
    comparison.sourceDiversityComparison.duplicateSelectedSourceDelta < 0
  ) {
    diagnosis.push({
      code: "source_diversity_improved",
      message: "The active run improved selected-source coverage or reduced duplicate-source evidence.",
      severity: "success",
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
        "Comparison is stable across query profile, concept grounding, search aspects, rules, quality, facets, evidence, and ranks.",
      severity: "success",
    });
  }
  return diagnosis;
}

function comparisonReportFromComparison(
  comparison: RetrievalRunComparison,
  judgments: RelevanceJudgment[],
  recommendedActions: RetrievalComparisonRecommendedAction[] = comparisonReportRecommendedActions(
    comparison,
    judgments,
  ),
) {
  return {
    report_type: "retrieval_run_comparison",
    version: 1,
    generated_at: new Date().toISOString(),
    summary: comparisonReportSummary(comparison, judgments),
    operator_summary: comparisonOperatorSummary(comparison, recommendedActions),
    remediation: {
      active:
        comparison.activeSummary.remediationSummary ??
        searchRunRemediationSummary(comparison.activeSummary),
      baseline:
        comparison.baselineSummary.remediationSummary ??
        searchRunRemediationSummary(comparison.baselineSummary),
    },
    recommended_action_summary: comparisonRecommendedActionSummary(recommendedActions),
    recommended_actions: recommendedActions,
    active: {
      query: comparison.activeQuery,
      run_id: comparison.activeRunId,
      search_signature: comparison.activeSummary.serverSignature,
      submitted_at: comparison.activeSubmittedAt,
      payload: comparison.activePayload,
      remediation_summary:
        comparison.activeSummary.remediationSummary ??
        searchRunRemediationSummary(comparison.activeSummary),
      summary: comparison.activeSummary,
    },
    baseline: {
      query: comparison.baselineQuery,
      run_id: comparison.baselineRunId,
      search_signature: comparison.baselineSummary.serverSignature,
      submitted_at: comparison.baselineSubmittedAt,
      payload: comparison.baselinePayload,
      remediation_summary:
        comparison.baselineSummary.remediationSummary ??
        searchRunRemediationSummary(comparison.baselineSummary),
      summary: comparison.baselineSummary,
    },
    deltas: {
      candidates: comparison.candidateDelta,
      hits: comparison.hitDelta,
      quality_score: comparison.qualityScoreDelta,
      quality_warnings: comparison.qualityWarningDelta,
      source_diversity: {
        candidate_sources: comparison.sourceDiversityComparison.candidateSourceDelta,
        duplicate_selected_sources:
          comparison.sourceDiversityComparison.duplicateSelectedSourceDelta,
        selected_sources: comparison.sourceDiversityComparison.selectedSourceDelta,
      },
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
    concept_grounding: {
      added: comparison.conceptGroundingComparison.added,
      removed: comparison.conceptGroundingComparison.removed,
      retained: comparison.conceptGroundingComparison.retained,
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
    source_diversity: {
      active: {
        candidate_source_count:
          comparison.sourceDiversityComparison.active.candidateSourceCount,
        duplicate_selected_source_count:
          comparison.sourceDiversityComparison.active.duplicateSelectedSourceCount,
        enabled: comparison.sourceDiversityComparison.active.enabled,
        lambda: comparison.sourceDiversityComparison.active.lambda,
        selected_source_count:
          comparison.sourceDiversityComparison.active.selectedSourceCount,
        selection_mode: comparison.sourceDiversityComparison.active.selectionMode,
        selected_source_ids:
          comparison.sourceDiversityComparison.activeSelectedSourceIds,
      },
      baseline: {
        candidate_source_count:
          comparison.sourceDiversityComparison.baseline.candidateSourceCount,
        duplicate_selected_source_count:
          comparison.sourceDiversityComparison.baseline.duplicateSelectedSourceCount,
        enabled: comparison.sourceDiversityComparison.baseline.enabled,
        lambda: comparison.sourceDiversityComparison.baseline.lambda,
        selected_source_count:
          comparison.sourceDiversityComparison.baseline.selectedSourceCount,
        selection_mode: comparison.sourceDiversityComparison.baseline.selectionMode,
        selected_source_ids:
          comparison.sourceDiversityComparison.baselineSelectedSourceIds,
      },
      added_source_ids: comparison.sourceDiversityComparison.addedSourceIds,
      removed_source_ids: comparison.sourceDiversityComparison.removedSourceIds,
      retained_source_ids: comparison.sourceDiversityComparison.retainedSourceIds,
      source_overlap_ratio: comparison.sourceDiversityComparison.sourceOverlapRatio,
      selection_mode_changed:
        comparison.sourceDiversityComparison.selectionModeChanged,
      lambda_changed: comparison.sourceDiversityComparison.lambdaChanged,
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
    const scoreComponents = scoreComponentsFromHit(hit);
    const rankingBoostSignals = rankingBoostSignalsFromHit(hit);
    const conceptMatches = conceptMatchesFromHit(hit);
    const aspectMatches = queryAspectMatchesFromHit(hit);
    return {
      rank: index + 1,
      evidence_id: hit.evidence.evidence_id,
      source_id: hit.evidence.source_id,
      source_type: hit.evidence.source_type,
      trust_level: hit.evidence.trust_level,
      confidence: hit.evidence.confidence ?? null,
      score: hit.score,
      support_summary: evidenceSupportSummary(hit, provenanceEntries),
      match_explanation: hitMatchExplanation({
        aspectMatches,
        buckets,
        conceptMatches,
        hit,
        provenanceEntries,
        rankingBoostSignals,
        scoreComponents,
      }),
    };
  });
}

function retrievalStandardSearchPlanReport(packageData: RetrievalPackage) {
  const plan = packageData.standard_search_plan ?? null;
  if (!plan) {
    return null;
  }
  return {
    plan_id: plan.plan_id,
    summary: plan.summary,
    primary_route: plan.primary_route,
    missing_routes: plan.missing_routes,
    governance_notes: plan.governance_notes,
    steps: plan.steps.map((step) => ({
      step_id: step.step_id,
      label: step.label,
      standard_system: step.standard_system,
      route_type: step.route_type,
      priority: step.priority,
      query: step.query,
      rationale: step.rationale,
      suggested_filters: step.suggested_filters,
      governance_notes: step.governance_notes,
      metadata: step.metadata,
    })),
  };
}

function retrievalDiversityReport(packageData: RetrievalPackage) {
  const diversity = diversityFromPackage(packageData);
  return {
    enabled: diversity.enabled,
    selection_mode: diversity.selectionMode,
    candidate_source_count: diversity.candidateSourceCount,
    selected_source_count: diversity.selectedSourceCount,
    duplicate_selected_source_count: diversity.duplicateSelectedSourceCount,
    lambda: diversity.lambda,
    selected_hits: diversity.selectedHits.map((selection) => ({
      evidence_id: selection.evidenceId,
      source_id: selection.sourceId,
      selected_rank: selection.selectedRank,
      original_rank: selection.originalRank,
      relevance_score: selection.relevanceScore,
      redundancy_score: selection.redundancyScore,
      selection_score: selection.selectionScore,
      reason: selection.reason,
    })),
  };
}

function medicalSearchHintReport(packageData: RetrievalPackage) {
  const analysis = queryAnalysisFromPackage(packageData);
  if (!analysis.searchHints.length) {
    return [];
  }
  return analysis.searchHints.slice(0, 8).map((hint) => {
    const metadata = hint.metadata;
    return {
      target: hint.target,
      query: hint.query,
      url: hint.url,
      rationale: hint.rationale,
      warnings: hint.warnings,
      route_details: {
        endpoint_scope: stringArrayValue(metadata.scope_endpoints).slice(0, 8),
        selected_terms: stringArrayValue(metadata.selected_terms).slice(0, 8),
        selected_unit_candidates: stringArrayValue(
          metadata.selected_unit_candidates,
        ).slice(0, 8),
        parameter_examples: searchHintParameterExamples(
          metadata.parameter_examples,
        ).slice(0, 8),
        lineage_followup: searchHintLineageFollowup(
          metadata.lineage_followup,
        ).slice(0, 4),
        launchable: metadata.launchable === undefined ? Boolean(hint.url) : Boolean(metadata.launchable),
        capability_warning: optionalStringValue(metadata.capability_warning),
      },
    };
  });
}

function comparisonReportSummary(
  comparison: RetrievalRunComparison,
  judgments: RelevanceJudgment[],
) {
  return {
    active_query: comparison.activeQuery,
    baseline_query: comparison.baselineQuery,
    status: comparison.diagnosis.some((item) => item.severity === "warning")
      ? "changed"
      : "stable",
    top_diagnosis: comparison.diagnosis[0] ?? null,
    quality: {
      before_status: comparison.baselineSummary.qualitySummary?.status ?? null,
      after_status: comparison.activeSummary.qualitySummary?.status ?? null,
      before_score: comparison.baselineSummary.qualitySummary?.score ?? null,
      after_score: comparison.activeSummary.qualitySummary?.score ?? null,
      score_delta: comparison.qualityScoreDelta,
      before_top_action: comparison.baselineSummary.qualitySummary?.top_action ?? null,
      after_top_action: comparison.activeSummary.qualitySummary?.top_action ?? null,
      changed: comparison.qualitySummaryChanged,
    },
    evidence: {
      added_count: comparison.addedEvidenceIds.length,
      removed_count: comparison.removedEvidenceIds.length,
      retained_count: comparison.retainedEvidenceIds.length,
      rank_change_count: comparison.rankChanges.length,
      top_source_changed: comparison.topSourceChanged,
    },
    top_source: {
      before: comparison.topSourceBefore,
      after: comparison.topSourceAfter,
      changed: comparison.topSourceChanged,
    },
    retrieval: {
      hit_delta: comparison.hitDelta,
      candidate_delta: comparison.candidateDelta,
      warning_delta: comparison.warningDelta,
      quality_warning_delta: comparison.qualityWarningDelta,
      overlap_ratio: comparison.metrics.overlapRatio,
      churn_ratio: comparison.metrics.churnRate,
      source_diversity: {
        selected_source_delta:
          comparison.sourceDiversityComparison.selectedSourceDelta,
        duplicate_selected_source_delta:
          comparison.sourceDiversityComparison.duplicateSelectedSourceDelta,
        source_overlap_ratio:
          comparison.sourceDiversityComparison.sourceOverlapRatio,
      },
    },
    changed_dimensions: comparison.diagnosis
      .filter((item) => item.severity !== "success")
      .map((item) => item.code),
    judgment_count: judgments.length,
  };
}

function comparisonOperatorSummary(
  comparison: RetrievalRunComparison,
  recommendedActions: RetrievalComparisonRecommendedAction[],
): RetrievalComparisonOperatorSummary {
  const warnings = comparison.diagnosis.filter(
    (item) => item.severity === "warning",
  );
  const improvements = comparison.diagnosis.filter(
    (item) => item.severity === "success" && item.code !== "comparison_stable",
  );
  const diversity = comparison.sourceDiversityComparison;
  const status: RetrievalComparisonOperatorSummary["status"] = warnings.length
    ? "review"
    : improvements.length
      ? "improved"
      : "stable";
  const headline =
    status === "review"
      ? `Review ${formatCount(warnings.length, "change driver")} before accepting this retrieval tuning run.`
      : status === "improved"
        ? "Active run improved one or more retrieval readiness signals without warning drivers."
        : "Active run is stable against the selected baseline.";
  const topAction =
    recommendedActions.find((action) => action.severity !== "success") ??
    recommendedActions[0] ??
    null;
  const sourceSpread =
    diversity.selectedSourceDelta === 0 &&
    diversity.duplicateSelectedSourceDelta === 0
      ? "Source spread is unchanged."
      : `Source spread ${formatSignedDelta(
          diversity.selectedSourceDelta,
        )}; duplicate-source evidence ${formatSignedDelta(
          diversity.duplicateSelectedSourceDelta,
        )}.`;
  const bullets = [
    `Evidence overlap ${formatPercent(comparison.metrics.overlapRatio)}; churn ${formatPercent(comparison.metrics.churnRate)}.`,
    `Quality score delta ${
      comparison.qualityScoreDelta === null
        ? "n/a"
        : formatSignedDelta(comparison.qualityScoreDelta)
    }; quality warnings ${formatSignedDelta(comparison.qualityWarningDelta)}.`,
    sourceSpread,
    topAction
      ? `Next action: ${topAction.action}`
      : "No follow-up action detected.",
  ];
  const reviewFocus = uniqueValues([
    ...warnings.slice(0, 4).map((item) => humanize(item.code)),
    ...(diversity.duplicateSelectedSourceDelta > 0 ? ["source concentration"] : []),
    ...(comparison.metrics.churnRate > 0.5 ? ["evidence churn"] : []),
    ...(comparison.rankChanges.length ? ["rank movement"] : []),
    ...(comparison.qualitySummaryChanged ? ["quality readiness"] : []),
  ]);

  return {
    bullets,
    headline,
    reviewFocus: reviewFocus.length ? reviewFocus : ["no immediate review focus"],
    status,
  };
}

function comparisonReportRecommendedActions(
  comparison: RetrievalRunComparison,
  judgments: RelevanceJudgment[],
): RetrievalComparisonRecommendedAction[] {
  const actions: RetrievalComparisonRecommendedAction[] = [];
  const activeTopAction = comparison.activeSummary.qualitySummary?.top_action;
  if (activeTopAction) {
    actions.push({
      action: activeTopAction,
      priority: comparison.activeSummary.qualitySummary?.status === "blocked" ? 1 : 2,
      reason: "Active retrieval package readiness policy selected this top action.",
      severity:
        comparison.activeSummary.qualitySummary?.status === "blocked"
          ? "destructive"
          : "warning",
      source: "quality_summary.top_action",
    });
  }
  if (
    comparison.coverageComparison.regressed.length ||
    comparison.coverageComparison.added.length
  ) {
    actions.push({
      action: "Review coverage diagnostics and apply supported standard/aspect filters before accepting this run.",
      priority: 1,
      reason: "Coverage diagnostics were added or regressed between baseline and active runs.",
      severity: "warning",
      source: "coverage",
    });
  }
  if (comparison.queryProfileChanged) {
    actions.push({
      action: "Confirm the active query profile, route, and retrieval mode match the intended search task.",
      priority: 3,
      reason: "Adaptive query-profile guidance changed between runs.",
      severity: "warning",
      source: "query_profile",
    });
  }
  if (comparison.rulePackChanged) {
    actions.push({
      action: "Record the active rule-pack fingerprints with any relevance-tuning decision.",
      priority: 3,
      reason: "Rule-pack data changed, so ranking movement may not be caused only by query edits.",
      severity: "warning",
      source: "rule_packs",
    });
  }
  if (comparison.qualitySignalComparison.added.length) {
    actions.push({
      action: "Inspect newly added quality signals before using the active evidence package downstream.",
      priority: 1,
      reason: "The active run added package-level quality signals.",
      severity: "warning",
      source: "quality_signals",
    });
  }
  if (comparison.metrics.churnRate > 0.5 || comparison.topSourceChanged) {
    actions.push({
      action: "Compare added, removed, and retained evidence before treating the active run as equivalent to baseline.",
      priority: 2,
      reason: "Evidence churn or top-source movement is high enough to affect review conclusions.",
      severity: "warning",
      source: "evidence",
    });
  }
  if (comparison.sourceDiversityComparison.duplicateSelectedSourceDelta > 0) {
    actions.push({
      action: "Review whether active results over-concentrate evidence from the same source family before accepting the tuning change.",
      priority: 2,
      reason: "The active run selected more duplicate-source evidence than the baseline.",
      severity: "warning",
      source: "source_diversity",
    });
  }
  if (
    comparison.sourceDiversityComparison.selectionModeChanged ||
    comparison.sourceDiversityComparison.lambdaChanged
  ) {
    actions.push({
      action: "Document source-diversity policy changes with this comparison result.",
      priority: 3,
      reason: "Selection mode or lambda changed, so source spread is not directly comparable without configuration context.",
      severity: "warning",
      source: "source_diversity",
    });
  }
  if (!judgments.length) {
    actions.push({
      action: "Add explicit relevance judgments for top hits before using this comparison as an evaluation record.",
      priority: 4,
      reason: "The copied comparison does not include any operator judgments.",
      severity: "muted",
      source: "judgments",
    });
  }
  if (!actions.length) {
    actions.push({
      action: "Keep the active retrieval configuration; no comparison follow-up was detected.",
      priority: 5,
      reason: "Comparison diagnostics are stable and no missing review signal was detected.",
      severity: "success",
      source: "comparison_stable",
    });
  }
  return actions.sort(
    (left, right) =>
      left.priority - right.priority || left.source.localeCompare(right.source),
  );
}

function comparisonRecommendedActionSummary(
  actions: RetrievalComparisonRecommendedAction[],
): RetrievalComparisonRecommendedActionSummary {
  const sources = new Set(actions.map((action) => action.source));
  const sourceCounts = actions.reduce<Record<string, number>>((counts, action) => {
    counts[action.source] = (counts[action.source] ?? 0) + 1;
    return counts;
  }, {});
  const highestPriority = Math.min(...actions.map((action) => action.priority));
  const hasDestructive = actions.some((action) => action.severity === "destructive");
  const hasWarning = actions.some((action) => action.severity === "warning");
  return {
    action_count: actions.length,
    badge_variant: hasDestructive ? "destructive" : hasWarning ? "warning" : "success",
    highest_priority: Number.isFinite(highestPriority) ? highestPriority : null,
    highest_severity: hasDestructive ? "destructive" : hasWarning ? "warning" : "success",
    source_count: sources.size,
    source_counts: sourceCounts,
    sources: Array.from(sources).sort(),
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

function conceptGroundingSummariesFromPackage(
  packageData: RetrievalPackage,
): ConceptGroundingSummary[] {
  const counts = new Map<string, ConceptGroundingSummary>();
  for (const hit of packageData.hits) {
    for (const concept of conceptMatchesFromHit(hit)) {
      const key = conceptGroundingKey(concept);
      const current = counts.get(key);
      if (current) {
        current.evidenceCount += 1;
      } else {
        counts.set(key, {
          code: concept.code,
          conceptId: concept.conceptId,
          displayName: concept.displayName,
          evidenceCount: 1,
          standardSystem: concept.standardSystem,
        });
      }
    }
  }
  return [...counts.values()].sort(
    (left, right) =>
      left.standardSystem.localeCompare(right.standardSystem) ||
      left.displayName.localeCompare(right.displayName),
  );
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

function sourceDiversityComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalSourceDiversityComparison {
  const active = activeRun.summary.diversity;
  const baseline = baselineRun.summary.diversity;
  const activeSelectedSourceIds = diversitySelectedSourceIds(active);
  const baselineSelectedSourceIds = diversitySelectedSourceIds(baseline);
  const activeSourceSet = new Set(activeSelectedSourceIds);
  const baselineSourceSet = new Set(baselineSelectedSourceIds);
  const addedSourceIds = activeSelectedSourceIds.filter(
    (sourceId) => !baselineSourceSet.has(sourceId),
  );
  const removedSourceIds = baselineSelectedSourceIds.filter(
    (sourceId) => !activeSourceSet.has(sourceId),
  );
  const retainedSourceIds = activeSelectedSourceIds.filter((sourceId) =>
    baselineSourceSet.has(sourceId),
  );
  const unionCount = Math.max(
    0,
    activeSelectedSourceIds.length + baselineSelectedSourceIds.length - retainedSourceIds.length,
  );

  return {
    active,
    activeSelectedSourceIds,
    addedSourceIds,
    baseline,
    baselineSelectedSourceIds,
    candidateSourceDelta: active.candidateSourceCount - baseline.candidateSourceCount,
    duplicateSelectedSourceDelta:
      active.duplicateSelectedSourceCount - baseline.duplicateSelectedSourceCount,
    lambdaChanged: active.lambda !== baseline.lambda,
    removedSourceIds,
    retainedSourceIds,
    selectedSourceDelta: active.selectedSourceCount - baseline.selectedSourceCount,
    selectionModeChanged: active.selectionMode !== baseline.selectionMode,
    sourceOverlapRatio: unionCount ? retainedSourceIds.length / unionCount : 1,
  };
}

function diversitySelectedSourceIds(diversity: DiversityStack): string[] {
  return uniqueValues(diversity.selectedHits.map((selection) => selection.sourceId));
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
  return facetFilterFields.map((field) => {
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
  field: FacetFilterField,
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

function conceptGroundingComparisonBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
): RetrievalConceptGroundingComparison {
  const activeConcepts = activeRun.summary.conceptGrounding;
  const baselineConcepts = baselineRun.summary.conceptGrounding;
  const activeByKey = new Map(
    activeConcepts.map((concept) => [conceptGroundingKey(concept), concept]),
  );
  const baselineByKey = new Map(
    baselineConcepts.map((concept) => [conceptGroundingKey(concept), concept]),
  );
  return {
    added: activeConcepts.filter(
      (concept) => !baselineByKey.has(conceptGroundingKey(concept)),
    ),
    removed: baselineConcepts.filter(
      (concept) => !activeByKey.has(conceptGroundingKey(concept)),
    ),
    retained: activeConcepts.filter((concept) =>
      baselineByKey.has(conceptGroundingKey(concept)),
    ),
  };
}

function conceptGroundingKey(
  concept: Pick<ConceptGroundingSummary, "code" | "conceptId" | "standardSystem">,
): string {
  return `${concept.standardSystem}:${concept.code ?? ""}:${concept.conceptId}`;
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

function qualitySummaryFingerprint(summary: RetrievalQualitySummary | null): string {
  if (!summary) return "none";
  return [
    summary.status,
    summary.score,
    summary.top_action,
    summary.blocker_codes.join(","),
    summary.warning_codes.join(","),
  ].join("|");
}

function retrievalRunSummary(packageData: RetrievalPackage): RetrievalRunSummary {
  const rulePacks = retrievalRulePacksFromPackage(packageData);
  return {
    candidateCount: packageData.trace.candidates_seen,
    conceptGrounding: conceptGroundingSummariesFromPackage(packageData),
    correctiveActionSummary: correctiveActionSummaryFromPackage(packageData),
    coverage: coverageSummariesFromPackage(packageData),
    diversity: diversityFromPackage(packageData),
    hitCount: packageData.hits.length,
    qualitySummary: packageData.quality_summary ?? null,
    qualityWarningCount: qualityWarningCount(packageData.quality_signals ?? []),
    queryAspects: queryAspectSummariesFromPackage(packageData),
    queryProfile: queryProfileSummaryFromPackage(packageData),
    rulePackCount: rulePacks.length,
    rulePackFingerprint: rulePacks
      .map((pack) => `${pack.name}:${rulePackFingerprint(pack)}`)
      .join("|"),
    serverSignature: serverSearchSignatureFromPackage(packageData),
    remediationSummary:
      packageData.remediation_summary ??
      optionalStringValue(packageData.handoff_context.remediation_summary) ??
      null,
    topSourceId: packageData.hits[0]?.evidence.source_id ?? null,
    warningCount: packageData.trace.warnings.length,
  };
}

function correctiveActionSummaryFromPackage(
  packageData: RetrievalPackage,
): CorrectiveActionSummary {
  const backendSummary = packageData.recommended_action_summary;
  if (backendSummary) {
    const actionTypeCounts = backendSummary.action_type_counts ?? {
      apply_filter: backendSummary.apply_filter_count,
      broaden_query: backendSummary.broaden_query_count ?? 0,
    };
    return {
      count: backendSummary.count,
      highestPriority: backendSummary.highest_priority ?? null,
      highestSeverity: backendSummary.highest_severity ?? null,
      topActionTitle: backendSummary.top_action_title ?? null,
      applyFilterCount: backendSummary.apply_filter_count,
      broadenQueryCount: backendSummary.broaden_query_count ?? actionTypeCounts.broaden_query ?? 0,
      actionTypeCounts,
    };
  }
  const actions = packageData.recommended_actions ?? [];
  const topAction = actions[0] ?? null;
  const actionTypeCounts = recommendedActionTypeCounts(actions);
  return {
    count: actions.length,
    highestPriority: topAction?.priority ?? null,
    highestSeverity: topAction?.severity ?? null,
    topActionTitle: topAction?.title ?? null,
    applyFilterCount: actionTypeCounts.apply_filter ?? 0,
    broadenQueryCount: actionTypeCounts.broaden_query ?? 0,
    actionTypeCounts,
  };
}

function qualityWarningCount(signals: RetrievalQualitySignal[]): number {
  return signals.filter((signal) =>
    ["destructive", "error", "warning"].includes(signal.severity),
  ).length;
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
