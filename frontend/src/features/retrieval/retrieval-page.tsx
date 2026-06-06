import * as React from "react";
import { Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  Clipboard,
  Database,
  ExternalLink,
  FileSearch,
  Gauge,
  GitCompareArrows,
  History,
  HelpCircle,
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
import { HelpTooltip } from "../../components/ui/help-tooltip";
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
  RetrievalEvidenceBucket,
  RetrievalFacetBucket,
  RetrievalGraphContext,
  RetrievalHit,
  RetrievalInterpretation,
  RetrievalIntegrityReport,
  RetrievalPackage,
  RetrievalCoverage,
  RetrievalFacets,
  RetrievalJudgmentEvaluationResult,
  RetrievalQualitySummary,
  RetrievalQualitySignal,
  RetrievalQueryVariant,
  RetrievalRecommendedAction,
  RetrievalRelevanceJudgment,
  RetrievalRelevanceJudgmentSummary,
  RetrievalScoreComponent,
  RetrievalSearchPayload,
  RetrievalSearchOption,
  RetrievalSearchPreset,
  RetrievalSource,
  RetrievalStrategyRecommendation,
  RetrievalStandardSearchPlan,
  RetrievalStandardSearchStep,
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
type QueryHealthItem = {
  code: string;
  description: string;
  label: string;
  status: "ok" | "review" | "blocked" | "info";
};
type SearchReadinessChecklistItem = {
  code: string;
  detail: string;
  label: string;
  status: QueryHealthItem["status"];
};
type SourceInventoryReadiness = {
  chunkCount: number;
  domainCount: number;
  emptySourceCount: number;
  filteredCount: number;
  readiness: "ready" | "review" | "blocked";
  standardCount: number;
  sourceCount: number;
  sourceTypeCount: number;
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
type FacetSection = {
  field: FacetFilterField;
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
type EvidenceSupportSummary = {
  aspect_count: number;
  concept_count: number;
  matched_term_count: number;
  provenance_field_count: number;
  ranking_signal_count: number;
};
type EvidenceSupportMatrixRow = {
  aspectCount: number;
  bucketLabels: string[];
  conceptCount: number;
  confidenceLabel: string;
  evidenceId: string;
  judgment: RelevanceJudgment | null;
  matchedTermCount: number;
  provenanceCount: number;
  rank: number;
  score: number;
  sourceId: string;
  sourceType: string;
  standardSystem: string | null;
  supportStatus: "strong" | "partial" | "weak";
};
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
  const [sourceId, setSourceId] = React.useState("");
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
  const isSearchResultStale = Boolean(
    packageData &&
      submittedSearchSignature &&
      currentSearchSignature !== submittedSearchSignature,
  );

  const executeSearch = async (overrides: Partial<RetrievalSearchPayload> = {}) => {
    const payload = retrievalPayloadFromForm(formState, overrides);
    if (!payload.query) {
      setFormError("Enter a retrieval query before searching.");
      return;
    }
    setFormError(null);
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
    } else if (field === "source_id") {
      setSourceId(value);
      overrides.filters = { source_id: value };
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
            <TracePanel
              activeFilters={
                submittedSearchPayload
                  ? activeFilterEntries(activeFacetFiltersFromPayload(submittedSearchPayload))
                  : activeFilterEntries(activeFacetFilters)
              }
              isSearchPending={searchMutation.isPending}
              onApplyCoverageFilter={applySearchFilter}
              onClearAllFilters={clearAllSearchFilters}
              onClearFilter={clearSearchFilter}
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
          <SourcesPanel
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

function RetrievalInlineGuide() {
  return (
    <details className="rounded-md border border-border bg-muted/25 px-4 py-3">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2 text-sm font-black">
        <HelpCircle className="h-4 w-4 text-primary" />
        How to read Retrieval
        <Badge variant="muted">guide</Badge>
      </summary>
      <div className="mt-3 grid gap-3 text-sm leading-6 md:grid-cols-4">
        <RetrievalGuideItem title="1. Search cockpit">
          Shows the route, provider state, filters, and next best action for the current search.
        </RetrievalGuideItem>
        <RetrievalGuideItem title="2. Evidence readiness">
          Explains whether required support classes are present before trusting the package.
        </RetrievalGuideItem>
        <RetrievalGuideItem title="3. Strategy recommendations">
          Explains why hybrid search, reranking, corrective filters, or more evidence may be needed.
        </RetrievalGuideItem>
        <RetrievalGuideItem title="4. Ranked evidence">
          Inspect sources and match explanations. Evidence supports operations; it is not clinical advice.
        </RetrievalGuideItem>
      </div>
      <div className="mt-3">
        <Button asChild size="sm" type="button" variant="outline">
          <Link to="/help">
            <BookOpen className="h-4 w-4" />
            Open full manual
          </Link>
        </Button>
      </div>
    </details>
  );
}

function RetrievalGuideItem({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <div className="mt-1 text-muted-foreground">{children}</div>
    </div>
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
                  {run.summary.serverSignature ? (
                    <Badge variant="muted">
                      {formatShortSignature(run.summary.serverSignature)}
                    </Badge>
                  ) : null}
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
                  {run.summary.correctiveActionSummary.count ? (
                    <Badge variant="warning">
                      {formatCount(run.summary.correctiveActionSummary.count, "action")}
                    </Badge>
                  ) : null}
                  <CorrectiveActionTypeCountChips
                    counts={run.summary.correctiveActionSummary.actionTypeCounts}
                  />
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
                {run.summary.correctiveActionSummary.topActionTitle ? (
                  <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
                    Top action: {run.summary.correctiveActionSummary.topActionTitle}
                    {run.summary.correctiveActionSummary.highestPriority
                      ? ` / P${run.summary.correctiveActionSummary.highestPriority}`
                      : ""}
                  </span>
                ) : null}
                <SearchRunEvidenceSummary run={run} />
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

function CorrectiveActionTypeCountChips({
  counts,
}: {
  counts: Record<string, number>;
}) {
  const entries = correctiveActionTypeCountEntries(counts);
  if (!entries.length) return null;
  return (
    <>
      {entries.slice(0, 4).map(([actionType, count]) => (
        <Badge key={actionType} variant="muted">
          {humanize(actionType)} {count}
        </Badge>
      ))}
      {entries.length > 4 ? (
        <Badge variant="muted">+{entries.length - 4} action types</Badge>
      ) : null}
    </>
  );
}

function correctiveActionTypeCountEntries(
  counts: Record<string, number>,
): Array<[string, number]> {
  return Object.entries(counts)
    .filter(([, count]) => Number.isFinite(count) && count > 0)
    .sort(([leftType, leftCount], [rightType, rightCount]) => {
      if (rightCount !== leftCount) return rightCount - leftCount;
      return leftType.localeCompare(rightType);
    });
}

function EvidencePackBuckets({
  buckets,
}: {
  buckets: RetrievalEvidenceBucket[];
}) {
  if (!buckets.length) return null;
  const availableCount = buckets.filter((bucket) => bucket.hit_count > 0).length;
  const missingRequiredCount = buckets.filter(
    (bucket) => bucket.required && bucket.hit_count === 0,
  ).length;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-xs font-bold uppercase text-muted-foreground">
            Evidence pack
          </div>
          <div className="mt-1 text-sm font-semibold">
            {formatCount(availableCount, "bucket")} with selected evidence
          </div>
        </div>
        <Badge variant={missingRequiredCount ? "warning" : "success"}>
          {missingRequiredCount
            ? formatCount(missingRequiredCount, "required gap")
            : "complete"}
        </Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
        {buckets.map((bucket) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2 text-xs"
            key={bucket.bucket_id}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{bucket.label}</span>
              <Badge variant={evidenceBucketBadgeVariant(bucket)}>
                {formatCount(bucket.hit_count, "hit")}
              </Badge>
            </div>
            <div className="break-words text-muted-foreground">
              {bucket.description}
            </div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {bucket.required ? <Badge variant="muted">required</Badge> : null}
              {bucket.source_ids.slice(0, 3).map((sourceId) => (
                <Badge className="max-w-full break-words" key={sourceId} variant="muted">
                  {sourceId}
                </Badge>
              ))}
              {bucket.source_ids.length > 3 ? (
                <Badge variant="muted">+{bucket.source_ids.length - 3}</Badge>
              ) : null}
              {bucket.warnings.map((warning) => (
                <Badge className="max-w-full break-words" key={warning} variant="warning">
                  {humanize(warning)}
                </Badge>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function evidenceBucketBadgeVariant(
  bucket: RetrievalEvidenceBucket,
): "success" | "warning" | "muted" {
  if (bucket.hit_count > 0) return "success";
  return bucket.required ? "warning" : "muted";
}

function qualitySummaryBadgeVariant(
  summary: RetrievalQualitySummary,
): "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
}

function SearchRunEvidenceSummary({ run }: { run: RetrievalSearchRun }) {
  const scopeLabels = searchRunScopeLabels(run.payload);
  const qualitySummary = run.summary.qualitySummary;
  const remediationSummary =
    run.summary.remediationSummary ?? searchRunRemediationSummary(run.summary);
  return (
    <span className="grid min-w-0 gap-1 rounded-md border border-border/70 bg-background/55 p-2">
      <span className="text-xs font-bold uppercase text-muted-foreground">
        Run scope
      </span>
      <span className="flex min-w-0 flex-wrap gap-1.5">
        {qualitySummary ? (
          <Badge variant={searchRunQualityBadgeVariant(qualitySummary)}>
            quality {humanize(qualitySummary.status)} {qualitySummary.score}
          </Badge>
        ) : null}
        <Badge variant={run.summary.coverage.length ? "warning" : "muted"}>
          {formatCount(run.summary.coverage.length, "coverage gap")}
        </Badge>
        <Badge variant={run.summary.conceptGrounding.length ? "success" : "warning"}>
          {formatCount(run.summary.conceptGrounding.length, "grounded concept")}
        </Badge>
        <Badge variant={run.summary.queryAspects.length ? "success" : "muted"}>
          {formatCount(run.summary.queryAspects.length, "search aspect")}
        </Badge>
        {scopeLabels.map((label) => (
          <Badge key={label} variant="muted">
            {label}
          </Badge>
        ))}
      </span>
      {qualitySummary?.top_action ? (
        <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
          Top action: {qualitySummary.top_action}
        </span>
      ) : null}
      {remediationSummary ? (
        <span className="min-w-0 break-words rounded-sm bg-muted px-2 py-1 text-xs font-semibold text-muted-foreground">
          Run remediation: {remediationSummary}
        </span>
      ) : null}
    </span>
  );
}

function searchRunRemediationSummary(summary: RetrievalRunSummary): string | null {
  const actions = summary.correctiveActionSummary;
  if (actions.count > 0) {
    const actionTypes = correctiveActionTypeCountEntries(actions.actionTypeCounts)
      .slice(0, 3)
      .map(([actionType, count]) => `${humanize(actionType)} ${count}`)
      .join(", ");
    const priority = actions.highestPriority ? `P${actions.highestPriority}` : "priority unreported";
    const topAction = actions.topActionTitle ?? "inspect backend corrective actions";
    return actionTypes
      ? `${topAction} (${priority}; ${actionTypes})`
      : `${topAction} (${priority})`;
  }
  if (summary.qualitySummary?.top_action) {
    return summary.qualitySummary.top_action;
  }
  if (summary.qualityWarningCount > 0 || summary.warningCount > 0) {
    return `inspect ${formatCount(
      summary.qualityWarningCount + summary.warningCount,
      "warning",
    )} before using this evidence`;
  }
  if (summary.hitCount === 0) {
    return "broaden search scope or inspect source inventory";
  }
  return null;
}

function SearchRunComparison({
  comparison,
  judgments,
}: {
  comparison: RetrievalRunComparison;
  judgments: RelevanceJudgment[];
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const reportCopyKey = "comparison-report";
  const reportCopied = copiedKey === reportCopyKey;
  const recommendedActions = React.useMemo(
    () => comparisonReportRecommendedActions(comparison, judgments),
    [comparison, judgments],
  );
  const operatorSummary = React.useMemo(
    () => comparisonOperatorSummary(comparison, recommendedActions),
    [comparison, recommendedActions],
  );

  const copyReport = async () => {
    await copyTextToClipboard(
      JSON.stringify(
        comparisonReportFromComparison(comparison, judgments, recommendedActions),
        null,
        2,
      ),
    );
    markCopied(reportCopyKey);
  };

  return (
    <div
      aria-label="Search run comparison"
      className="mt-1 grid gap-3 rounded-md border border-border bg-muted/25 p-3 text-sm"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
          Run comparison
          <HelpTooltip label="Run comparison help">
            Compares the currently displayed search package against the selected baseline run. Use this to tune query scope, filters, and retrieval policy, not to make clinical conclusions.
          </HelpTooltip>
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
          <Badge variant={comparison.qualitySummaryChanged ? "warning" : "success"}>
            {comparison.qualitySummaryChanged ? "quality changed" : "quality stable"}
          </Badge>
          <Button
            aria-label="Copy retrieval comparison report"
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
            {reportCopied ? "Copied" : "Copy comparison JSON"}
          </Button>
          <HelpTooltip label="Comparison JSON report help">
            Copies active versus baseline search payloads, quality deltas, evidence changes, rank movement, and recommended tuning actions for offline review.
          </HelpTooltip>
        </div>
      </div>
      <SectionHelpText>
        Baseline is the older comparison run; active is the currently displayed package. Treat warning deltas, quality changes, and rank movement as tuning signals that need evidence review.
      </SectionHelpText>
      <RunComparisonOperatorSummary summary={operatorSummary} />
      <div className="grid gap-1 rounded-md border border-border bg-card px-3 py-2 text-xs">
        <span className="font-bold uppercase text-muted-foreground">Baseline query</span>
        <span className="break-words leading-5">{comparison.baselineQuery}</span>
      </div>
      <RunComparisonAtAGlance
        actionSummary={comparisonRecommendedActionSummary(recommendedActions)}
        comparison={comparison}
      />
      <RunComparisonDiagnosis diagnosis={comparison.diagnosis} />
      <RunComparisonRecommendedActions
        actions={recommendedActions}
      />
      <RunComparisonMetrics metrics={comparison.metrics} />
      <RunComparisonSourceDiversity
        comparison={comparison.sourceDiversityComparison}
      />
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
        <RunComparisonConceptGrounding
          comparison={comparison.conceptGroundingComparison}
        />
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

function RunComparisonOperatorSummary({
  summary,
}: {
  summary: RetrievalComparisonOperatorSummary;
}) {
  const variant =
    summary.status === "improved"
      ? "success"
      : summary.status === "stable"
        ? "muted"
        : "warning";
  return (
    <div
      aria-label="Comparison operator summary"
      className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="grid min-w-0 gap-1">
          <span className="font-bold text-muted-foreground">
            Operator summary
          </span>
          <span className="break-words text-sm font-semibold">
            {summary.headline}
          </span>
        </div>
        <Badge variant={variant}>{humanize(summary.status)}</Badge>
      </div>
      <div className="grid gap-1 sm:grid-cols-2">
        {summary.bullets.map((item) => (
          <span
            className="rounded-md border border-border bg-muted/30 px-2 py-1 text-muted-foreground"
            key={item}
          >
            {item}
          </span>
        ))}
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <span className="font-semibold text-muted-foreground">
          Review focus
        </span>
        {summary.reviewFocus.map((item) => (
          <Badge key={item} variant="muted">
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function RunComparisonAtAGlance({
  actionSummary,
  comparison,
}: {
  actionSummary: RetrievalComparisonRecommendedActionSummary;
  comparison: RetrievalRunComparison;
}) {
  return (
    <div aria-label="Comparison at a glance" className="grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
      <RunComparisonMetricCard
        label="Readiness"
        tone={comparison.qualitySummaryChanged ? "warning" : "success"}
        value={readinessGlanceLabel(comparison)}
      />
      <RunComparisonMetricCard
        label="Action priority"
        tone={actionSummary.badge_variant === "success" ? "success" : "warning"}
        value={`P${actionSummary.highest_priority ?? "-"}`}
      />
      <RunComparisonMetricCard
        label="Evidence overlap"
        tone={comparison.metrics.overlapRatio >= 0.5 ? "success" : "warning"}
        value={formatPercent(comparison.metrics.overlapRatio)}
      />
      <RunComparisonMetricCard
        label="Result churn"
        tone={comparison.metrics.churnRate > 0.5 ? "warning" : "success"}
        value={formatPercent(comparison.metrics.churnRate)}
      />
      <RunComparisonMetricCard
        label="Top source"
        tone={comparison.topSourceChanged ? "warning" : "success"}
        value={comparison.topSourceChanged ? "changed" : "stable"}
      />
      <RunComparisonMetricCard
        label="Source spread"
        tone={
          comparison.sourceDiversityComparison.duplicateSelectedSourceDelta > 0
            ? "warning"
            : "success"
        }
        value={formatSignedDelta(
          comparison.sourceDiversityComparison.selectedSourceDelta,
        )}
      />
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

function RunComparisonRecommendedActions({
  actions,
}: {
  actions: RetrievalComparisonRecommendedAction[];
}) {
  const actionSummary = comparisonRecommendedActionSummary(actions);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">
          Recommended actions
        </span>
        <span className="flex flex-wrap justify-end gap-1.5">
          <Badge variant={actionSummary.badge_variant}>
            {formatCount(actionSummary.action_count, "action")}
          </Badge>
          <Badge variant="muted">P{actionSummary.highest_priority}</Badge>
          <Badge variant="muted">
            {formatCount(actionSummary.source_count, "source")}
          </Badge>
        </span>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {actionSummary.sources.map((source) => (
          <Badge key={source} variant="muted">
            {humanize(source)} {actionSummary.source_counts[source] ?? 0}
          </Badge>
        ))}
      </div>
      <div className="grid gap-1.5">
        {actions.map((item) => (
          <div className="grid gap-1" key={`${item.source}-${item.action}`}>
            <div className="flex min-w-0 flex-wrap items-start gap-2">
              <Badge variant={item.severity}>P{item.priority}</Badge>
              <Badge variant="muted">{humanize(item.source)}</Badge>
              <span className="min-w-0 flex-1 break-words font-semibold">
                {item.action}
              </span>
            </div>
            <span className="break-words pl-0 text-muted-foreground sm:pl-20">
              {item.reason}
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
    <div aria-label="Search comparison metrics" className="grid gap-2">
      <SectionHelpText>
        Overlap shows shared evidence; churn shows how much the result set changed; mean rank delta shows ordering instability among retained evidence.
      </SectionHelpText>
      <div className="grid gap-2 sm:grid-cols-2">
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
    </div>
  );
}

function RunComparisonSourceDiversity({
  comparison,
}: {
  comparison: RetrievalSourceDiversityComparison;
}) {
  return (
    <div
      aria-label="Source diversity comparison"
      className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">
          Source diversity
        </span>
        <span className="flex flex-wrap justify-end gap-1.5">
          <Badge
            variant={
              comparison.duplicateSelectedSourceDelta > 0 ? "warning" : "success"
            }
          >
            duplicates {formatSignedDelta(comparison.duplicateSelectedSourceDelta)}
          </Badge>
          <Badge variant="muted">
            overlap {formatPercent(comparison.sourceOverlapRatio)}
          </Badge>
        </span>
      </div>
      <SectionHelpText>
        Shows whether tuning changed selected-source coverage after hybrid retrieval and reranking. More selected sources is useful when evidence must come from independent standards or source families; more duplicate selected sources needs review.
      </SectionHelpText>
      <div className="grid gap-2 sm:grid-cols-3">
        <RunComparisonMetricCard
          label="Selected sources"
          tone={comparison.selectedSourceDelta >= 0 ? "success" : "warning"}
          value={`${comparison.baseline.selectedSourceCount} -> ${comparison.active.selectedSourceCount}`}
        />
        <RunComparisonMetricCard
          label="Candidate sources"
          tone={comparison.candidateSourceDelta >= 0 ? "success" : "warning"}
          value={`${comparison.baseline.candidateSourceCount} -> ${comparison.active.candidateSourceCount}`}
        />
        <RunComparisonMetricCard
          label="Policy"
          tone={
            comparison.selectionModeChanged || comparison.lambdaChanged
              ? "warning"
              : "success"
          }
          value={comparison.selectionModeChanged ? "changed" : "stable"}
        />
      </div>
      <div className="grid gap-1">
        <SourceListDelta
          label="Added sources"
          sourceIds={comparison.addedSourceIds}
          variant="success"
        />
        <SourceListDelta
          label="Removed sources"
          sourceIds={comparison.removedSourceIds}
          variant="warning"
        />
        <SourceListDelta
          label="Retained sources"
          sourceIds={comparison.retainedSourceIds}
          variant="muted"
        />
      </div>
    </div>
  );
}

function SourceListDelta({
  label,
  sourceIds,
  variant,
}: {
  label: string;
  sourceIds: string[];
  variant: "success" | "warning" | "muted";
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-start gap-2">
      <span className="w-28 shrink-0 font-semibold text-muted-foreground">
        {label}
      </span>
      {sourceIds.length ? (
        sourceIds.slice(0, 8).map((sourceId) => (
          <Badge key={sourceId} variant={variant}>
            {sourceId}
          </Badge>
        ))
      ) : (
        <Badge variant="muted">none</Badge>
      )}
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

function RunComparisonConceptGrounding({
  comparison,
}: {
  comparison: RetrievalConceptGroundingComparison;
}) {
  const changed = comparison.added.length || comparison.removed.length;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Concept grounding</span>
        <Badge variant={changed ? "warning" : "success"}>
          {changed ? "changed" : "stable"}
        </Badge>
      </div>
      <ConceptGroundingChangeList
        concepts={comparison.added}
        emptyLabel="No newly grounded concepts."
        label="Added"
        variant="success"
      />
      <ConceptGroundingChangeList
        concepts={comparison.removed}
        emptyLabel="No lost grounded concepts."
        label="Removed"
        variant="warning"
      />
      <ConceptGroundingChangeList
        concepts={comparison.retained}
        emptyLabel="No retained grounded concepts."
        label="Retained"
        variant="muted"
      />
    </div>
  );
}

function ConceptGroundingChangeList({
  concepts,
  emptyLabel,
  label,
  variant,
}: {
  concepts: ConceptGroundingSummary[];
  emptyLabel: string;
  label: string;
  variant: "success" | "warning" | "muted";
}) {
  return (
    <div className="grid gap-1">
      <span className="font-bold text-muted-foreground">{label}</span>
      {concepts.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {concepts.map((concept) => (
            <Badge
              className="max-w-full break-words"
              key={conceptGroundingKey(concept)}
              variant={variant}
            >
              {concept.standardSystem}
              {concept.code ? ` ${concept.code}` : ""}: {concept.displayName} (
              {concept.evidenceCount})
            </Badge>
          ))}
        </div>
      ) : (
        <span className="text-muted-foreground">{emptyLabel}</span>
      )}
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
      <div className="grid gap-1 rounded-md border border-border bg-card px-3 py-2">
        <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
          <span className="text-xs font-bold text-muted-foreground">Rank movement</span>
          <Badge variant="success">stable</Badge>
        </div>
        <SectionHelpText>
          Stable rank means retained evidence kept the same ordering between baseline and active runs.
        </SectionHelpText>
      </div>
    );
  }
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
          Rank movement
          <HelpTooltip label="Rank movement help">
            Rank movement only compares evidence retained in both runs. An item moving up means it ranked closer to the top in the active run.
          </HelpTooltip>
        </span>
        <Badge variant="warning">{formatCount(rankChanges.length, "changed rank")}</Badge>
      </div>
      <SectionHelpText>
        Use rank movement to debug relevance tuning. Large movements can come from query wording, filters, reranking, or rule-pack changes.
      </SectionHelpText>
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
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
          Search presets
          <HelpTooltip label="Search presets help">
            Data-driven examples loaded from trusted knowledge configuration. Applying one fills the query builder but does not run search until you submit.
          </HelpTooltip>
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
        <EvidenceInterpretationPanel packageData={packageData} />
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
        <EvidenceReadinessPanel
          isSearchPending={isSearchPending}
          onApplyBucketFilter={onApplyFacet}
          packageData={packageData}
        />
        <RecommendedActionsPanel
          activeFilters={resultFilterEntries}
          actions={packageData.recommended_actions ?? []}
          isSearchPending={isSearchPending}
          onApplyFilter={onApplyFacet}
          onClearAllFilters={onClearAllFilters}
          onClearFilter={onClearFilter}
        />
        <EvidencePackBuckets buckets={packageData.evidence_buckets ?? []} />
        <EvidenceSupportMatrix
          packageData={packageData}
          relevanceJudgments={relevanceJudgments}
          runId={runId}
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
            isSearchPending={isSearchPending}
            onClearAllFilters={onClearAllFilters}
            onClearFilter={onClearFilter}
            onApplyFacet={onApplyFacet}
            packageData={packageData}
            submittedSearchPayload={submittedSearchPayload}
          />
        ) : null}
      </CardContent>
    </Card>
  );
}

function EvidenceInterpretationPanel({ packageData }: { packageData: RetrievalPackage }) {
  const topHit = packageData.hits[0] ?? null;
  const topHitProvenance = topHit
    ? provenanceEntriesFromEvidence(topHit.evidence)
    : [];
  const topHitSupport = topHit
    ? evidenceSupportSummary(topHit, topHitProvenance)
    : null;
  const topHitExplanation = topHit
    ? hitMatchExplanation({
        aspectMatches: queryAspectMatchesFromHit(topHit),
        buckets: packageData.evidence_buckets ?? [],
        conceptMatches: conceptMatchesFromHit(topHit),
        hit: topHit,
        provenanceEntries: topHitProvenance,
        rankingBoostSignals: rankingBoostSignalsFromHit(topHit),
        scoreComponents: scoreComponentsFromHit(topHit),
      })
    : null;
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingRequiredBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const primaryAction = [...(packageData.recommended_actions ?? [])].sort(
    (left, right) => left.priority - right.priority,
  )[0] ?? null;
  const warnings = [
    ...(packageData.trace.warnings ?? []),
    ...((packageData.coverage?.warnings ?? []) as string[]),
  ].filter((warning) => warning.trim());
  const coverageItemCount =
    (packageData.coverage?.standard_system.length ?? 0) +
    (packageData.coverage?.query_aspects?.length ?? 0);
  const backendInterpretation = packageData.interpretation ?? null;
  const interpretation = evidenceInterpretationSummary({
    backendInterpretation,
    missingRequiredBuckets,
    packageData,
    primaryAction,
    requiredBuckets,
    topHit,
    topHitExplanation,
    topHitSupport,
    warnings,
  });

  return (
    <section className="grid gap-3 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Evidence interpretation
            </div>
            <Badge variant={interpretation.variant}>{interpretation.status}</Badge>
            {interpretation.supportStatus ? (
              <Badge variant={supportStatusBadgeVariant(interpretation.supportStatus)}>
                {interpretation.supportStatus} support
              </Badge>
            ) : null}
          </div>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-muted-foreground">
            {interpretation.summary}
          </p>
        </div>
        <HelpTooltip label="Evidence interpretation help">
          This panel summarizes the search package using backend trace data, evidence buckets, score drivers, matched terms, and recommended actions. It is for workflow evidence review, not clinical advice.
        </HelpTooltip>
      </div>

      <div className="grid gap-2 lg:grid-cols-3">
        <InterpretationCard
          label="Why the top result matched"
          title={interpretation.topSourceId ?? topHit?.evidence.source_id ?? "No ranked result"}
          detail={
            interpretation.topScoreDriver
              ? interpretation.topScoreDriver
              : interpretation.matchedTerms.length
              ? `Matched terms: ${interpretation.matchedTerms.join(", ")}`
              : "No ranked evidence was returned for this request."
          }
          items={[
            interpretation.conceptLabels.length
              ? `Concepts: ${interpretation.conceptLabels.join(", ")}`
              : null,
            interpretation.aspectLabels.length
              ? `Aspects: ${interpretation.aspectLabels.join(", ")}`
              : null,
            topHitSupport
              ? `${formatCount(topHitSupport.provenance_field_count, "provenance field")} / ${formatCount(topHitSupport.ranking_signal_count, "ranking signal")}`
              : null,
          ]}
        />
        <InterpretationCard
          label="Coverage"
          title={
            interpretation.requiredBucketCount
              ? `${interpretation.coveredRequiredBucketCount}/${interpretation.requiredBucketCount} required buckets`
              : "No required bucket policy"
          }
          detail={
            interpretation.missingRequiredBuckets.length
              ? `Missing required support: ${interpretation.missingRequiredBuckets.join(", ")}`
              : "The package has no missing required evidence buckets."
          }
          items={[
            packageData.coverage
              ? `${formatCount(coverageItemCount, "coverage item")} checked`
              : null,
            warnings.length ? `${formatCount(warnings.length, "warning")} raised` : null,
          ]}
        />
        <InterpretationCard
          label="Next action"
          title={primaryAction?.title ?? interpretation.nextActionTitle}
          detail={primaryAction?.description ?? interpretation.nextActionDetail}
          items={[
            primaryAction ? `Priority ${primaryAction.priority}` : null,
            primaryAction ? humanize(primaryAction.action_type) : null,
          ]}
        />
      </div>
    </section>
  );
}

function InterpretationCard({
  detail,
  items,
  label,
  title,
}: {
  detail: string;
  items: Array<string | null>;
  label: string;
  title: string;
}) {
  const visibleItems = items.filter((item): item is string => Boolean(item));
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="text-xs font-black uppercase text-muted-foreground">{label}</div>
      <div className="break-words text-sm font-black">{title}</div>
      <p className="break-words text-sm leading-6 text-muted-foreground">{detail}</p>
      {visibleItems.length ? (
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {visibleItems.map((item) => (
            <Badge className="max-w-full whitespace-normal break-words leading-4" key={item} variant="muted">
              {item}
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function evidenceInterpretationSummary({
  backendInterpretation,
  missingRequiredBuckets,
  packageData,
  primaryAction,
  requiredBuckets,
  topHit,
  topHitExplanation,
  topHitSupport,
  warnings,
}: {
  backendInterpretation: RetrievalInterpretation | null;
  missingRequiredBuckets: RetrievalEvidenceBucket[];
  packageData: RetrievalPackage;
  primaryAction: RetrievalRecommendedAction | null;
  requiredBuckets: RetrievalEvidenceBucket[];
  topHit: RetrievalHit | null;
  topHitExplanation: HitMatchExplanation | null;
  topHitSupport: EvidenceSupportSummary | null;
  warnings: string[];
}): {
  nextActionDetail: string;
  nextActionTitle: string;
  supportStatus: EvidenceSupportMatrixRow["supportStatus"] | null;
  status: string;
  summary: string;
  topScoreDriver: string | null;
  topSourceId: string | null;
  matchedTerms: string[];
  conceptLabels: string[];
  aspectLabels: string[];
  requiredBucketCount: number;
  coveredRequiredBucketCount: number;
  missingRequiredBuckets: string[];
  variant: React.ComponentProps<typeof Badge>["variant"];
} {
  if (backendInterpretation) {
    const supportStatus = hitSupportStatusValue(backendInterpretation.support_status);
    return {
      nextActionDetail:
        backendInterpretation.next_action_detail ??
        primaryAction?.description ??
        "Review backend interpretation and evidence details.",
      nextActionTitle:
        backendInterpretation.next_action_title ??
        primaryAction?.title ??
        "Review evidence",
      supportStatus,
      status: humanize(backendInterpretation.status),
      summary: backendInterpretation.summary,
      topScoreDriver: backendInterpretation.top_score_driver ?? null,
      topSourceId: backendInterpretation.top_source_id ?? null,
      matchedTerms: backendInterpretation.matched_terms ?? [],
      conceptLabels: backendInterpretation.concept_labels ?? [],
      aspectLabels: backendInterpretation.aspect_labels ?? [],
      requiredBucketCount: backendInterpretation.required_bucket_count,
      coveredRequiredBucketCount: backendInterpretation.covered_required_bucket_count,
      missingRequiredBuckets: backendInterpretation.missing_required_buckets ?? [],
      variant: supportStatus ? supportStatusBadgeVariant(supportStatus) : "muted",
    };
  }

  if (!topHit) {
    return {
      nextActionDetail:
        primaryAction?.description ??
        "Broaden search terms, clear exact source filters, or reindex the trusted source inventory.",
      nextActionTitle: primaryAction?.title ?? "Broaden or reindex",
      supportStatus: null,
      status: "no ranked evidence",
      summary:
        "No ranked evidence was returned. Treat this as a search coverage problem until filters, source inventory, and backend warnings have been reviewed.",
      topScoreDriver: null,
      topSourceId: null,
      matchedTerms: [],
      conceptLabels: [],
      aspectLabels: [],
      requiredBucketCount: requiredBuckets.length,
      coveredRequiredBucketCount: requiredBuckets.length - missingRequiredBuckets.length,
      missingRequiredBuckets: missingRequiredBuckets.map((bucket) => bucket.label),
      variant: "warning",
    };
  }

  if (missingRequiredBuckets.length) {
    return {
      nextActionDetail:
        primaryAction?.description ??
        "Add or broaden sources for the missing required evidence buckets before relying on the package.",
      nextActionTitle: primaryAction?.title ?? "Resolve support gaps",
      supportStatus: topHitExplanation?.supportStatus ?? null,
      status: "support gaps",
      summary: `The top result is ${topHit.evidence.source_id}, but required support is missing for ${missingRequiredBuckets.map((bucket) => bucket.label).join(", ")}.`,
      topScoreDriver: topHitExplanation?.topScoreDriver ?? null,
      topSourceId: topHit.evidence.source_id,
      matchedTerms: topHitExplanation?.matchedTerms ?? [],
      conceptLabels: topHitExplanation?.conceptLabels ?? [],
      aspectLabels: topHitExplanation?.aspectLabels ?? [],
      requiredBucketCount: requiredBuckets.length,
      coveredRequiredBucketCount: requiredBuckets.length - missingRequiredBuckets.length,
      missingRequiredBuckets: missingRequiredBuckets.map((bucket) => bucket.label),
      variant: "warning",
    };
  }

  if (warnings.length) {
    return {
      nextActionDetail:
        primaryAction?.description ??
        "Review warnings and compare score drivers before using the ranking order.",
      nextActionTitle: primaryAction?.title ?? "Review warnings",
      supportStatus: topHitExplanation?.supportStatus ?? null,
      status: "review warnings",
      summary: `The package returned ${formatCount(packageData.hits.length, "ranked hit")}; warnings indicate the search may need review before the result order is trusted.`,
      topScoreDriver: topHitExplanation?.topScoreDriver ?? null,
      topSourceId: topHit.evidence.source_id,
      matchedTerms: topHitExplanation?.matchedTerms ?? [],
      conceptLabels: topHitExplanation?.conceptLabels ?? [],
      aspectLabels: topHitExplanation?.aspectLabels ?? [],
      requiredBucketCount: requiredBuckets.length,
      coveredRequiredBucketCount: requiredBuckets.length - missingRequiredBuckets.length,
      missingRequiredBuckets: [],
      variant: "warning",
    };
  }

  const supportStatus = topHitExplanation?.supportStatus ?? "partial";
  const supportText = topHitSupport
    ? `${formatCount(topHitSupport.matched_term_count, "matched term")}, ${formatCount(topHitSupport.provenance_field_count, "provenance field")}, and ${formatCount(topHitSupport.ranking_signal_count, "ranking signal")}`
    : "available support signals";
  return {
    nextActionDetail:
      primaryAction?.description ??
      "Inspect the top evidence claim and optionally record a relevance judgment for evaluation.",
    nextActionTitle: primaryAction?.title ?? "Review top evidence",
    supportStatus,
    status: supportStatus === "strong" ? "ready to review" : "needs review",
    summary: `The top result is ${topHit.evidence.source_id}. It has ${supportStatus} operational support from ${supportText}.`,
    topScoreDriver: topHitExplanation?.topScoreDriver ?? null,
    topSourceId: topHit.evidence.source_id,
    matchedTerms: topHitExplanation?.matchedTerms ?? [],
    conceptLabels: topHitExplanation?.conceptLabels ?? [],
    aspectLabels: topHitExplanation?.aspectLabels ?? [],
    requiredBucketCount: requiredBuckets.length,
    coveredRequiredBucketCount: requiredBuckets.length - missingRequiredBuckets.length,
    missingRequiredBuckets: [],
    variant: supportStatusBadgeVariant(supportStatus),
  };
}

function SearchAnswerCard({
  packageData,
  submittedSearchPayload,
}: {
  packageData: RetrievalPackage;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const copyKey = "retrieval-answer-report";
  const qualitySummary = packageData.quality_summary ?? null;
  const topHit = packageData.hits[0] ?? null;
  const actions = packageData.recommended_actions ?? [];
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const warnings = [
    ...(packageData.trace.warnings ?? []),
    ...((packageData.coverage?.warnings ?? []) as string[]),
  ].filter((warning) => warning.trim());
  const remediation =
    packageData.remediation_summary ??
    optionalStringValue(packageData.handoff_context.remediation_summary) ??
    searchAnswerFallbackRemediation(packageData);
  const status = searchAnswerStatus(packageData);
  const copied = copiedKey === copyKey;

  const copyReport = async () => {
    await copyTextToClipboard(
      JSON.stringify(
        searchAnswerReportFromPackage(packageData, submittedSearchPayload, {
          missingBucketLabels: missingBuckets.map((bucket) => bucket.label),
          remediation,
          status,
          warningCount: warnings.length,
        }),
        null,
        2,
      ),
    );
    markCopied(copyKey);
  };

  return (
    <section
      aria-label="Search answer"
      className="grid gap-3 rounded-md border border-primary/25 bg-primary/5 p-3"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Search answer
            </div>
            <Badge variant={status.variant}>{status.label}</Badge>
            {qualitySummary ? (
              <Badge variant={qualitySummaryBadgeVariant(qualitySummary)}>
                readiness {qualitySummary.score}/100
              </Badge>
            ) : null}
            <Badge variant="muted">{formatCount(packageData.hits.length, "hit")}</Badge>
          </div>
          <div className="mt-2 max-w-4xl break-words text-base font-black leading-7">
            {remediation}
          </div>
          <p className="mt-1 max-w-4xl text-sm leading-6 text-muted-foreground">
            This is an evidence retrieval summary for workflow operations. It explains source
            support and search quality; it is not clinical advice.
          </p>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Button
            aria-label="Copy retrieval answer report"
            onClick={() => void copyReport()}
            size="sm"
            type="button"
            variant="outline"
          >
            {copied ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}
            {copied ? "Copied" : "Copy answer JSON"}
          </Button>
          <HelpTooltip label="Answer JSON report help">
            Copies the plain-language retrieval answer, readiness, warnings, top evidence, missing required buckets, and recommended backend actions.
          </HelpTooltip>
        </div>
      </div>

      <div className="grid gap-2 md:grid-cols-3">
        <SearchAnswerMetric
          label="Top evidence"
          value={topHit?.evidence.source_id ?? "No ranked source"}
          detail={
            topHit
              ? `${humanize(topHit.evidence.source_type)} / ${topHit.evidence.trust_level}`
              : "Broaden scope or inspect inventory before treating this as evidence absence."
          }
        />
        <SearchAnswerMetric
          label="Required support"
          value={
            requiredBuckets.length
              ? `${requiredBuckets.length - missingBuckets.length}/${requiredBuckets.length} covered`
              : "No bucket policy"
          }
          detail={
            missingBuckets.length
              ? `Missing: ${missingBuckets.map((bucket) => bucket.label).join(", ")}`
              : "Required evidence buckets are covered for this package."
          }
        />
        <SearchAnswerMetric
          label="Backend actions"
          value={actions.length ? formatCount(actions.length, "action") : "No action"}
          detail={
            actions[0]
              ? `${actions[0].title} / ${humanize(actions[0].action_type)}`
              : "No corrective action was generated by the quality policy."
          }
        />
      </div>

      {warnings.length ? (
        <div className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5">
          <div className="font-black uppercase text-amber-800">
            Coverage warnings
          </div>
          {warnings.slice(0, 3).map((warning) => (
            <div className="break-words text-amber-900" key={warning}>
              {warning}
            </div>
          ))}
          {warnings.length > 3 ? (
            <div className="font-semibold text-amber-900">
              {formatCount(warnings.length - 3, "additional warning")} hidden in detailed panels.
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function SearchAnswerMetric({
  detail,
  label,
  value,
}: {
  detail: string;
  label: string;
  value: string;
}) {
  return (
    <div className="min-w-0 rounded-md border border-border bg-card px-3 py-2">
      <div className="text-xs font-black uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 break-words text-sm font-black">{value}</div>
      <div className="mt-1 break-words text-xs leading-5 text-muted-foreground">
        {detail}
      </div>
    </div>
  );
}

function searchAnswerStatus(packageData: RetrievalPackage): {
  label: string;
  variant: "default" | "success" | "warning" | "destructive" | "muted";
} {
  if (!packageData.hits.length) return { label: "No evidence hit", variant: "destructive" };
  const qualityStatus = packageData.quality_summary?.status;
  if (qualityStatus === "blocked") return { label: "Blocked", variant: "destructive" };
  if (qualityStatus === "review") return { label: "Needs review", variant: "warning" };
  if (packageData.trace.warnings.length) return { label: "Review warnings", variant: "warning" };
  return { label: "Evidence ready", variant: "success" };
}

function searchAnswerFallbackRemediation(packageData: RetrievalPackage): string {
  const topAction = packageData.recommended_actions?.[0];
  if (topAction) return `${topAction.title}: ${topAction.description}`;
  const qualityAction = packageData.quality_summary?.top_action;
  if (qualityAction) return qualityAction;
  if (!packageData.hits.length) return "Broaden search scope or inspect source inventory.";
  return "Review the top evidence hit, readiness score, and source provenance before using this package.";
}

function searchAnswerReportFromPackage(
  packageData: RetrievalPackage,
  submittedSearchPayload: RetrievalSearchPayload | null,
  summary: {
    missingBucketLabels: string[];
    remediation: string;
    status: { label: string; variant: string };
    warningCount: number;
  },
) {
  const topHit = packageData.hits[0] ?? null;
  return {
    report_type: "retrieval_search_answer",
    version: 1,
    generated_at: new Date().toISOString(),
    query: submittedSearchPayload?.query ?? null,
    status: summary.status.label,
    remediation_summary: summary.remediation,
    interpretation: retrievalInterpretationReport(packageData),
    standard_search_plan: retrievalStandardSearchPlanReport(packageData),
    medical_search_hints: medicalSearchHintReport(packageData),
    diversity: retrievalDiversityReport(packageData),
    readiness: packageData.quality_summary,
    warnings: {
      count: summary.warningCount,
      trace: packageData.trace.warnings,
      coverage: packageData.coverage?.warnings ?? [],
    },
    required_support: {
      missing_buckets: summary.missingBucketLabels,
      buckets: packageData.evidence_buckets ?? [],
    },
    top_evidence: topHit
      ? {
          evidence_id: topHit.evidence.evidence_id,
          source_id: topHit.evidence.source_id,
          source_type: topHit.evidence.source_type,
          trust_level: topHit.evidence.trust_level,
          claim: formatClaim(topHit.evidence.claim),
          score: topHit.score,
          match_explanation: topHit.match_explanation ?? null,
        }
      : null,
    recommended_actions: (packageData.recommended_actions ?? [])
      .slice(0, 6)
      .map(correctiveActionReportItem),
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

function NoResultRemediationPanel({
  isSearchPending,
  onApplyFacet,
  onClearAllFilters,
  onClearFilter,
  packageData,
  submittedSearchPayload,
}: {
  isSearchPending: boolean;
  onApplyFacet: (field: SupportedFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
  packageData: RetrievalPackage;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  const submittedFilters = submittedSearchPayload
    ? activeFilterEntries(activeFacetFiltersFromPayload(submittedSearchPayload))
    : [];
  const sourceFilter = submittedFilters.find((filter) => filter.field === "source_id");
  const suggestedAction = firstSupportedRecommendedAction(packageData.recommended_actions ?? []);
  const missingBucketCount = (packageData.evidence_buckets ?? []).filter(
    (bucket) => bucket.required && bucket.hit_count === 0,
  ).length;
  const candidateCount = packageData.trace.candidates_seen;
  return (
    <div className="grid gap-3 rounded-md border border-amber-200 bg-amber-50 p-4">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-sm font-black">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-700" />
            No matching evidence returned
          </div>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">
            The backend completed the search, but no ranked evidence hit is available for this exact request. Use the remediation checks below before trusting the result as evidence absence.
          </p>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant="warning">{formatCount(candidateCount, "candidate")}</Badge>
          {missingBucketCount ? (
            <Badge variant="warning">{formatCount(missingBucketCount, "required gap")}</Badge>
          ) : null}
          {submittedFilters.length ? (
            <Badge variant="muted">{formatCount(submittedFilters.length, "active filter")}</Badge>
          ) : null}
        </div>
      </div>
      <div className="grid gap-2 md:grid-cols-3">
        <NoResultActionCard
          title={submittedFilters.length ? "Loosen scope" : "Broaden query"}
          text={
            submittedFilters.length
              ? "The submitted search has active filters. Remove exact source, standard, domain, or trust filters if you need broader evidence."
              : "Try fewer exact terms, add field names, or start from a trusted preset when the query is too narrow."
          }
        >
          {submittedFilters.length ? (
            <div className="grid gap-2">
              <div className="flex min-w-0 flex-wrap gap-1.5">
                {submittedFilters.map((filter) => (
                  <Badge className="max-w-full break-words" key={filter.field} variant="muted">
                    {filter.label}: {filter.displayValue}
                  </Badge>
                ))}
              </div>
              <div className="flex min-w-0 flex-wrap gap-1.5">
                {sourceFilter ? (
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
                  disabled={isSearchPending}
                  onClick={onClearAllFilters}
                  size="sm"
                  title="Clear all active metadata filters and rerun search"
                  type="button"
                  variant="outline"
                >
                  <ListFilter className="h-4 w-4" />
                  Clear all filters
                </Button>
              </div>
            </div>
          ) : null}
        </NoResultActionCard>
        <NoResultActionCard
          title={candidateCount ? "Inspect quality gaps" : "Check source inventory"}
          text={
            candidateCount
              ? "Candidates were seen, so review readiness, evidence buckets, and strategy recommendations for why none became usable hits."
              : "No candidates were seen. Reindex the trusted corpus or confirm the source inventory contains the domain and standard you need."
          }
        />
        <NoResultActionCard
          title={suggestedAction ? "Apply backend suggestion" : "Use guided presets"}
          text={
            suggestedAction
              ? "A backend corrective action has a supported filter. Apply it only if it matches the evidence class you need."
              : "No supported corrective filter was returned. Use a preset or adjust schema, format, fields, and source scope."
          }
        >
          {suggestedAction ? (
            <Button
              disabled={isSearchPending}
              onClick={() => onApplyFacet(suggestedAction.field, suggestedAction.value)}
              size="sm"
              type="button"
              variant="outline"
            >
              <ListFilter className="h-4 w-4" />
              Apply {filterFieldLabel(suggestedAction.field)}
            </Button>
          ) : null}
        </NoResultActionCard>
      </div>
    </div>
  );
}

function NoResultActionCard({
  children,
  text,
  title,
}: {
  children?: React.ReactNode;
  text: string;
  title: string;
}) {
  return (
    <div className="grid content-start gap-2 rounded-md border border-amber-200 bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <p className="text-sm leading-6 text-muted-foreground">{text}</p>
      {children}
    </div>
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

function RetrievalFirstRunGuide() {
  return (
    <div className="grid gap-3 rounded-md border border-border bg-muted/20 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-sm font-black">
            <FileSearch className="h-4 w-4 text-primary" />
            Start with a concrete healthcare data question
          </div>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">
            Retrieval finds trusted schema, terminology, policy, and corpus evidence. It is best for explaining data operations, validation findings, and workflow grounding.
          </p>
        </div>
        <Badge variant="muted">first search guide</Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-3">
        <FirstRunGuideCard
          title="1. Pick a preset"
          text="Use presets for common lab, FHIR-like, PHI, and standards questions. They fill the builder safely."
        />
        <FirstRunGuideCard
          title="2. Add context"
          text="Fields, schema, format, and source filters narrow evidence. Leave them blank when you need broad discovery."
        />
        <FirstRunGuideCard
          title="3. Read readiness first"
          text="After search, check readiness, strategy recommendations, and evidence buckets before individual hits."
        />
      </div>
      <div className="grid gap-2 rounded-md border border-border bg-card p-3 text-sm">
        <div className="font-black">Good starter questions</div>
        <ul className="grid gap-1 text-muted-foreground">
          <li>Validate lab CSV fields and explain missing unit issues.</li>
          <li>Find trusted evidence for FHIR Observation mapping.</li>
          <li>Which fields are sensitive patient information in this dataset?</li>
        </ul>
      </div>
    </div>
  );
}

function FirstRunGuideCard({ text, title }: { text: string; title: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <p className="mt-1 text-sm leading-6 text-muted-foreground">{text}</p>
    </div>
  );
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
        onClearFilter={onClearFilter}
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
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        recommendations={strategyRecommendations}
      />

      <StandardSearchPlanPanel
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

function QueryHealthPanel({
  activeFilters,
  isSearchPending,
  items,
  onClearAllFilters,
  onClearFilter,
}: {
  activeFilters: ActiveFilterEntry[];
  isSearchPending: boolean;
  items: QueryHealthItem[];
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
}) {
  const overconstrained = items.some(
    (item) => item.code === "diagnostic_overconstrained_metadata_filters",
  );
  const sourceFilter = activeFilters.find((filter) => filter.field === "source_id");
  return (
    <div
      aria-label="Query health checklist"
      className="grid gap-2 rounded-md border border-border bg-card p-3"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
          Query health
          <HelpTooltip label="Query health help">
            Data-derived checklist for search scope and interpretation risk. Review warnings before trusting the ranked evidence.
          </HelpTooltip>
        </div>
        <Badge variant={queryHealthOverallVariant(items)}>
          {queryHealthOverallLabel(items)}
        </Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <div
            className="grid gap-1 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm"
            key={item.code}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-black">{item.label}</span>
              <Badge variant={queryHealthBadgeVariant(item.status)}>
                {humanize(item.status)}
              </Badge>
            </div>
            <div className="break-words text-xs leading-5 text-muted-foreground">
              {item.description}
            </div>
            {item.code === "diagnostic_overconstrained_metadata_filters" ? (
              <div className="flex min-w-0 flex-wrap gap-1.5 pt-1">
                {sourceFilter ? (
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
        ))}
      </div>
      {overconstrained ? (
        <SectionHelpText>
          These actions broaden the submitted search and rerun retrieval. Use them before deciding the corpus lacks evidence.
        </SectionHelpText>
      ) : null}
    </div>
  );
}

function CockpitMetricCard({
  helpText,
  label,
  supporting,
  tone,
  value,
}: {
  helpText: string;
  label: string;
  supporting: string;
  tone: "success" | "warning" | "info";
  value: string;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2">
      <span className="inline-flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
        {label}
        <HelpTooltip label={`${label} help`}>{helpText}</HelpTooltip>
      </span>
      <Badge variant={tone === "info" ? "default" : tone}>{value}</Badge>
      <span className="break-words text-xs leading-5 text-muted-foreground">
        {supporting}
      </span>
    </div>
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

function SearchReadinessChecklist({
  items,
}: {
  items: SearchReadinessChecklistItem[];
}) {
  const overallVariant = queryHealthOverallVariant(items);
  const overallLabel = queryHealthOverallLabel(items);
  return (
    <section
      aria-label="Search readiness checklist"
      className="grid gap-2 rounded-md border border-border bg-card p-3"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Search readiness checklist
          </div>
          <div className="mt-1 break-words text-sm font-semibold text-muted-foreground">
            Fast review of whether this search package is ready to inspect,
            needs human review, or should be remediated before downstream use.
          </div>
        </div>
        <Badge variant={overallVariant}>{humanize(overallLabel)}</Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-muted/25 px-3 py-2"
            key={item.code}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-1.5">
              <span className="break-words text-xs font-black text-muted-foreground">
                {item.label}
              </span>
              <Badge variant={queryHealthBadgeVariant(item.status)}>
                {humanize(item.status)}
              </Badge>
            </div>
            <div className="break-words text-xs leading-5 text-muted-foreground">
              {item.detail}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
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

function queryHealthBadgeVariant(
  status: QueryHealthItem["status"],
): "success" | "warning" | "destructive" | "muted" {
  if (status === "ok") return "success";
  if (status === "blocked") return "destructive";
  if (status === "review") return "warning";
  return "muted";
}

function queryHealthOverallVariant(
  items: Array<{ status: QueryHealthItem["status"] }>,
): "success" | "warning" | "destructive" | "muted" {
  if (items.some((item) => item.status === "blocked")) return "destructive";
  if (items.some((item) => item.status === "review")) return "warning";
  if (items.some((item) => item.status === "ok")) return "success";
  return "muted";
}

function queryHealthOverallLabel(
  items: Array<{ status: QueryHealthItem["status"] }>,
): string {
  if (items.some((item) => item.status === "blocked")) return "blocked";
  if (items.some((item) => item.status === "review")) return "review";
  if (items.some((item) => item.status === "ok")) return "healthy";
  return "unscored";
}

function StrategyRecommendationsPanel({
  isSearchPending,
  onApplyFilter,
  recommendations,
}: {
  isSearchPending: boolean;
  onApplyFilter: (field: SupportedFilterField, value: string) => void;
  recommendations: RetrievalStrategyRecommendation[];
}) {
  if (!recommendations.length) {
    return null;
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
          Strategy recommendations
          <HelpTooltip label="Strategy recommendations help">
            Backend-generated search advice. Apply a recommendation only when it matches the operational question and the suggested filter is supported.
          </HelpTooltip>
        </div>
        <Badge variant="muted">{formatCount(recommendations.length, "rule")}</Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {recommendations.slice(0, 4).map((recommendation) => (
          <StrategyRecommendationCard
            isSearchPending={isSearchPending}
            key={recommendation.recommendation_id}
            onApplyFilter={onApplyFilter}
            recommendation={recommendation}
          />
        ))}
      </div>
    </div>
  );
}

function StandardSearchPlanPanel({
  isSearchPending,
  onApplyFilter,
  plan,
}: {
  isSearchPending: boolean;
  onApplyFilter: (field: SupportedFilterField, value: string) => void;
  plan: RetrievalStandardSearchPlan | null;
}) {
  if (!plan || !plan.steps.length) {
    return null;
  }
  const visibleNotes = plan.governance_notes.slice(0, 3);
  return (
    <div className="grid gap-3 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            Healthcare search plan
            <HelpTooltip label="Healthcare search plan help">
              Backend-selected playbook for the next standards-aware search. It maps the query to FHIR, terminology, privacy, or external medical-search routes before downstream use.
            </HelpTooltip>
          </div>
          <div className="mt-1 break-words text-sm leading-6 text-muted-foreground">
            {plan.summary}
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={standardRouteBadgeVariant(plan.primary_route)}>
            {humanize(plan.primary_route)}
          </Badge>
          <Badge variant="muted">{formatCount(plan.steps.length, "step")}</Badge>
          {plan.missing_routes.length ? (
            <Badge variant="warning">
              {formatCount(plan.missing_routes.length, "missing route")}
            </Badge>
          ) : null}
        </div>
      </div>
      <div className="grid gap-2 lg:grid-cols-2">
        {plan.steps.slice(0, 4).map((step) => (
          <StandardSearchStepCard
            isSearchPending={isSearchPending}
            key={step.step_id}
            onApplyFilter={onApplyFilter}
            step={step}
          />
        ))}
      </div>
      {visibleNotes.length ? (
        <div className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-950">
          <div className="font-black uppercase">Governance guardrails</div>
          <ul className="grid gap-1">
            {visibleNotes.map((note) => (
              <li className="grid grid-cols-[12px_minmax(0,1fr)] gap-2" key={note}>
                <span aria-hidden="true" className="pt-0.5 font-black">
                  -
                </span>
                <span className="min-w-0 break-words">{note}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function SourceDiversityPanel({
  diversity,
  isSearchPending,
}: {
  diversity: DiversityStack;
  isSearchPending: boolean;
}) {
  const visibleSelections = diversity.selectedHits
    .filter((selection) => selection.evidenceId && selection.sourceId)
    .slice(0, 4);
  const duplicateTone =
    diversity.duplicateSelectedSourceCount > 0 ? "warning" : "success";
  const modeLabel = humanize(diversity.selectionMode);
  return (
    <div className="grid gap-3 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            Source diversity
            <HelpTooltip label="Source diversity help">
              Shows how the backend selected a balanced evidence set after hybrid retrieval and reranking. This helps detect over-reliance on one source before the package is used downstream.
            </HelpTooltip>
          </div>
          <div className="mt-1 break-words text-sm leading-6 text-muted-foreground">
            {diversity.enabled
              ? "Final evidence was selected with source-aware diversity scoring so strong matches from repeated sources do not hide independent standards or policy evidence."
              : "Source diversity selection is disabled for this retrieval run; evidence follows score order only."}
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={diversity.enabled ? "success" : "warning"}>
            {diversity.enabled ? "enabled" : "disabled"}
          </Badge>
          <Badge variant="muted">{modeLabel}</Badge>
          <Badge variant={duplicateTone}>
            {formatCount(diversity.duplicateSelectedSourceCount, "duplicate")}
          </Badge>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        <DiversityMetricCard
          label="Candidate sources"
          value={diversity.candidateSourceCount}
        />
        <DiversityMetricCard
          label="Selected sources"
          value={diversity.selectedSourceCount}
        />
        <DiversityMetricCard
          label="Balance weight"
          value={diversity.lambda === null ? "n/a" : diversity.lambda.toFixed(2)}
        />
      </div>
      {isSearchPending ? (
        <div className="rounded-md border border-border bg-muted/25 px-3 py-2 text-sm font-semibold text-muted-foreground">
          Updating source-diversity trace...
        </div>
      ) : visibleSelections.length ? (
        <div className="grid gap-2">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Selected-hit rationale
          </div>
          {visibleSelections.map((selection) => (
            <div
              className="grid gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-xs"
              key={`${selection.selectedRank}:${selection.evidenceId}`}
            >
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                  <Badge variant="muted">#{selection.selectedRank}</Badge>
                  <span className="min-w-0 break-words font-black">
                    {selection.sourceId}
                  </span>
                </div>
                <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
                  <Badge variant="muted">original #{selection.originalRank}</Badge>
                  <Badge variant={selection.redundancyScore > 0 ? "warning" : "success"}>
                    redundancy {selection.redundancyScore.toFixed(2)}
                  </Badge>
                  <Badge variant="muted">
                    score {selection.selectionScore.toFixed(3)}
                  </Badge>
                </div>
              </div>
              <div className="break-words leading-5 text-muted-foreground">
                {selection.reason}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-border bg-muted/25 px-3 py-2 text-sm font-semibold text-muted-foreground">
          No selected-hit diversity trace was returned for this run.
        </div>
      )}
    </div>
  );
}

function DiversityMetricCard({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div className="rounded-md border border-border bg-muted/20 px-3 py-2">
      <div className="text-xs font-black uppercase text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-xl font-black tabular-nums">{value}</div>
    </div>
  );
}

function StandardSearchStepCard({
  isSearchPending,
  onApplyFilter,
  step,
}: {
  isSearchPending: boolean;
  onApplyFilter: (field: SupportedFilterField, value: string) => void;
  step: RetrievalStandardSearchStep;
}) {
  const filterAction = suggestedFilterAction(step.suggested_filters);
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      <div className="grid min-w-0 gap-2 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
        <div className="min-w-0">
          <div className="break-words font-black">{step.label}</div>
          <div className="mt-1 flex min-w-0 flex-wrap items-center gap-1.5">
            <Badge variant="muted">P{step.priority}</Badge>
            <Badge variant="success">{step.standard_system}</Badge>
            <Badge variant={standardRouteBadgeVariant(step.route_type)}>
              {humanize(step.route_type)}
            </Badge>
          </div>
        </div>
        {filterAction ? (
          <Button
            disabled={isSearchPending}
            onClick={() => onApplyFilter(filterAction.field, filterAction.value)}
            size="sm"
            type="button"
            variant="outline"
          >
            <ListFilter className="h-4 w-4" />
            Apply {filterFieldLabel(filterAction.field)}
          </Button>
        ) : null}
      </div>
      <div className="break-words text-xs leading-5 text-muted-foreground">
        {step.rationale}
      </div>
      <StandardSearchMatchReasons metadata={step.metadata} />
      <div className="break-words rounded-md border border-border bg-card px-3 py-2 font-mono text-xs leading-5 text-foreground">
        {step.query}
      </div>
      <StandardSearchGovernanceNotes notes={step.governance_notes} />
    </div>
  );
}

function StandardSearchMatchReasons({ metadata }: { metadata: Record<string, unknown> }) {
  const reasons = standardSearchMatchReasons(metadata);
  if (!reasons.length) {
    return null;
  }
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5 text-xs">
      <span className="font-black uppercase text-muted-foreground">Matched by</span>
      {reasons.map((reason) => (
        <Badge key={`${reason.label}:${reason.value}`} variant={reason.variant}>
          {reason.label}: {reason.value}
        </Badge>
      ))}
    </div>
  );
}

function standardSearchMatchReasons(metadata: Record<string, unknown>) {
  const sources: {
    key: string;
    label: string;
    variant: React.ComponentProps<typeof Badge>["variant"];
  }[] = [
    { key: "matched_fields", label: "field", variant: "default" },
    { key: "matched_query_aspects", label: "aspect", variant: "muted" },
    { key: "matched_standards", label: "standard", variant: "success" },
    { key: "matched_concepts", label: "concept", variant: "muted" },
    { key: "source_quality_signal_codes", label: "signal", variant: "warning" },
  ];
  return sources.flatMap((source) =>
    stringArrayValue(metadata[source.key])
      .slice(0, 3)
      .map((value) => ({
        label: source.label,
        value,
        variant: source.variant,
      })),
  );
}

function StandardSearchGovernanceNotes({ notes }: { notes: string[] }) {
  const visibleNotes = notes.slice(0, 2);
  if (!visibleNotes.length) {
    return null;
  }
  return (
    <div className="grid gap-1 text-xs leading-5 text-muted-foreground">
      {visibleNotes.map((note) => (
        <div className="grid grid-cols-[14px_minmax(0,1fr)] gap-2" key={note}>
          <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-700" />
          <span className="min-w-0 break-words">{note}</span>
        </div>
      ))}
    </div>
  );
}

function standardRouteBadgeVariant(
  routeType: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  const normalized = routeType.toLowerCase();
  if (normalized.includes("privacy") || normalized.includes("review")) return "warning";
  if (normalized.includes("fhir") || normalized.includes("terminology")) return "default";
  if (normalized.includes("validation")) return "success";
  if (normalized.includes("external")) return "muted";
  return "muted";
}

function StrategyRecommendationCard({
  isSearchPending,
  onApplyFilter,
  recommendation,
}: {
  isSearchPending: boolean;
  onApplyFilter: (field: SupportedFilterField, value: string) => void;
  recommendation: RetrievalStrategyRecommendation;
}) {
  const filterAction = suggestedFilterAction(recommendation.suggested_filters);
  return (
    <div className="grid gap-1 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <Badge variant={strategyRecommendationVariant(recommendation.status)}>
          {humanize(recommendation.status)}
        </Badge>
        <span className="break-words font-black">{recommendation.title}</span>
      </div>
      <div className="break-words text-xs font-semibold text-muted-foreground">
        {humanize(recommendation.technique)}
      </div>
      <div className="break-words text-xs leading-5 text-muted-foreground">
        {recommendation.rationale}
      </div>
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        {recommendation.source_signal_codes.slice(0, 3).map((code) => (
          <Badge key={code} variant="muted">
            {humanize(code)}
          </Badge>
        ))}
        {filterAction ? (
          <Button
            disabled={isSearchPending}
            onClick={() => onApplyFilter(filterAction.field, filterAction.value)}
            size="sm"
            type="button"
            variant="outline"
          >
            <ListFilter className="h-4 w-4" />
            Apply {filterFieldLabel(filterAction.field)}
          </Button>
        ) : null}
      </div>
    </div>
  );
}

function strategyRecommendationVariant(status: string) {
  if (status === "active") return "success";
  if (status === "action_required" || status === "caution") return "warning";
  return "muted";
}

function EvidenceReadinessPanel({
  isSearchPending,
  onApplyBucketFilter,
  packageData,
}: {
  isSearchPending: boolean;
  onApplyBucketFilter: (field: SupportedFilterField, value: string) => void;
  packageData: RetrievalPackage;
}) {
  const qualitySummary = packageData.quality_summary ?? null;
  const requiredBuckets = (packageData.evidence_buckets ?? []).filter(
    (bucket) => bucket.required,
  );
  const missingBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const bucketSignal = (packageData.quality_signals ?? []).find(
    (signal) => signal.code === "missing_required_evidence_buckets",
  );
  const ready = missingBuckets.length === 0 && qualitySummary?.status !== "blocked";
  const interpretation = readinessInterpretation(qualitySummary, missingBuckets.length);
  return (
    <div
      className={cn(
        "grid gap-3 rounded-md border p-3",
        ready
          ? "border-emerald-200 bg-emerald-50"
          : "border-amber-200 bg-amber-50",
      )}
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Evidence readiness
          </div>
          <div className="mt-1 break-words text-sm font-black">
            {ready
              ? "Required evidence classes are present"
              : "Required evidence classes need review"}
          </div>
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          {qualitySummary ? (
            <Badge variant={qualitySummaryBadgeVariant(qualitySummary)}>
              {humanize(qualitySummary.status)} {qualitySummary.score}/100
            </Badge>
          ) : null}
          <Badge variant={missingBuckets.length ? "warning" : "success"}>
            {missingBuckets.length
              ? formatCount(missingBuckets.length, "required gap")
              : "required buckets covered"}
          </Badge>
        </div>
      </div>
      {missingBuckets.length ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {missingBuckets.map((bucket) => {
            const action = bucketSuggestedFilter(bucket);
            return (
              <div
                className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-amber-200 bg-card px-3 py-2"
                key={bucket.bucket_id}
              >
                <div className="min-w-0">
                  <div className="break-words text-sm font-black">
                    Missing {bucket.label}
                  </div>
                  <div className="mt-1 break-words text-xs text-muted-foreground">
                    {action
                      ? `${filterFieldLabel(action.field)}: ${formatFilterValue(action.field, action.value)}`
                      : "No supported filter is available for this bucket."}
                  </div>
                </div>
                {action ? (
                  <Button
                    disabled={isSearchPending}
                    onClick={() => onApplyBucketFilter(action.field, action.value)}
                    size="sm"
                    type="button"
                    variant="outline"
                  >
                    <ListFilter className="h-4 w-4" />
                    Apply
                  </Button>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}
      <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2">
        <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
          <div className="break-words text-sm font-black">
            {interpretation.title}
          </div>
          <Badge variant={interpretation.variant}>{interpretation.badge}</Badge>
        </div>
        <p className="break-words text-sm leading-6 text-muted-foreground">
          {interpretation.description}
        </p>
        {qualitySummary ? (
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {qualitySummary.blocker_codes.slice(0, 4).map((code) => (
              <Badge className="max-w-full break-words" key={`blocker-${code}`} variant="destructive">
                {humanize(code)}
              </Badge>
            ))}
            {qualitySummary.warning_codes.slice(0, 4).map((code) => (
              <Badge className="max-w-full break-words" key={`warning-${code}`} variant="warning">
                {humanize(code)}
              </Badge>
            ))}
          </div>
        ) : null}
      </div>
      <div className="break-words text-sm leading-6 text-muted-foreground">
        {bucketSignal?.suggested_action ??
          qualitySummary?.top_action ??
          "Review selected evidence before using it downstream."}
      </div>
    </div>
  );
}

function readinessInterpretation(
  qualitySummary: RetrievalQualitySummary | null,
  missingRequiredBucketCount: number,
): {
  badge: string;
  description: string;
  title: string;
  variant: "success" | "warning" | "destructive" | "muted";
} {
  if (!qualitySummary) {
    return {
      badge: "unscored",
      description:
        "No readiness score was returned. Treat the evidence as unreviewed until quality signals are available.",
      title: "Readiness score unavailable",
      variant: "muted",
    };
  }
  if (qualitySummary.status === "blocked") {
    return {
      badge: "blocked",
      description:
        "Do not use this evidence package downstream yet. Resolve blocker codes or apply backend corrective actions first.",
      title: "Blocked for governed use",
      variant: "destructive",
    };
  }
  if (qualitySummary.status === "review" || missingRequiredBucketCount > 0) {
    return {
      badge: "review",
      description:
        "Use this package only with human review. Missing required evidence, warnings, or low confidence can change the interpretation.",
      title: "Needs human review",
      variant: "warning",
    };
  }
  if (qualitySummary.status === "ready") {
    return {
      badge: "ready",
      description:
        "Required evidence classes are present. Still inspect source provenance and limitations before operational use.",
      title: "Ready for evidence review",
      variant: "success",
    };
  }
  return {
    badge: humanize(qualitySummary.status),
    description:
      "The backend returned a non-standard readiness status. Review quality signals before using the evidence package.",
    title: "Readiness requires inspection",
    variant: "muted",
  };
}

function RecommendedActionsPanel({
  activeFilters,
  actions,
  isSearchPending,
  onApplyFilter,
  onClearAllFilters,
  onClearFilter,
}: {
  activeFilters: ActiveFilterEntry[];
  actions: RetrievalRecommendedAction[];
  isSearchPending: boolean;
  onApplyFilter: (field: SupportedFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
}) {
  if (!actions.length) {
    return <TokenList items={[]} title="Corrective actions" />;
  }
  const actionTypeCounts = recommendedActionTypeCounts(actions);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Corrective actions
          </div>
          <div className="mt-1 break-words text-sm text-muted-foreground">
            Backend-derived next steps from retrieval quality signals.
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant="warning">{formatCount(actions.length, "action")}</Badge>
          {Object.entries(actionTypeCounts).map(([actionType, count]) => (
            <Badge key={actionType} variant="muted">
              {humanize(actionType)} {count}
            </Badge>
          ))}
        </div>
      </div>
      <div className="grid gap-2">
        {actions.slice(0, 6).map((action) => {
          const filterAction = recommendedActionFilter(action);
          const isBroadeningAction = action.action_type === "broaden_query";
          const sourceFilter = activeFilters.find((filter) => filter.field === "source_id");
          const sourceLabel = recommendedActionSourceLabel(action);
          return (
            <div
              className="grid gap-2 rounded-md border border-border bg-card p-3"
              key={action.action_id}
            >
              <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                    <Badge variant={qualitySignalBadgeVariant(action.severity)}>
                      P{action.priority}
                    </Badge>
                    <Badge variant="muted">{humanize(action.action_type)}</Badge>
                    {sourceLabel ? <Badge variant="muted">{sourceLabel}</Badge> : null}
                    {action.source_signal_codes.slice(0, 2).map((code) => (
                      <Badge
                        className="max-w-full break-words"
                        key={`${action.action_id}-${code}`}
                        variant="muted"
                      >
                        {humanize(code)}
                      </Badge>
                    ))}
                  </div>
                  <div className="mt-2 break-words text-sm font-black">
                    {action.title}
                  </div>
                  <div className="mt-1 break-words text-xs leading-5 text-muted-foreground">
                    {action.description}
                  </div>
                </div>
                {filterAction ? (
                  <Button
                    disabled={isSearchPending}
                    onClick={() => onApplyFilter(filterAction.field, filterAction.value)}
                    size="sm"
                    type="button"
                    variant="outline"
                  >
                    <ListFilter className="h-4 w-4" />
                    Apply
                  </Button>
                ) : null}
                {isBroadeningAction ? (
                  <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
                    {sourceFilter ? (
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
              {filterAction ? (
                <div className="break-words rounded-md bg-muted px-2 py-1 text-xs font-semibold text-muted-foreground">
                  {filterFieldLabel(filterAction.field)}:{" "}
                  {formatFilterValue(filterAction.field, filterAction.value)}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
      {actions.length > 6 ? (
        <div className="text-xs font-semibold text-muted-foreground">
          Showing first 6 actions by backend priority.
        </div>
      ) : null}
    </div>
  );
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
  const { copiedKey, markCopied } = useCopyFeedback();
  const evaluationCopyKey = "judgment-evaluation-report";
  const evaluationCopied = copiedKey === evaluationCopyKey;

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
    markCopied(evaluationCopyKey);
  };

  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
          Judgment metrics
          <HelpTooltip label="Judgment metrics help">
            Metrics summarize how many ranked hits have human relevance labels and how useful the current ranking looks for this query.
          </HelpTooltip>
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
            <>
              <Button
                aria-label="Copy retrieval judgment evaluation report"
                onClick={() => void copyEvaluationReport()}
                size="sm"
                type="button"
                variant="outline"
              >
                {evaluationCopied ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  <Clipboard className="h-4 w-4" />
                )}
                {evaluationCopied ? "Copied" : "Copy evaluation JSON"}
              </Button>
              <HelpTooltip label="Judgment evaluation JSON report help">
                Copies server relevance metrics, local judgment coverage, stored-label summary, recommendations, and query-profile context for retrieval tuning notes.
              </HelpTooltip>
            </>
          ) : null}
        </div>
      </div>
      <SectionHelpText>
        Label top hits as relevant, partial, or not relevant. Coverage shows how much of the result set has labels; Precision@k and nDCG@k become meaningful only after enough judgments exist.
      </SectionHelpText>
      {persistedEvaluation ? (
        <EvaluationReadinessPanel evaluation={persistedEvaluation} />
      ) : null}
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

function EvaluationReadinessPanel({
  evaluation,
}: {
  evaluation: RetrievalJudgmentEvaluationResult;
}) {
  const readiness = evaluation.evaluation_readiness;
  return (
    <div
      aria-label="Judgment evaluation readiness"
      className={cn(
        "grid gap-2 rounded-md border p-3 text-sm",
        evaluationReadinessClass(readiness.status),
      )}
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 font-black">
          {readiness.status === "ready" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0" />
          ) : (
            <AlertTriangle className="h-4 w-4 shrink-0" />
          )}
          {readiness.label}
          <HelpTooltip label="Judgment readiness help">
            Readiness tells whether enough ranked hits have human labels for Precision@k, MAP@k, MRR@k, and nDCG@k to be useful for tuning.
          </HelpTooltip>
        </div>
        <Badge variant={evaluationReadinessVariant(readiness.status)}>
          {humanize(readiness.status)}
        </Badge>
      </div>
      <p className="break-words leading-6">{readiness.message}</p>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant="muted">
          min {formatCount(readiness.min_judged_count, "judged hit")}
        </Badge>
        <Badge variant="muted">
          min coverage {formatPercent(readiness.min_coverage_at_k)}
        </Badge>
      </div>
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

function EvidenceSupportMatrix({
  packageData,
  relevanceJudgments,
  runId,
}: {
  packageData: RetrievalPackage;
  relevanceJudgments: RelevanceJudgmentIndex;
  runId: string | null;
}) {
  const rows = evidenceSupportMatrixRows(packageData, relevanceJudgments, runId);
  if (!rows.length) return null;
  return (
    <section className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            <span>Evidence support matrix</span>
            <HelpTooltip label="Evidence support matrix help">
              Fast scan of whether each ranked hit has terms, provenance, concept grounding, query-aspect support, judgment state, and enough score support to trust for review.
            </HelpTooltip>
          </div>
          <div className="mt-1 text-sm font-semibold text-muted-foreground">
            Coverage, grounding, provenance, and review state for selected evidence.
          </div>
        </div>
        <Badge variant={rows.some((row) => row.supportStatus === "weak") ? "warning" : "success"}>
          {formatCount(rows.length, "evidence row")}
        </Badge>
      </div>
      <SectionHelpText>
        Weak rows need inspection before use. Missing provenance means the source locator is thin; missing concepts or aspects means the hit may match words without enough medical grounding.
      </SectionHelpText>
      <div className="grid gap-2 md:hidden">
        {rows.map((row) => (
          <EvidenceSupportMatrixCard key={row.evidenceId} row={row} />
        ))}
      </div>
      <div className="hidden overflow-auto rounded-md border border-border bg-card md:block">
        <Table>
          <THead>
            <TR>
              <TH>Rank</TH>
              <TH>Source</TH>
              <TH>Standard</TH>
              <TH>Evidence buckets</TH>
              <TH>Support</TH>
              <TH>Judgment</TH>
              <TH>Score</TH>
            </TR>
          </THead>
          <TBody>
            {rows.map((row) => (
              <TR key={row.evidenceId}>
                <TD className="font-mono text-xs font-bold">#{row.rank}</TD>
                <TD>
                  <div className="max-w-72 break-words font-bold">{row.sourceId}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {humanize(row.sourceType)} / {row.confidenceLabel}
                  </div>
                </TD>
                <TD>
                  {row.standardSystem ? (
                    <Badge variant="muted">{row.standardSystem}</Badge>
                  ) : (
                    <span className="text-xs font-semibold text-muted-foreground">-</span>
                  )}
                </TD>
                <TD>
                  <div className="flex min-w-52 flex-wrap gap-1">
                    {row.bucketLabels.length ? (
                      row.bucketLabels.map((label) => (
                        <Badge key={label} variant="muted">
                          {label}
                        </Badge>
                      ))
                    ) : (
                      <Badge variant="warning">No bucket</Badge>
                    )}
                  </div>
                </TD>
                <TD>
                  <div className="flex min-w-44 flex-wrap gap-1">
                    <Badge variant={row.matchedTermCount ? "success" : "warning"}>
                      {row.matchedTermCount} terms
                    </Badge>
                    <Badge variant={row.provenanceCount ? "success" : "warning"}>
                      {row.provenanceCount} provenance
                    </Badge>
                    <Badge variant={row.conceptCount ? "success" : "muted"}>
                      {row.conceptCount} concepts
                    </Badge>
                    <Badge variant={row.aspectCount ? "success" : "muted"}>
                      {row.aspectCount} aspects
                    </Badge>
                  </div>
                </TD>
                <TD>
                  {row.judgment ? (
                    <Badge variant={judgmentBadgeVariant(row.judgment.value)}>
                      {judgmentLabel(row.judgment.value)}
                    </Badge>
                  ) : (
                    <Badge variant="muted">Unjudged</Badge>
                  )}
                </TD>
                <TD>
                  <div className="font-mono text-xs font-bold">{formatScore(row.score)}</div>
                  <Badge variant={supportStatusBadgeVariant(row.supportStatus)}>
                    {humanize(row.supportStatus)}
                  </Badge>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </div>
    </section>
  );
}

function EvidenceSupportMatrixCard({ row }: { row: EvidenceSupportMatrixRow }) {
  return (
    <article className="grid min-w-0 gap-2 rounded-md border border-border bg-card p-3 text-sm">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Rank {row.rank}
          </div>
          <div className="mt-1 break-words font-black">{row.sourceId}</div>
          <div className="mt-1 text-xs font-semibold text-muted-foreground">
            {humanize(row.sourceType)} / {row.confidenceLabel}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap justify-end gap-1">
          <Badge variant={supportStatusBadgeVariant(row.supportStatus)}>
            {humanize(row.supportStatus)}
          </Badge>
          <Badge variant="muted">{formatScore(row.score)}</Badge>
        </div>
      </div>
      <div className="grid gap-2">
        <EvidenceSupportMobileField label="Standard">
          {row.standardSystem ? (
            <Badge variant="muted">{row.standardSystem}</Badge>
          ) : (
            <span className="text-xs font-semibold text-muted-foreground">Not specified</span>
          )}
        </EvidenceSupportMobileField>
        <EvidenceSupportMobileField label="Evidence buckets">
          <div className="flex min-w-0 flex-wrap gap-1">
            {row.bucketLabels.length ? (
              row.bucketLabels.map((label) => (
                <Badge key={label} variant="muted">
                  {label}
                </Badge>
              ))
            ) : (
              <Badge variant="warning">No bucket</Badge>
            )}
          </div>
        </EvidenceSupportMobileField>
        <EvidenceSupportMobileField label="Support">
          <div className="flex min-w-0 flex-wrap gap-1">
            <Badge variant={row.matchedTermCount ? "success" : "warning"}>
              {row.matchedTermCount} terms
            </Badge>
            <Badge variant={row.provenanceCount ? "success" : "warning"}>
              {row.provenanceCount} provenance
            </Badge>
            <Badge variant={row.conceptCount ? "success" : "muted"}>
              {row.conceptCount} concepts
            </Badge>
            <Badge variant={row.aspectCount ? "success" : "muted"}>
              {row.aspectCount} aspects
            </Badge>
          </div>
        </EvidenceSupportMobileField>
        <EvidenceSupportMobileField label="Judgment">
          {row.judgment ? (
            <Badge variant={judgmentBadgeVariant(row.judgment.value)}>
              {judgmentLabel(row.judgment.value)}
            </Badge>
          ) : (
            <Badge variant="muted">Unjudged</Badge>
          )}
        </EvidenceSupportMobileField>
      </div>
    </article>
  );
}

function EvidenceSupportMobileField({
  children,
  label,
}: {
  children: React.ReactNode;
  label: string;
}) {
  return (
    <div className="min-w-0 rounded-md bg-muted/45 px-2 py-1.5">
      <div className="text-[11px] font-black uppercase text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 min-w-0">{children}</div>
    </div>
  );
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

      {hit.snippet ? <SnippetBlock snippet={hit.snippet} /> : null}

      <p className="break-words text-sm leading-6 text-muted-foreground">
        {formatClaim(evidence.claim)}
      </p>

      <HitEvidenceAuditStrip summary={supportSummary} />

      <EvidenceUsabilitySummaryPanel summary={usabilitySummary} />

      <EvidenceUseGuidancePanel
        guidance={evidenceUseGuidance(supportSummary, matchExplanation, judgment)}
      />

      <HitMatchExplanationPanel explanation={matchExplanation} />

      <EvidenceProvenanceSummary entries={provenanceEntries} />

      <RelevanceJudgmentControl judgment={judgment} onSetJudgment={onSetJudgment} />

      <div className="grid gap-2 md:grid-cols-3">
        <ScoreMeter label="Lexical" value={hit.lexical_score} />
        <ScoreMeter label="Vector" value={hit.vector_score} />
        <ScoreMeter label="Rerank" value={hit.rerank_score} />
      </div>

      <ScoreExplanation components={scoreComponents} />

      <DiversitySelectionExplanation selection={diversitySelection} />

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

function HitEvidenceAuditStrip({
  summary,
}: {
  summary: EvidenceSupportSummary;
}) {
  return (
    <div
      aria-label="Evidence support summary"
      className="flex min-w-0 flex-wrap gap-1.5 rounded-md border border-border bg-muted/20 p-2"
    >
      <Badge variant={summary.matched_term_count ? "success" : "warning"}>
        {formatCount(summary.matched_term_count, "matched term")}
      </Badge>
      <Badge variant={summary.provenance_field_count ? "success" : "warning"}>
        {formatCount(summary.provenance_field_count, "provenance field")}
      </Badge>
      <Badge variant={summary.concept_count ? "success" : "muted"}>
        {formatCount(summary.concept_count, "grounded concept")}
      </Badge>
      <Badge variant={summary.aspect_count ? "success" : "muted"}>
        {formatCount(summary.aspect_count, "aspect")}
      </Badge>
      <Badge variant={summary.ranking_signal_count ? "success" : "muted"}>
        {formatCount(summary.ranking_signal_count, "ranking signal")}
      </Badge>
    </div>
  );
}

function EvidenceUsabilitySummaryPanel({
  summary,
}: {
  summary: EvidenceUsabilitySummary;
}) {
  return (
    <section
      aria-label="Evidence usability summary"
      className="grid gap-2 rounded-md border border-border bg-muted/20 p-2 text-sm"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="grid min-w-0 gap-1">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Usability summary
          </div>
          <div className="break-words font-semibold">{summary.headline}</div>
        </div>
        <Badge variant={supportStatusBadgeVariant(summary.status)}>
          {humanize(summary.status)}
        </Badge>
      </div>
      <div className="grid gap-1.5 sm:grid-cols-2">
        <div className="rounded-md border border-border bg-card/70 px-2 py-1.5">
          <div className="text-[11px] font-black uppercase text-muted-foreground">
            Recommendation
          </div>
          <div className="mt-1 break-words font-semibold">
            {summary.recommendation}
          </div>
        </div>
        <div className="rounded-md border border-border bg-card/70 px-2 py-1.5">
          <div className="text-[11px] font-black uppercase text-muted-foreground">
            Limitation
          </div>
          <div className="mt-1 break-words text-muted-foreground">
            {summary.limitation}
          </div>
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {summary.checks.map((check) => (
          <Badge className="max-w-full break-words" key={check} variant="muted">
            {check}
          </Badge>
        ))}
      </div>
    </section>
  );
}

function EvidenceUseGuidancePanel({
  guidance,
}: {
  guidance: EvidenceUseGuidance;
}) {
  const Icon = guidance.status === "strong" ? CheckCircle2 : AlertTriangle;
  return (
    <div
      aria-label="Evidence interpretation guidance"
      className={cn(
        "grid gap-2 rounded-md border p-2 text-sm",
        guidance.status === "strong"
          ? "border-emerald-200 bg-emerald-50 text-emerald-950"
          : guidance.status === "partial"
            ? "border-amber-200 bg-amber-50 text-amber-950"
            : "border-red-200 bg-red-50 text-red-950",
      )}
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex min-w-0 items-center gap-2 font-black">
          <Icon className="h-4 w-4 shrink-0" />
          <span>{guidance.title}</span>
          <HelpTooltip label="Evidence interpretation help">
            This is a data-derived operator guide for the evidence card. It summarizes whether the hit has enough terms, provenance, medical grounding, and judgment state for review.
          </HelpTooltip>
        </div>
        <Badge variant={supportStatusBadgeVariant(guidance.status)}>
          {humanize(guidance.status)}
        </Badge>
      </div>
      <div className="break-words font-semibold leading-6">{guidance.action}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {guidance.reasons.map((reason) => (
          <Badge className="max-w-full break-words" key={reason} variant="muted">
            {reason}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function HitMatchExplanationPanel({
  explanation,
}: {
  explanation: HitMatchExplanation;
}) {
  return (
    <div
      aria-label="Why this evidence matched"
      className="grid gap-2 rounded-md border border-border bg-muted/20 p-2"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
          <BrainCircuit className="h-3.5 w-3.5 shrink-0" />
          <span>Why this matched</span>
        </div>
        <Badge variant={supportStatusBadgeVariant(explanation.supportStatus)}>
          {humanize(explanation.supportStatus)}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <MatchExplanationMetric
          label="Top driver"
          value={explanation.topScoreDriver ?? "not reported"}
        />
        <MatchExplanationMetric
          label="Evidence pack"
          value={
            explanation.bucketLabels.length
              ? explanation.bucketLabels.join(", ")
              : "unbucketed"
          }
        />
        <MatchExplanationMetric
          label="Terms"
          value={
            explanation.matchedTerms.length
              ? explanation.matchedTerms.join(", ")
              : "no exact terms"
          }
        />
        <MatchExplanationMetric
          label="Traceability"
          value={`${formatCount(explanation.provenanceCount, "provenance field")}, ${formatCount(
            explanation.rankingSignalCount,
            "ranking signal",
          )}`}
        />
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {explanation.conceptLabels.map((label) => (
          <Badge className="max-w-full break-words" key={`concept-${label}`} variant="muted">
            {label}
          </Badge>
        ))}
        {explanation.aspectLabels.map((label) => (
          <Badge className="max-w-full break-words" key={`aspect-${label}`} variant="muted">
            {label}
          </Badge>
        ))}
        {!explanation.conceptLabels.length && !explanation.aspectLabels.length ? (
          <span className="text-xs font-semibold text-muted-foreground">
            No concept or query-aspect grounding was reported for this hit.
          </span>
        ) : null}
      </div>
    </div>
  );
}

function MatchExplanationMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs">
      <span className="font-bold text-muted-foreground">{label}</span>
      <span className="min-w-0 break-words font-semibold">{value}</span>
    </div>
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
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
          Relevance judgment
          <HelpTooltip label="Relevance judgment help">
            Mark whether this evidence actually answers the submitted search. These labels feed judgment metrics and comparison reports.
          </HelpTooltip>
        </div>
        {judgment ? (
          <Badge variant={judgmentBadgeVariant(judgment.value)}>
            {judgmentLabel(judgment.value)}
          </Badge>
        ) : (
          <Badge variant="muted">unjudged</Badge>
        )}
      </div>
      <SectionHelpText>
        Use relevant for direct support, partial for useful but incomplete support, and not relevant when the hit does not answer the query.
      </SectionHelpText>
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

function EvidenceProvenanceSummary({
  entries,
}: {
  entries: EvidenceProvenanceEntry[];
}) {
  if (!entries.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
          <span>Evidence provenance</span>
        </div>
        <Badge variant="muted">{formatCount(entries.length, "field")}</Badge>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {entries.map((entry) => (
          <span
            className="inline-flex max-w-full items-center gap-1 rounded-full border border-border bg-card/70 px-2 py-1 text-xs font-semibold text-muted-foreground"
            key={`${entry.label}-${entry.value}`}
          >
            <span className="shrink-0 font-bold text-foreground">{entry.label}:</span>
            {entry.href ? (
              <a
                className="inline-flex min-w-0 items-center gap-1 break-words text-primary underline-offset-2 hover:underline"
                href={entry.href}
                rel="noopener noreferrer"
                target="_blank"
              >
                <span className="min-w-0 break-words">{entry.value}</span>
                <ExternalLink className="h-3 w-3 shrink-0" />
              </a>
            ) : (
              <span className="min-w-0 break-words">{entry.value}</span>
            )}
          </span>
        ))}
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

function ConceptMatchExplanation({ matches }: { matches: ConceptMatchSignal[] }) {
  if (!matches.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Network className="h-3.5 w-3.5 shrink-0" />
        <span>Concept grounding</span>
      </div>
      <div className="grid gap-1.5">
        {matches.map((match) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs"
            key={`${match.standardSystem}-${match.conceptId}`}
          >
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge className="max-w-full break-words" variant="success">
                {match.standardSystem}
                {match.code ? ` ${match.code}` : ""}
              </Badge>
              <span className="min-w-0 break-words font-bold">{match.displayName}</span>
              <span className="font-mono font-semibold text-muted-foreground">
                {Math.round(match.confidence * 100)}%
              </span>
            </div>
            <div className="break-words font-semibold text-muted-foreground">
              {match.reason}
            </div>
            <div className="flex min-w-0 flex-wrap gap-1">
              {match.matchedFields.map((field) => (
                <span
                  className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                  key={`${match.conceptId}-${field}`}
                >
                  {humanize(field)}
                </span>
              ))}
              {match.matchedAliases.slice(0, 3).map((alias) => (
                <span
                  className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                  key={`${match.conceptId}-${alias}`}
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
  activeFilters,
  isSearchPending,
  onApplyCoverageFilter,
  onClearAllFilters,
  onClearFilter,
  onApplyFilterSuggestion,
  packageData,
}: {
  activeFilters: ActiveFilterEntry[];
  isSearchPending: boolean;
  onApplyCoverageFilter: (field: SupportedFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
  packageData: RetrievalPackage | undefined;
}) {
  const trace = packageData?.trace;
  const stack = packageData ? rankingStackFromPackage(packageData) : null;
  const diversity = packageData ? diversityFromPackage(packageData) : null;
  const qualityPolicy = packageData ? qualityPolicyFromPackage(packageData) : null;
  const queryAnalysis = packageData ? queryAnalysisFromPackage(packageData) : null;
  const searchSignature = packageData ? serverSearchSignatureFromPackage(packageData) : null;
  const coverage = packageData?.coverage;
  const qualitySignals = packageData?.quality_signals ?? [];
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle className="flex items-center gap-2">
          <ListFilter className="h-5 w-5 text-primary" />
          Retrieval trace
          <HelpTooltip label="Retrieval trace help">
            Trace shows how the backend transformed the query, which filters were applied, and which quality or safety issues affected the evidence package.
          </HelpTooltip>
        </CardTitle>
        <CardDescription>Query route, rewrites, filters, warnings, and quality diagnostics.</CardDescription>
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
              label="Search signature"
              value={searchSignature ? formatShortSignature(searchSignature) : "unknown"}
            />
            <TraceFact
              label="Filters"
              value={Object.keys(trace.filters_applied).length ? JSON.stringify(trace.filters_applied) : "none"}
            />
            <QualitySignalList signals={qualitySignals} />
            <RecommendedActionsPanel
              activeFilters={activeFilters}
              actions={packageData.recommended_actions ?? []}
              isSearchPending={isSearchPending}
              onApplyFilter={onApplyCoverageFilter}
              onClearAllFilters={onClearAllFilters}
              onClearFilter={onClearFilter}
            />
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
            <TokenList
              description="Safety-sensitive context detected in the retrieval request. Treat query text as untrusted data."
              items={trace.safety_flags.map(humanize)}
              title="Safety flags"
              tone="warning"
            />
            <TokenList
              description="Backend warnings about search coverage, fallbacks, or risky context."
              items={trace.warnings}
              title="Warnings"
              tone="warning"
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}

function QualitySignalList({ signals }: { signals: RetrievalQualitySignal[] }) {
  if (!signals.length) {
    return (
      <TokenList
        description="Backend quality checks did not return warnings or blockers."
        items={[]}
        title="Retrieval quality"
      />
    );
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
      <SectionHelpText>
        Quality signals explain why the evidence package is ready, needs review, or is blocked.
      </SectionHelpText>
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
              <QualitySignalMetadataDetails signal={signal} />
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

function QualitySignalMetadataDetails({ signal }: { signal: RetrievalQualitySignal }) {
  const details = qualitySignalMetadataDetails(signal);
  if (!details.length) return null;
  return (
    <div className="grid gap-1.5 rounded-md border border-border bg-muted/20 p-2">
      <div className="text-[11px] font-bold uppercase text-muted-foreground">
        Signal details
      </div>
      <div className="grid gap-1.5">
        {details.map((detail) => (
          <div className="grid gap-1" key={detail.label}>
            <span className="font-bold text-muted-foreground">{detail.label}</span>
            <div className="flex min-w-0 flex-wrap gap-1">
              {detail.values.map((value) => (
                <Badge
                  className="max-w-full break-words text-left"
                  key={`${detail.label}-${value}`}
                  variant={detail.variant}
                >
                  {value}
                </Badge>
              ))}
            </div>
          </div>
        ))}
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
    return (
      <TokenList
        description="No missing standard or search-aspect coverage was reported."
        items={[]}
        title="Coverage diagnostics"
      />
    );
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
      <SectionHelpText>
        Coverage diagnostics show missing standards or query aspects and offer backend-supported filters when available.
      </SectionHelpText>
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
    return (
      <TokenList
        description="No query rewrite variants were generated for this search."
        items={[]}
        title="Query rewrites"
      />
    );
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Query rewrites
      </div>
      <SectionHelpText>
        Query rewrites are backend-generated search variants. They improve recall but do not change the submitted payload.
      </SectionHelpText>
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
  const { copiedKey, clearCopied, markCopied } = useCopyFeedback();

  const copyHintQuery = async (hintKey: string, query: string) => {
    try {
      await copyTextToClipboard(query);
      markCopied(hintKey);
    } catch {
      clearCopied();
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
          const copied = copiedKey === hintKey;
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
              <SearchHintMetadata metadata={hint.metadata} />
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

function SearchHintMetadata({ metadata }: { metadata: Record<string, unknown> }) {
  const parameterExamples = searchHintParameterExamples(metadata.parameter_examples);
  const lineageFollowup = searchHintLineageFollowup(metadata.lineage_followup);
  const scopeEndpoints = stringArrayValue(metadata.scope_endpoints);
  const selectedTerms = stringArrayValue(metadata.selected_terms);
  const selectedUnitCandidates = stringArrayValue(metadata.selected_unit_candidates);
  const selectedCandidates = selectedTerms.length ? selectedTerms : selectedUnitCandidates;
  const selectedCandidateTitle = selectedTerms.length ? "Selected terminology terms" : "Selected unit candidates";
  const capabilityWarning = optionalStringValue(metadata.capability_warning);
  if (
    !parameterExamples.length &&
    !lineageFollowup.length &&
    !scopeEndpoints.length &&
    !selectedCandidates.length &&
    !capabilityWarning
  ) {
    return null;
  }
  return (
    <details className="rounded-md border border-border bg-muted/20">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-1.5 px-2 py-1.5 font-black">
        Route details
        {parameterExamples.length ? (
          <Badge variant="muted">{formatCount(parameterExamples.length, "parameter")}</Badge>
        ) : null}
        {scopeEndpoints.length ? <Badge variant="muted">scoped API</Badge> : null}
        {selectedCandidates.length ? (
          <Badge variant="success">{formatCount(selectedCandidates.length, "candidate")}</Badge>
        ) : null}
        {lineageFollowup.length ? <Badge variant="warning">lineage</Badge> : null}
      </summary>
      <div className="grid gap-2 border-t border-border p-2">
        {scopeEndpoints.length ? (
          <div className="grid gap-1.5">
            <div className="font-black uppercase text-muted-foreground">
              Endpoint scope
            </div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {scopeEndpoints.slice(0, 6).map((endpoint) => (
                <code
                  className="rounded border border-border bg-card px-1.5 py-0.5 font-mono text-[11px]"
                  key={endpoint}
                >
                  {endpoint}
                </code>
              ))}
            </div>
          </div>
        ) : null}
        {selectedCandidates.length ? (
          <div className="grid gap-1.5">
            <div className="font-black uppercase text-muted-foreground">
              {selectedCandidateTitle}
            </div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {selectedCandidates.slice(0, 8).map((candidate) => (
                <Badge key={candidate} variant="success">
                  {candidate}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}
        {parameterExamples.length ? (
          <div className="grid gap-1.5">
            <div className="font-black uppercase text-muted-foreground">
              Parameter examples
            </div>
            {parameterExamples.map((example) => (
              <div
                className="grid gap-1 rounded-md border border-border bg-card px-2 py-1.5"
                key={`${example.name}:${example.example}`}
              >
                <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                  <Badge variant={example.matchedDatasetField ? "success" : "muted"}>
                    {example.name}
                  </Badge>
                  <span className="break-words text-muted-foreground">
                    {example.targetField}
                  </span>
                </div>
                <code className="break-words font-mono text-[11px]">{example.example}</code>
              </div>
            ))}
          </div>
        ) : null}
        {lineageFollowup.length ? (
          <div className="grid gap-1.5">
            <div className="font-black uppercase text-muted-foreground">
              Lineage follow-up
            </div>
            {lineageFollowup.map((item) => (
              <div
                className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-1.5 text-amber-950"
                key={item.parameter}
              >
                <code className="break-words font-mono text-[11px]">{item.parameter}</code>
                <div className="break-words text-[11px] leading-5">{item.purpose}</div>
              </div>
            ))}
          </div>
        ) : null}
        {capabilityWarning ? (
          <div className="rounded-md border border-border bg-card px-2 py-1.5 text-[11px] font-semibold leading-5 text-muted-foreground">
            {capabilityWarning}
          </div>
        ) : null}
      </div>
    </details>
  );
}

function QueryDiagnosticList({
  diagnostics,
}: {
  diagnostics: QueryDiagnosticStack[];
}) {
  if (!diagnostics.length) {
    return (
      <TokenList
        description="No query diagnostic warnings were emitted."
        items={[]}
        title="Query diagnostics"
      />
    );
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Query diagnostics
      </div>
      <SectionHelpText>
        Query diagnostics explain parser, expansion, and safety issues detected before ranking.
      </SectionHelpText>
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
            <DiagnosticMetadataChips metadata={diagnostic.metadata} />
            <div className="break-words font-semibold text-foreground">
              {diagnostic.suggestedAction}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DiagnosticMetadataChips({ metadata }: { metadata: Record<string, unknown> }) {
  const activeFilters = stringArrayValue(metadata.active_metadata_filters);
  const suggestedStandards = stringArrayValue(metadata.suggested_standards);
  const appliedStandard = optionalStringValue(metadata.applied_standard);
  const tokenCount = numberValue(metadata.query_token_count);
  const filterCount = numberValue(metadata.active_metadata_filter_count);
  const chips = [
    tokenCount !== null ? `${tokenCount} query token${tokenCount === 1 ? "" : "s"}` : "",
    filterCount !== null ? `${filterCount} active filter${filterCount === 1 ? "" : "s"}` : "",
    appliedStandard ? `applied ${appliedStandard}` : "",
    suggestedStandards.length ? `suggested ${suggestedStandards.join(", ")}` : "",
    activeFilters.length ? `filters ${activeFilters.join(", ")}` : "",
  ].filter(Boolean);
  if (!chips.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap gap-1">
      {chips.map((chip) => (
        <Badge className="max-w-full break-words" key={chip} variant="muted">
          {chip}
        </Badge>
      ))}
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
                  {relation.count} {humanize(relation.relation)}
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
                        <div className="break-words text-sm font-black">{node.normalized_display ?? node.label}</div>
                        <div className="mt-0.5 break-words font-mono text-xs text-muted-foreground">
                          {node.normalized_code}
                        </div>
                      </div>
                      <Badge variant="success">{node.normalized_system ?? "code"}</Badge>
                    </div>
                    <div className="mt-2 flex min-w-0 flex-wrap gap-1.5 text-xs">
                      {node.clinical_domain ? <Badge variant="muted">{humanize(node.clinical_domain)}</Badge> : null}
                      {node.matched_text ? <Badge variant="muted">matched {node.matched_text}</Badge> : null}
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
                    <Badge variant="muted">{humanize(triple.predicate)}</Badge>
                  </div>
                  <div className="break-words text-sm text-muted-foreground">
                    {triple.object}
                  </div>
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
        <Badge variant={graphNodeBadgeVariant(node.type)}>{humanize(node.type)}</Badge>
      </div>
      <div className="mt-2 flex min-w-0 flex-wrap gap-1.5 text-xs">
        {node.rule_source ? <Badge variant="muted">{humanize(node.rule_source)}</Badge> : null}
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

function evaluationReadinessVariant(
  status: string,
): "success" | "warning" | "destructive" | "muted" {
  if (status === "ready") return "success";
  if (status === "unlabeled") return "destructive";
  if (status === "low_confidence" || status === "usable_with_gaps") return "warning";
  return "muted";
}

function evaluationReadinessClass(status: string): string {
  if (status === "ready") return "border-emerald-200 bg-emerald-50 text-emerald-950";
  if (status === "unlabeled") return "border-red-200 bg-red-50 text-red-950";
  if (status === "low_confidence" || status === "usable_with_gaps") {
    return "border-amber-200 bg-amber-50 text-amber-950";
  }
  return "border-border bg-card text-card-foreground";
}

function SourceScopePicker({
  isSearchPending,
  onClear,
  onSelect,
  selectedSource,
  sourceId,
  sources,
}: {
  isSearchPending: boolean;
  onClear: () => void;
  onSelect: (sourceId: string) => void;
  selectedSource: RetrievalSource | null;
  sourceId: string;
  sources: RetrievalSource[];
}) {
  const [search, setSearch] = React.useState("");
  const visibleSources = sources
    .filter((source) =>
      sourceMatchesInventoryFilters(source, {
        domain: null,
        search,
        standard: null,
        type: null,
      }),
    )
    .slice(0, 8);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
            Exact source scope
            <HelpTooltip label="Exact source scope help">
              Exact source scope reruns retrieval against one source ID. Use it for audit or source-specific debugging, not broad evidence discovery.
            </HelpTooltip>
          </div>
          <div className="mt-1 break-words text-sm font-semibold text-muted-foreground">
            {sourceId
              ? selectedSource?.title ?? sourceId
              : `${formatCount(sources.length, "approved source")} available`}
          </div>
        </div>
        {sourceId ? (
          <Button
            disabled={isSearchPending}
            onClick={onClear}
            size="sm"
            type="button"
            variant="outline"
          >
            <X className="h-4 w-4" />
            Clear source
          </Button>
        ) : null}
      </div>
      <div
        className={cn(
          "flex min-w-0 items-start gap-2 rounded-md border px-3 py-2 text-xs leading-5",
          sourceId
            ? "border-amber-200 bg-amber-50 text-amber-950"
            : "border-border bg-card text-muted-foreground",
        )}
      >
        {sourceId ? (
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-700" />
        ) : (
          <Search className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
        )}
        <span className="min-w-0 break-words font-semibold">
          {sourceId
            ? "Search is constrained to one exact source. Clear it before judging corpus-wide evidence coverage."
            : "Leave exact source blank for broad search. Pick a source only when you need source-specific evidence."}
        </span>
      </div>
      {sourceId ? (
        <div className="grid gap-1 rounded-md border border-primary/25 bg-primary/10 p-2 text-sm">
          <div className="font-bold">{selectedSource?.title ?? sourceId}</div>
          <div className="break-all font-mono text-xs text-muted-foreground">{sourceId}</div>
          {selectedSource ? (
            <div className="flex min-w-0 flex-wrap gap-1.5">
              <Badge variant="muted">{humanize(selectedSource.source_type)}</Badge>
              {selectedSource.clinical_domain ? (
                <Badge variant="muted">{humanize(selectedSource.clinical_domain)}</Badge>
              ) : null}
              {selectedSource.standard_system ? (
                <Badge variant="muted">{selectedSource.standard_system}</Badge>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
      <Input
        aria-label="Search exact source scope"
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search source ID, title, type, domain, or standard"
        value={search}
      />
      <div className="grid gap-1.5">
        {visibleSources.map((source) => (
          <button
            className={cn(
              "grid min-w-0 gap-1 rounded-md border px-3 py-2 text-left text-sm transition-colors",
              source.source_id === sourceId
                ? "border-primary bg-primary/10"
                : "border-border bg-card hover:border-primary hover:bg-primary/5",
            )}
            disabled={isSearchPending}
            key={source.source_id}
            onClick={() => onSelect(source.source_id)}
            type="button"
            >
              <span className="break-words font-bold">{source.title}</span>
              {source.source_id === sourceId ? (
                <Badge className="w-fit" variant="success">
                  applied exact source
                </Badge>
              ) : null}
              <span className="break-all font-mono text-xs text-muted-foreground">
                {source.source_id}
            </span>
            <span className="flex min-w-0 flex-wrap gap-1.5">
              <Badge variant="muted">{humanize(source.source_type)}</Badge>
              {source.clinical_domain ? (
                <Badge variant="muted">{humanize(source.clinical_domain)}</Badge>
              ) : null}
              {source.standard_system ? (
                <Badge variant="muted">{source.standard_system}</Badge>
              ) : null}
              <Badge variant="muted">{formatCount(source.chunk_count, "chunk")}</Badge>
            </span>
          </button>
        ))}
        {!visibleSources.length ? (
          <div className="rounded-md border border-border bg-card p-3 text-sm text-muted-foreground">
            {sources.length ? "No source matches this search." : "No retrieval sources loaded."}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function SourcesPanel({
  isLoading,
  onUseSource,
  sources,
}: {
  isLoading: boolean;
  onUseSource: (sourceId: string) => void;
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
  const readiness = sourceInventoryReadiness(sources, filteredSources);
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
          <CardTitle className="flex items-center gap-2">
            Trusted sources
            <HelpTooltip label="Trusted sources help">
              Source inventory shows what the retrieval system can search. The Use source action applies exact source scope to the query builder.
            </HelpTooltip>
          </CardTitle>
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
        <SectionHelpText>
          Inventory filters only inspect available sources. Use source constrains retrieval to one source ID; clear exact source scope for corpus-wide coverage.
        </SectionHelpText>
        <SourceInventoryReadinessPanel
          hasSourceFilters={hasSourceFilters}
          readiness={readiness}
        />
        <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
              Source inventory filters
              <HelpTooltip label="Source inventory filters help">
                Inventory filters inspect available trusted sources. Use source scope only when you intentionally want evidence from one exact source.
              </HelpTooltip>
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
        <div className="grid gap-3">
          {filteredSources.map((source) => (
            <SourceCard key={source.source_id} onUseSource={onUseSource} source={source} />
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

function SourceInventoryReadinessPanel({
  hasSourceFilters,
  readiness,
}: {
  hasSourceFilters: boolean;
  readiness: SourceInventoryReadiness;
}) {
  const blocked = readiness.readiness === "blocked";
  const review = readiness.readiness === "review";
  return (
    <div
      aria-label="Source inventory readiness"
      className={cn(
        "grid gap-2 rounded-md border p-3",
        blocked
          ? "border-red-200 bg-red-50 text-red-950"
          : review
            ? "border-amber-200 bg-amber-50 text-amber-950"
            : "border-emerald-200 bg-emerald-50 text-emerald-950",
      )}
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase">
          Source readiness
          <HelpTooltip label="Source readiness help">
            Summarizes whether the trusted corpus has searchable sources, chunks, domains, and standards before you apply exact source scope.
          </HelpTooltip>
        </div>
        <Badge variant={sourceInventoryReadinessVariant(readiness.readiness)}>
          {humanize(readiness.readiness)}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <SourceReadinessMetric label="Sources" value={`${readiness.filteredCount}/${readiness.sourceCount}`} />
        <SourceReadinessMetric label="Chunks" value={formatCount(readiness.chunkCount, "chunk")} />
        <SourceReadinessMetric label="Domains" value={formatCount(readiness.domainCount, "domain")} />
        <SourceReadinessMetric label="Standards" value={formatCount(readiness.standardCount, "standard")} />
      </div>
      <div className="break-words text-sm font-semibold leading-6">
        {sourceInventoryReadinessMessage(readiness, hasSourceFilters)}
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant={readiness.sourceTypeCount ? "success" : "warning"}>
          {formatCount(readiness.sourceTypeCount, "source type")}
        </Badge>
        <Badge variant={readiness.emptySourceCount ? "warning" : "success"}>
          {readiness.emptySourceCount
            ? formatCount(readiness.emptySourceCount, "empty source")
            : "all shown sources have chunks"}
        </Badge>
        {hasSourceFilters ? <Badge variant="warning">filtered inventory</Badge> : null}
      </div>
    </div>
  );
}

function SourceReadinessMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-card/80 px-3 py-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 break-words text-sm font-black">{value}</div>
    </div>
  );
}

function SourceCard({
  onUseSource,
  source,
}: {
  onUseSource: (sourceId: string) => void;
  source: RetrievalSource;
}) {
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
      <Button
        className="w-fit"
        onClick={() => onUseSource(source.source_id)}
        size="sm"
        type="button"
        variant="outline"
      >
        <Search className="h-4 w-4" />
        Use source
      </Button>
    </article>
  );
}

function sourceInventoryReadiness(
  sources: RetrievalSource[],
  filteredSources: RetrievalSource[],
): SourceInventoryReadiness {
  const chunkCount = filteredSources.reduce((count, source) => count + source.chunk_count, 0);
  const emptySourceCount = filteredSources.filter((source) => source.chunk_count <= 0).length;
  const readiness =
    !sources.length || !filteredSources.length || chunkCount <= 0
      ? "blocked"
      : emptySourceCount > 0 || filteredSources.length < sources.length
        ? "review"
        : "ready";
  return {
    chunkCount,
    domainCount: uniqueValues(filteredSources.map((source) => source.clinical_domain)).length,
    emptySourceCount,
    filteredCount: filteredSources.length,
    readiness,
    sourceCount: sources.length,
    sourceTypeCount: uniqueValues(filteredSources.map((source) => source.source_type)).length,
    standardCount: uniqueValues(filteredSources.map((source) => source.standard_system)).length,
  };
}

function sourceInventoryReadinessVariant(
  readiness: SourceInventoryReadiness["readiness"],
): "success" | "warning" | "destructive" {
  if (readiness === "ready") return "success";
  if (readiness === "review") return "warning";
  return "destructive";
}

function sourceInventoryReadinessMessage(
  readiness: SourceInventoryReadiness,
  hasSourceFilters: boolean,
): string {
  if (!readiness.sourceCount) {
    return "No trusted sources are loaded. Reindex the corpus before judging retrieval quality.";
  }
  if (!readiness.filteredCount) {
    return "No trusted sources match the current inventory filters. Clear filters before concluding the corpus lacks coverage.";
  }
  if (!readiness.chunkCount) {
    return "Matching sources have no indexed chunks. Refresh or reindex before relying on retrieval results.";
  }
  if (hasSourceFilters) {
    return "Inventory is filtered. Use this view to inspect available source types, but clear filters for corpus-wide coverage checks.";
  }
  if (readiness.emptySourceCount) {
    return "Some trusted sources have no indexed chunks. Review index integrity before using exact source scope.";
  }
  return "Trusted source inventory is searchable. Use exact source scope only for audit or source-specific debugging.";
}

function TokenList({
  description,
  items,
  title,
  tone = "neutral",
}: {
  description?: string;
  items: string[];
  title: string;
  tone?: "neutral" | "warning";
}) {
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">{title}</div>
      {description ? <SectionHelpText>{description}</SectionHelpText> : null}
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

function SectionHelpText({ children }: { children: React.ReactNode }) {
  return (
    <p className="break-words text-xs font-semibold leading-5 text-muted-foreground">
      {children}
    </p>
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
  metadata: Record<string, unknown>;
  query: string;
  rationale: string;
  target: string;
  url: string | null;
  warnings: string[];
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
type EvidenceProvenanceEntry = {
  href: string | null;
  label: string;
  value: string;
};
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

function qualitySignalMetadataDetails(signal: RetrievalQualitySignal): Array<{
  label: string;
  values: string[];
  variant: "success" | "warning" | "destructive" | "muted";
}> {
  const metadata = recordValue(signal.metadata);
  const details: Array<{
    label: string;
    values: string[];
    variant: "success" | "warning" | "destructive" | "muted";
  }> = [];
  const missingConcepts = conceptMetadataValues(metadata.missing_concepts);
  if (missingConcepts.length) {
    details.push({
      label: "Missing concepts",
      values: missingConcepts,
      variant: "warning",
    });
  }
  const provenanceIssues = provenanceIssueMetadataValues(metadata.issues);
  if (provenanceIssues.length) {
    details.push({
      label: "Provenance issues",
      values: provenanceIssues,
      variant: "warning",
    });
  }
  const missingStandards = stringArrayValue(metadata.missing_standards);
  if (missingStandards.length) {
    details.push({
      label: "Missing standards",
      values: missingStandards,
      variant: "warning",
    });
  }
  const missingAspects = stringArrayValue(metadata.missing_aspects).map(humanize);
  if (missingAspects.length) {
    details.push({
      label: "Missing aspects",
      values: missingAspects,
      variant: "warning",
    });
  }
  const suggestedFilters = suggestedFilterMetadataValues(metadata.suggested_filters);
  if (suggestedFilters.length) {
    details.push({
      label: "Suggested filters",
      values: suggestedFilters,
      variant: "muted",
    });
  }
  return details;
}

function conceptMetadataValues(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((concept) => {
      const standard = stringValue(concept.standard_system, "standard");
      const code = optionalStringValue(concept.code);
      const name = stringValue(concept.display_name, stringValue(concept.concept_id, "concept"));
      const confidence = numberValue(concept.confidence);
      const confidenceText = confidence === null ? "" : ` / ${Math.round(confidence * 100)}%`;
      return `${standard}${code ? ` ${code}` : ""}: ${name}${confidenceText}`;
    })
    .filter(Boolean);
}

function provenanceIssueMetadataValues(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((issue) => {
      const sourceId = stringValue(issue.source_id, "source");
      const missing = stringArrayValue(issue.missing).map(humanize);
      return `${sourceId}: missing ${missing.length ? missing.join(", ") : "metadata"}`;
    })
    .filter(Boolean);
}

function suggestedFilterMetadataValues(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .flatMap((filter) =>
      Object.entries(filter)
        .map(([field, rawValue]) => {
          const value = stringValue(rawValue, "");
          return value ? `${humanize(field)}=${value}` : "";
        })
        .filter(Boolean),
    );
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
    filters: {
      source_id: form.sourceId || null,
    },
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

function searchRunScopeLabels(payload: RetrievalSearchPayload): string[] {
  return [
    payload.schema_id ? `schema ${payload.schema_id}` : null,
    payload.detected_format ? `format ${humanize(payload.detected_format)}` : null,
    payload.resource_type ? `resource ${payload.resource_type}` : null,
    payload.clinical_domain ? `domain ${humanize(payload.clinical_domain)}` : null,
    payload.standard_system ? `standard ${payload.standard_system}` : null,
    payload.source_type ? `source ${humanize(payload.source_type)}` : null,
    payload.filters?.source_id ? `source ID ${payload.filters.source_id}` : null,
    payload.trust_level ? `trust ${humanize(payload.trust_level)}` : null,
    payload.fields.length ? formatCount(payload.fields.length, "field") : null,
  ].filter((label): label is string => Boolean(label));
}

function searchRunQualityBadgeVariant(
  summary: RetrievalQualitySummary,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
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

function formatRunTime(submittedAt: string): string {
  const date = new Date(submittedAt);
  if (Number.isNaN(date.getTime())) return "recent";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatShortSignature(signature: string): string {
  const digest = signature.includes(":") ? signature.split(":").pop() ?? signature : signature;
  return `sig ${digest.slice(0, 10)}`;
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
