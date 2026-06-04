export type ApiEnvelope<T> = {
  data: T | null;
  error: ApiError | null;
  meta?: Record<string, unknown>;
};

export type ApiError = {
  code: string;
  message: string;
  details: Record<string, unknown>;
  workflow_id?: string | null;
};

export type AuthUser = {
  user_id: string;
  email: string;
  email_verified: boolean;
  display_name?: string | null;
  avatar_url?: string | null;
};

export type AuthLoginResponse = {
  expires_at: string;
  user: AuthUser;
};

export type AuthSessionResponse = {
  user: AuthUser;
  session: {
    session_id: string;
    expires_at: string;
    last_seen_at?: string | null;
  };
};

export type WorkflowStatus =
  | "created"
  | "running"
  | "needs_human_review"
  | "approved"
  | "rejected"
  | "completed"
  | "failed"
  | "cancelled";

export type ReviewStatus =
  | "pending"
  | "approved"
  | "approved_with_edits"
  | "rejected"
  | "clarification_requested"
  | "cancelled";

export type ClarificationRequest = {
  requested_by?: string | null;
  requested_at?: string | null;
  payload: Record<string, unknown>;
};

export type WorkflowStep = {
  step_id: string;
  name: string;
  status: string;
  started_at: string;
  completed_at?: string | null;
  summary: string;
  output_ref?: string | null;
  issue_count: number;
};

export type WorkflowFailure = {
  code: string;
  message: string;
  error_type: string;
  details: Record<string, unknown>;
  failed_at: string;
};

export type ValidationIssue = {
  issue_id: string;
  kind: string;
  severity: string;
  message: string;
  location?: {
    row?: number | null;
    column?: string | null;
    field?: string | null;
    source_ref?: string | null;
  } | null;
  suggested_action?: string | null;
  requires_review: boolean;
};

export type Evidence = {
  evidence_id: string;
  source_type: string;
  source_id: string;
  claim: string;
  source_version?: string | null;
  locator: Record<string, unknown>;
  confidence?: number | null;
  trust_level: string;
};

export type RetrievalTrace = {
  strategy: string;
  query_variants: string[];
  query_variant_details?: RetrievalQueryVariant[];
  filters_applied: Record<string, unknown>;
  candidates_seen: number;
  final_hit_ids: string[];
  safety_flags: string[];
  warnings: string[];
};

export type RetrievalQueryVariant = {
  variant: string;
  source: string;
  reason: string;
  metadata: Record<string, unknown>;
};

export type RetrievalHit = {
  evidence: Evidence;
  score: number;
  lexical_score: number;
  vector_score: number;
  rerank_score: number;
  score_components: RetrievalScoreComponent[];
  matched_terms: string[];
  source_locator: Record<string, unknown>;
  snippet?: RetrievalSnippet | null;
};

export type RetrievalScoreComponent = {
  component: string;
  label: string;
  value: number;
  rank?: number | null;
  description: string;
  metadata: Record<string, unknown>;
};

export type RetrievalSnippet = {
  text: string;
  start_char: number;
  end_char: number;
  matched_terms: string[];
  extraction_strategy: string;
};

export type RetrievalFacetBucket = {
  value: string;
  count: number;
};

export type RetrievalFacets = {
  source_type: RetrievalFacetBucket[];
  clinical_domain: RetrievalFacetBucket[];
  standard_system: RetrievalFacetBucket[];
  trust_level: RetrievalFacetBucket[];
};

export type RetrievalCoverageItem = {
  field: string;
  value: string;
  selected_count: number;
  status: string;
  severity: string;
  reason: string;
  suggested_action?: string | null;
  suggested_filter?: Record<string, unknown> | null;
};

export type RetrievalCoverage = {
  standard_system: RetrievalCoverageItem[];
  warnings: string[];
};

export type RetrievalQualitySignal = {
  code: string;
  severity: string;
  message: string;
  suggested_action: string;
  evidence_ids: string[];
  metadata: Record<string, unknown>;
};

export type RetrievalQualitySummary = {
  status: string;
  score: number;
  success_count: number;
  warning_count: number;
  destructive_count: number;
  info_count: number;
  top_action: string;
  blocker_codes: string[];
  warning_codes: string[];
};

export type RetrievalGraphNode = {
  id: string;
  label: string;
  type: string;
};

export type RetrievalGraphEdge = {
  source: string;
  relation: string;
  target: string;
  evidence_id?: string | null;
};

export type RetrievalGraphTriple = {
  subject: string;
  predicate: string;
  object: string;
  evidence_id?: string | null;
};

export type RetrievalGraphContext = {
  graph_contract: string;
  nodes: RetrievalGraphNode[];
  edges: RetrievalGraphEdge[];
  triples: RetrievalGraphTriple[];
  limits?: Record<string, unknown>;
};

export type RetrievalQueryAnalysis = {
  strategy: string;
  detected_concepts: string[];
  concept_candidates: RetrievalConceptCandidate[];
  expanded_terms: string[];
  standards: string[];
  rule_ids: string[];
  query_variants: string[];
  filter_suggestions: RetrievalFilterSuggestion[];
  diagnostics: RetrievalQueryDiagnostic[];
  search_hints: RetrievalSearchHint[];
};

export type RetrievalConceptCandidate = {
  concept_id: string;
  display_name: string;
  standard_system: string;
  code?: string | null;
  clinical_domain?: string | null;
  matched_aliases: string[];
  confidence: number;
  source?: string | null;
  metadata: Record<string, unknown>;
};

export type RetrievalFilterSuggestion = {
  field: string;
  value: string;
  reason: string;
  rule_id: string;
  confidence: number;
  applied: boolean;
};

export type RetrievalQueryDiagnostic = {
  code: string;
  severity: string;
  message: string;
  suggested_action: string;
};

export type RetrievalSearchHint = {
  target: string;
  query: string;
  url?: string | null;
  rationale: string;
  warnings: string[];
};

export type RetrievalPackage = {
  hits: RetrievalHit[];
  evidence: Evidence[];
  coverage?: RetrievalCoverage | null;
  facets?: RetrievalFacets | null;
  quality_signals?: RetrievalQualitySignal[];
  quality_summary?: RetrievalQualitySummary | null;
  trace: RetrievalTrace;
  handoff_context: {
    graph_context?: RetrievalGraphContext;
    query_analysis?: RetrievalQueryAnalysis;
    [key: string]: unknown;
  };
};

export type RetrievalSearchPayload = {
  query: string;
  top_k: number;
  schema_id?: string | null;
  workflow_id?: string | null;
  fields: string[];
  detected_format?: string | null;
  resource_type?: string | null;
  clinical_domain?: string | null;
  standard_system?: string | null;
  trust_level?: string | null;
  source_type?: string | null;
  filters: RetrievalSearchFilters;
};

export type RetrievalSearchPreset = {
  preset_id: string;
  label: string;
  description: string;
  category?: string | null;
  query: string;
  top_k: number;
  fields: string[];
  schema_id?: string | null;
  detected_format?: string | null;
  resource_type?: string | null;
  clinical_domain?: string | null;
  standard_system?: string | null;
  trust_level?: string | null;
  source_type?: string | null;
  target_sources: string[];
  launch_hint_targets: string[];
};

export type RetrievalSearchOption = {
  value: string;
  label: string;
  description?: string | null;
};

export type RetrievalSearchOptions = {
  version: string;
  detected_formats: RetrievalSearchOption[];
  top_k_values: number[];
};

export type RetrievalJudgmentValue = "relevant" | "partial" | "not_relevant";

export type RetrievalRelevanceJudgment = {
  judgment_id: string;
  owner_user_id: string;
  query: string;
  query_hash: string;
  evidence_id: string;
  value: RetrievalJudgmentValue;
  rating: number;
  source_id?: string | null;
  source_type?: string | null;
  source_version?: string | null;
  run_id?: string | null;
  search_signature?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type RetrievalRelevanceJudgmentSummary = {
  total_count: number;
  query_count: number;
  evidence_count: number;
  source_count: number;
  relevant_count: number;
  partial_count: number;
  not_relevant_count: number;
  average_rating?: number | null;
  latest_updated_at?: string | null;
  sample_limit: number;
  value_counts: Record<RetrievalJudgmentValue, number>;
};

export type RetrievalJudgmentEvaluationPayload = {
  query: string;
  ranked_evidence_ids: string[];
  cutoff?: number | null;
};

export type RetrievalEvaluationRecommendation = {
  rule_id: string;
  severity: string;
  metric: string;
  message: string;
  suggested_action: string;
  evidence_ids: string[];
  metadata: Record<string, unknown>;
};

export type RetrievalJudgmentEvaluationResult = {
  query: string;
  ranked_evidence_ids: string[];
  cutoff: number;
  judged_count: number;
  unjudged_count: number;
  relevant_count: number;
  partial_count: number;
  not_relevant_count: number;
  coverage_at_k: number;
  precision_at_k: number;
  judged_precision?: number | null;
  average_precision_at_k: number;
  ndcg_at_k?: number | null;
  average_rating?: number | null;
  unjudged_evidence_ids: string[];
  judgment_ids: string[];
  recommendations: RetrievalEvaluationRecommendation[];
};

export type RetrievalJudgmentPayload = {
  query: string;
  evidence_id: string;
  value: RetrievalJudgmentValue;
  rating?: number | null;
  source_id?: string | null;
  source_type?: string | null;
  source_version?: string | null;
  run_id?: string | null;
  search_signature?: string | null;
  metadata?: Record<string, unknown>;
};

export type RetrievalSearchFilters = {
  trust_level?: string | null;
  clinical_domain?: string | null;
  standard_system?: string | null;
  source_type?: string | null;
};

export type RetrievalSource = {
  source_id: string;
  source_type: string;
  title: string;
  source_version?: string | null;
  trust_level: string;
  clinical_domain?: string | null;
  standard_system?: string | null;
  chunk_count: number;
};

export type RetrievalIntegrityItem = {
  source_id: string;
  status: string;
  expected_chunk_count: number;
  indexed_chunk_count: number;
  expected_hash?: string | null;
  indexed_hash?: string | null;
  message: string;
};

export type RetrievalIntegrityReport = {
  repository: string;
  status: string;
  checked_scope: string;
  expected_source_count: number;
  indexed_source_count: number;
  ok_count: number;
  stale_count: number;
  missing_count: number;
  extra_count: number;
  checks: RetrievalIntegrityItem[];
  warnings: string[];
};

export type RetrievalReindexPayload = {
  include_seeded: boolean;
  include_corpus: boolean;
};

export type RetrievalReindexResult = {
  repository: string;
  include_seeded: boolean;
  include_corpus: boolean;
  chunks_indexed: number;
  embedding?: Record<string, unknown>;
  corpus?: {
    files_seen: number;
    files_indexed: number;
    chunks_indexed: number;
    skipped_files: string[];
  } | null;
};

export type AssistantChatPayload = {
  message: string;
  context?: Record<string, unknown>;
  execute_write_actions?: boolean;
};

export type AssistantToolSpec = {
  name: string;
  description: string;
  permission_scope: string;
  requires_approval: boolean;
  input_schema: Record<string, unknown>;
};

export type AssistantToolResult = {
  tool_name: string;
  status: "completed" | "failed" | "requires_approval" | "skipped";
  arguments: Record<string, unknown>;
  output: Record<string, unknown>;
  summary: string;
  error?: string | null;
  requires_approval: boolean;
};

export type AssistantFinding = {
  title: string;
  detail: string;
  severity: "info" | "warning" | "error" | "action_required";
  source_tool?: string | null;
  source_ids: string[];
};

export type AssistantEvidenceSummary = {
  source_id: string;
  claim: string;
  trust_level: string;
  confidence?: number | null;
};

export type AssistantResponse = {
  message: string;
  mode: "deterministic" | "llm";
  model?: string | null;
  findings: AssistantFinding[];
  evidence_summary: AssistantEvidenceSummary[];
  tool_calls: AssistantToolResult[];
  suggestions: string[];
  warnings: string[];
};

export type AssistantTranscriptItem = {
  id: string;
  message: string;
  context: Record<string, unknown>;
  response?: AssistantResponse;
  error?: string;
};

export type HumanReview = {
  review_id: string;
  workflow_id: string;
  status: ReviewStatus;
  trigger: string;
  question: string;
  proposed_action: Record<string, unknown>;
  allowed_decisions: string[];
  decision?: string | null;
  decision_payload?: Record<string, unknown> | null;
  decided_by?: string | null;
  decided_at?: string | null;
  clarification_requests: ClarificationRequest[];
};

export type WorkflowEvent = {
  event_id: string;
  workflow_id: string;
  timestamp: string;
  actor_type: string;
  actor_id: string;
  event_type: string;
  severity: string;
  summary: string;
  input_refs: string[];
  output_refs: string[];
  metadata: Record<string, unknown>;
};

export type WorkflowState = {
  workflow_id: string;
  owner_user_id?: string | null;
  created_at: string;
  updated_at: string;
  status: WorkflowStatus;
  schema_version: string;
  user_instruction: string;
  input?: {
    dataset_ref: string;
    input_hash: string;
    declared_format?: string | null;
    detected_format: string;
  } | null;
  intent: {
    task_type: string;
    target_format?: string | null;
    requires_explanation: boolean;
    options: Record<string, unknown>;
  };
  steps: WorkflowStep[];
  profile?: {
    row_count: number;
    field_count: number;
    fields: Array<{
      name: string;
      inferred_type: string;
      missing_count: number;
      sample_values: string[];
      pii_flag: boolean;
    }>;
    warnings: string[];
  } | null;
  validation_report?: {
    report_id: string;
    issues: ValidationIssue[];
    severity_summary: Record<string, number>;
    requires_review: boolean;
    schema_confidence: number;
  } | null;
  transformation_plan?: {
    plan_id: string;
    target_format: string;
    requires_review: boolean;
    actions: Array<Record<string, unknown>>;
    rationale: string;
  } | null;
  review?: HumanReview | null;
  retrieved_context: Evidence[];
  output?: {
    transformation?: {
      output_format: string;
      output_ref?: string | null;
      output_hash?: string | null;
      preview?: string | null;
      row_count?: number | null;
      warnings: string[];
      diff_summary: Record<string, unknown>;
    } | null;
    validation_report_id?: string | null;
    explanation_id?: string | null;
  } | null;
  explanation?: {
    explanation_id: string;
    summary: string;
    supported_claims: string[];
    unsupported_claims: string[];
    limitations: string[];
    requires_clinician_review: boolean;
  } | null;
  failure?: WorkflowFailure | null;
  handoff_context?: {
    retrieval_trace?: RetrievalTrace;
    retrieval_handoff?: Record<string, unknown>;
    graph_context?: RetrievalGraphContext;
    [key: string]: unknown;
  };
  audit_event_refs: string[];
  risk_flags: string[];
};

export type WorkflowOutputArtifact = {
  workflow_id: string;
  output_format: string;
  output_hash?: string | null;
  byte_size: number;
  content: string;
  warnings: string[];
  diff_summary: Record<string, unknown>;
};

export type SchemaEntry = {
  schema_id: string;
  title: string;
  version: string;
  required: string[];
  field_count: number;
  fields: Array<{
    name: string;
    type: string;
    description?: string | null;
  }>;
  source_ref: string;
};

export type StartWorkflowPayload = {
  instruction: string;
  data: string;
  input_format: string | null;
  target_format: string;
  schema_id: string | null;
  require_human_review: boolean;
};

export type WorkflowSummaryItem = {
  workflow_id: string;
  owner_user_id?: string | null;
  status: WorkflowStatus;
  instruction: string;
  schema_id?: string | null;
  target_format?: string | null;
  issue_count: number;
  review_id?: string | null;
  review_status?: string | null;
  evidence_count: number;
  created_at: string;
  updated_at: string;
};

export type WorkflowSummaryPage = {
  items: WorkflowSummaryItem[];
  page: number;
  page_size: number;
  total: number;
};

export type WorkflowStats = {
  total: number;
  by_status: Record<string, number>;
  pending_reviews: number;
  failed: number;
  completed: number;
  review_gated: number;
  average_issue_count: number;
};

export type ExtractorInventory = {
  available: string[];
  supported_extensions: string[];
};

export type RuntimeHealth = {
  status: string;
};

export type ReadinessCheck = {
  name: string;
  status: "ok" | "warning" | "error";
  summary: string;
  details: Record<string, unknown>;
};

export type RuntimeReadiness = {
  status: "ready" | "degraded" | "not_ready";
  checks: ReadinessCheck[];
};

export type RuntimeRetrievalSettings = {
  retrieval_framework: "custom" | "llamaindex";
  retrieval_candidate_multiplier: number;
  retrieval_min_candidates: number;
  retrieval_vector_weight: number;
  retrieval_bm25_weight: number;
  retrieval_diversity_enabled: boolean;
  retrieval_diversity_lambda: number;
  retrieval_hnsw_ef_search: number;
};

export type RuntimeRetrievalSettingsPayload = Partial<RuntimeRetrievalSettings>;

export type RuntimeRetrievalSettingsUpdate = {
  settings: RuntimeRetrievalSettings;
  reloaded: boolean;
};

export type RuntimeAssistantSettings = {
  llm_provider: "disabled" | "openai";
  llm_model: string;
  llm_timeout_seconds: number;
  llm_max_tool_calls: number;
};

export type RuntimeAssistantSettingsPayload = Partial<RuntimeAssistantSettings>;

export type RuntimeAssistantSettingsUpdate = {
  settings: RuntimeAssistantSettings;
  reloaded: boolean;
};

export type RuntimeConfig = {
  status: string;
  storage_backend: string;
  persistent_storage: boolean;
  postgres_configured: boolean;
  redis_configured: boolean;
  data_dir_configured: boolean;
  auth: {
    google_oauth_configured: boolean;
    hosted_domain_restricted: boolean;
    cookie_secure: boolean;
    cookie_effective_secure: boolean;
    cookie_samesite: string;
    session_ttl_seconds: number;
    state_ttl_seconds: number;
  };
  embedding: {
    provider: string;
    model: string;
    dimensions: number;
    openai_configured?: boolean;
    openai_base_url_configured?: boolean;
    hf_device?: string;
    hf_batch_size?: number;
    hf_cache_dir_configured?: boolean;
  };
  llm?: {
    provider: string;
    model: string;
    openai_configured: boolean;
    base_url_configured: boolean;
    timeout_seconds: number;
    max_tool_calls: number;
    runtime_settings_configured?: boolean;
    runtime_settings?: RuntimeAssistantSettings;
  };
  rerank?: {
    provider: string;
    enabled: boolean;
    model: string;
    device: string;
    batch_size: number;
    candidate_limit: number;
    score_weight: number;
  };
  retrieval?: {
    framework?: string;
    corpus_dir_count: number;
    chunk_max_chars: number;
    chunk_overlap_chars: number;
    candidate_multiplier?: number;
    min_candidates?: number;
    vector_weight?: number;
    bm25_weight?: number;
    diversity_enabled?: boolean;
    diversity_lambda?: number;
    hnsw_ef_search?: number;
    runtime_settings_configured?: boolean;
    runtime_settings?: RuntimeRetrievalSettings;
  };
  upload: {
    max_upload_bytes: number;
    max_inline_data_bytes: number;
    read_chunk_bytes: number;
    allowed_extensions: string[];
  };
};
