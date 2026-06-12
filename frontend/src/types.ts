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
  request_id?: string | null;
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

export type WorkflowProvenanceRecord = {
  provenance_id: string;
  activity:
    | "workflow"
    | "assistant"
    | "upload"
    | "extract"
    | "parse"
    | "profile"
    | "retrieve_evidence"
    | "validate"
    | "policy_review"
    | "review"
    | "convert"
    | "retrieval_derived_transform"
    | "explain"
    | "failure";
  agent: string;
  event_refs: string[];
  source_refs: string[];
  target_refs: string[];
  evidence_ids: string[];
  issue_ids: string[];
  review_ids: string[];
  request_id?: string | null;
  occurred_at: string;
  summary: string;
  metadata: Record<string, unknown>;
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

export type OcrEvidenceFieldInput = {
  page: number;
  name: string;
  value: string;
  bbox: number[];
  confidence: number;
  source_ref: string;
  normalized_to?: string | null;
};

export type OcrField = OcrEvidenceFieldInput & {
  field_id: string;
  requires_review: boolean;
};

export type OcrEvidenceResponse = {
  fields: OcrField[];
  evidence: Evidence[];
  requires_review: boolean;
};

export type RetrievalTrace = {
  strategy: string;
  query_variants: string[];
  query_variant_details?: RetrievalQueryVariant[];
  fusion_diagnostics?: Record<string, unknown>;
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
  match_explanation?: Record<string, unknown>;
  snippet?: RetrievalSnippet | null;
};

export type RetrievalEvidenceBucket = {
  bucket_id:
    | "schema"
    | "policy"
    | "terminology"
    | "fhir_mapping"
    | "source_locator"
    | "prior_decision"
    | "other";
  label: string;
  description: string;
  evidence_ids: string[];
  source_ids: string[];
  hit_count: number;
  required: boolean;
  status: string;
  warnings: string[];
  suggested_filter: Record<string, string>;
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
  query_aspects?: RetrievalCoverageItem[];
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

export type RetrievalRecommendedAction = {
  action_id: string;
  priority: number;
  severity: string;
  action_type:
    | "apply_filter"
    | "broaden_query"
    | "rewrite_query"
    | "reindex_source"
    | "add_source"
    | "require_review"
    | "diversify_sources";
  title: string;
  description: string;
  suggested_filter: Record<string, string>;
  source_signal_codes: string[];
  evidence_ids: string[];
  metadata: Record<string, unknown>;
};

export type RetrievalRecommendedActionSummary = {
  count: number;
  highest_priority?: number | null;
  highest_severity?: string | null;
  top_action_title?: string | null;
  apply_filter_count: number;
  broaden_query_count: number;
  action_type_counts: Record<string, number>;
};

export type RetrievalStrategyRecommendation = {
  recommendation_id: string;
  title: string;
  technique: string;
  status: string;
  rationale: string;
  source_signal_codes: string[];
  suggested_filters: Record<string, string>;
  metadata: Record<string, unknown>;
};

export type RetrievalInterpretation = {
  status: string;
  summary: string;
  top_evidence_id?: string | null;
  top_source_id?: string | null;
  top_score_driver?: string | null;
  support_status?: string | null;
  matched_terms: string[];
  concept_labels: string[];
  aspect_labels: string[];
  required_bucket_count: number;
  covered_required_bucket_count: number;
  missing_required_buckets: string[];
  warning_count: number;
  next_action_title?: string | null;
  next_action_detail?: string | null;
  metadata: Record<string, unknown>;
};

export type RetrievalSupportStatus = "strong" | "partial" | "weak" | "unsupported";

export type RetrievalEvidenceSupportRow = {
  claim_id: string;
  claim: string;
  support_status: RetrievalSupportStatus;
  evidence_id: string;
  source_id: string;
  source_type: string;
  source_version?: string | null;
  source_locator: Record<string, unknown>;
  matched_terms: string[];
  score: number;
  confidence?: number | null;
  reasoning: string;
  warnings: string[];
  metadata: Record<string, unknown>;
};

export type RetrievalEvidenceSupportMatrix = {
  version: string;
  query_claim: string;
  row_count: number;
  strong_count: number;
  partial_count: number;
  weak_count: number;
  unsupported_count: number;
  rows: RetrievalEvidenceSupportRow[];
  warnings: string[];
};

export type RetrievalAnswerStatus = "supported" | "partial" | "refused" | "review_required";

export type RetrievalAnswerCitation = {
  citation_id: string;
  evidence_id: string;
  source_id: string;
  source_type: string;
  source_version?: string | null;
  source_locator: Record<string, unknown>;
  supported_claim_ids: string[];
};

export type RetrievalAnswerClaim = {
  claim_id: string;
  text: string;
  support_status: RetrievalSupportStatus;
  evidence_ids: string[];
  citation_ids: string[];
  graph_path_refs: string[];
  graph_guard: Record<string, unknown>;
  warnings: string[];
};

export type RetrievalAnswerFreshnessWarning = {
  warning_id: string;
  severity: string;
  evidence_id?: string | null;
  source_id?: string | null;
  source_version?: string | null;
  message: string;
  suggested_action: string;
  metadata: Record<string, unknown>;
};

export type RetrievalAnswer = {
  version: string;
  status: RetrievalAnswerStatus;
  answer_text: string;
  refusal_reason?: string | null;
  requires_human_review: boolean;
  confidence: number;
  claims: RetrievalAnswerClaim[];
  citations: RetrievalAnswerCitation[];
  unsupported_claims: RetrievalAnswerClaim[];
  missing_evidence_gaps: string[];
  freshness_warnings: RetrievalAnswerFreshnessWarning[];
  graph_path_summary: Record<string, unknown>;
  metadata: Record<string, unknown>;
};

export type RetrievalStandardSearchStep = {
  step_id: string;
  label: string;
  standard_system: string;
  route_type: string;
  query: string;
  rationale: string;
  priority: number;
  suggested_filters: Record<string, string>;
  governance_notes: string[];
  metadata: Record<string, unknown>;
};

export type RetrievalStandardSearchPlan = {
  plan_id: string;
  summary: string;
  primary_route: string;
  steps: RetrievalStandardSearchStep[];
  missing_routes: string[];
  governance_notes: string[];
  metadata: Record<string, unknown>;
};

export type RetrievalDiversitySelection = {
  evidence_id: string;
  source_id: string;
  selected_rank: number;
  original_rank: number;
  relevance_score: number;
  redundancy_score: number;
  selection_score: number;
  reason: string;
};

export type RetrievalDiversitySummary = {
  enabled: boolean;
  selection_mode: string;
  lambda_value?: number | null;
  candidate_source_count: number;
  selected_source_count: number;
  duplicate_selected_source_count: number;
  selected_hits: RetrievalDiversitySelection[];
};

export type RetrievalGraphNode = {
  id: string;
  label: string;
  type: string;
  confidence?: number;
  matched_text?: string;
  rule_source?: string;
  clinical_domain?: string;
  concept_registry_id?: string;
  normalized_code?: string;
  normalized_system?: string;
  normalized_display?: string;
  standard_system?: string;
  display_name?: string;
  target_field?: string | null;
  search_type?: string | null;
  example?: string | null;
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
  summary?: {
    node_count?: number;
    edge_count?: number;
    triple_count?: number;
    rule_source_count?: number;
    concept_registry_count?: number;
  };
  limits?: Record<string, unknown>;
};

export type RetrievalGraphContextRecord = {
  graph_id: string;
  owner_user_id?: string | null;
  workflow_id?: string | null;
  request_id?: string | null;
  search_signature?: string | null;
  query: string;
  resource_type?: string | null;
  fields: string[];
  node_count: number;
  edge_count: number;
  triple_count: number;
  graph_context: RetrievalGraphContext | Record<string, unknown>;
  created_at: string;
};

export type RetrievalGraphNeighborhoodQuery = {
  workflow_id?: string | null;
  q?: string | null;
  node_id?: string | null;
  evidence_id?: string | null;
  source_id?: string | null;
  normalized_code?: string | null;
  resource_type?: string | null;
  field?: string | null;
  relation?: string | null;
  limit?: number;
  max_depth?: number;
};

export type RetrievalGraphNeighborhood = {
  query: RetrievalGraphNeighborhoodQuery;
  source_graph_ids: string[];
  graph_count: number;
  node_count: number;
  edge_count: number;
  triple_count: number;
  matched_node_ids: string[];
  matched_evidence_ids: string[];
  nodes: Array<Record<string, unknown>>;
  edges: Array<Record<string, unknown>>;
  triples: Array<Record<string, unknown>>;
  warnings: string[];
  generated_at: string;
};

export type RetrievalQueryAnalysis = {
  strategy: string;
  detected_concepts: string[];
  concept_candidates: RetrievalConceptCandidate[];
  expanded_terms: string[];
  standards: string[];
  rule_ids: string[];
  query_variants: string[];
  query_variant_details?: RetrievalQueryVariant[];
  filter_suggestions: RetrievalFilterSuggestion[];
  diagnostics: RetrievalQueryDiagnostic[];
  search_hints: RetrievalSearchHint[];
  query_profile?: RetrievalQueryProfile | null;
  query_route?: RetrievalQueryRoute | null;
  query_aspects?: RetrievalQueryAspect[];
  retrieval_tasks?: RetrievalSearchTask[];
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
  metadata: Record<string, unknown>;
};

export type RetrievalSearchHint = {
  target: string;
  query: string;
  url?: string | null;
  rationale: string;
  warnings: string[];
  metadata?: Record<string, unknown>;
};

export type RetrievalQueryProfile = {
  profile_id: string;
  label: string;
  route: string;
  complexity: string;
  retrieval_mode: string;
  description: string;
  suggested_filters: Record<string, string>;
  rule_ids: string[];
};

export type RetrievalRouteBudget = {
  max_candidates: number;
  max_returned_hits: number;
  reranker_candidate_limit: number;
  source_diversity_enabled: boolean;
  min_source_count: number;
  diversity_lambda: number;
  external_network_allowed: boolean;
  latency_target_ms: number;
  rationale: string;
  metadata: Record<string, unknown>;
};

export type RetrievalQueryRoute = {
  route_id: string;
  strategy_id: string;
  label: string;
  retrieval_mode: string;
  rationale: string;
  rule_id: string;
  priority: number;
  confidence: number;
  matched_criteria: string[];
  suggested_filters: Record<string, string>;
  risk_controls: string[];
  budget?: RetrievalRouteBudget | null;
  metadata: Record<string, unknown>;
};

export type RetrievalQueryAspect = {
  aspect_id: string;
  label: string;
  question: string;
  rationale: string;
  priority: number;
  rule_id: string;
  suggested_terms: string[];
  suggested_filters: Record<string, string>;
};

export type RetrievalSearchTask = {
  task_id: string;
  label: string;
  target: "local_corpus" | "external_medical_index";
  action_type: "run_local_search" | "open_external_url" | "copy_query";
  query: string;
  rationale: string;
  priority: number;
  required: boolean;
  aspect_id?: string | null;
  search_hint_target?: string | null;
  query_variants: string[];
  standards: string[];
  suggested_filters: Record<string, string>;
  warnings: string[];
  metadata: Record<string, unknown>;
};

export type RetrievalPlanCoverageSummary = {
  ready: boolean;
  local_task_count: number;
  required_local_task_count: number;
  external_task_count: number;
  standard_count: number;
  filter_count: number;
  standards: string[];
  warnings: string[];
  next_action: string;
  summary: string;
};

export type RetrievalPlanRiskSignal = {
  code: string;
  severity: string;
  message: string;
  suggested_action: string;
  source: string;
  metadata: Record<string, unknown>;
};

export type RetrievalPlanTaskSummary = {
  total_task_count: number;
  runnable_local_count: number;
  required_runnable_local_count: number;
  external_open_count: number;
  external_copy_count: number;
  manual_followup_count: number;
  blocked_task_count: number;
  primary_action: string;
  summary: string;
};

export type RetrievalPackage = {
  hits: RetrievalHit[];
  evidence: Evidence[];
  evidence_buckets?: RetrievalEvidenceBucket[];
  coverage?: RetrievalCoverage | null;
  facets?: RetrievalFacets | null;
  quality_signals?: RetrievalQualitySignal[];
  quality_summary?: RetrievalQualitySummary | null;
  recommended_actions?: RetrievalRecommendedAction[];
  recommended_action_summary?: RetrievalRecommendedActionSummary | null;
  remediation_summary?: string | null;
  interpretation?: RetrievalInterpretation | null;
  support_matrix?: RetrievalEvidenceSupportMatrix | null;
  answer?: RetrievalAnswer | null;
  strategy_recommendations?: RetrievalStrategyRecommendation[];
  standard_search_plan?: RetrievalStandardSearchPlan | null;
  diversity?: RetrievalDiversitySummary | null;
  trace: RetrievalTrace;
  handoff_context: {
    graph_context?: RetrievalGraphContext;
    query_analysis?: RetrievalQueryAnalysis;
    retrieval_rule_packs?: RuntimeRetrievalRulePack[];
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

export type RetrievalPlanQuery = {
  query: string;
  workflow_id?: string | null;
  fields: string[];
  schema_id?: string | null;
  detected_format?: string | null;
  resource_type?: string | null;
  top_k: number;
  filters: Record<string, unknown>;
};

export type RetrievalPlan = {
  query: RetrievalPlanQuery;
  query_analysis: RetrievalQueryAnalysis;
  coverage_summary?: RetrievalPlanCoverageSummary | null;
  task_summary?: RetrievalPlanTaskSummary | null;
  risk_signals?: RetrievalPlanRiskSignal[];
  search_signature: string;
  summary: string;
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

export type RetrievalSourceTrustPolicy = {
  source_id: string;
  source_name: string;
  authority: string;
  domain: string;
  standard_system: string;
  clinical_scope: string[];
  intended_use: string[];
  prohibited_use: string[];
  refresh_cadence: string;
  license_constraints: string[];
  access_mode: string;
  ingestion_mode: string;
  evidence_tier: string;
  requires_reviewer_approval: boolean;
  source_urls: Record<string, string>;
  policy_notes: string[];
};

export type RetrievalSourceTrustPolicyCatalog = {
  version: string;
  policies: RetrievalSourceTrustPolicy[];
};

export type CorpusLifecycleState =
  | "candidate"
  | "approved"
  | "deprecated"
  | "blocked"
  | "failed"
  | "needs_review";

export type CorpusLicenseMetadata = {
  license_id: string;
  name: string;
  url?: string | null;
  constraints: string[];
};

export type CorpusSourceAdapter = {
  adapter_id: string;
  source_id: string;
  title: string;
  authority: string;
  source_type: string;
  clinical_domain: string;
  standard_system: string;
  access_mode: string;
  ingestion_mode: string;
  release_version: string;
  refresh_cadence: string;
  reviewer_state: CorpusLifecycleState;
  lifecycle_state: CorpusLifecycleState;
  enabled: boolean;
  source_urls: Record<string, string>;
  local_paths: string[];
  parser: string;
  chunk_profile: string;
  fetch_time_policy: string;
  license: CorpusLicenseMetadata;
  governance_notes: string[];
  metadata: Record<string, unknown>;
};

export type CorpusAdapterCatalog = {
  version: string;
  adapters: CorpusSourceAdapter[];
};

export type CorpusChunkingProfile = {
  profile_id: string;
  label: string;
  description: string;
  boundary_strategy: string;
  max_chars: number;
  overlap_chars: number;
  preferred_extensions: string[];
  metadata_fields: string[];
  intended_sources: string[];
  lifecycle_state: CorpusLifecycleState;
  governance_notes: string[];
};

export type CorpusChunkingProfileCatalog = {
  version: string;
  profiles: CorpusChunkingProfile[];
};

export type CorpusIngestionItem = {
  item_id: string;
  source_id: string;
  adapter_id?: string | null;
  title: string;
  source_type: string;
  clinical_domain: string;
  standard_system: string;
  release_version: string;
  fetched_at: string;
  fetch_time_source: string;
  content_hash: string;
  size_bytes: number;
  path?: string | null;
  source_url?: string | null;
  license: CorpusLicenseMetadata;
  reviewer_state: CorpusLifecycleState;
  lifecycle_state: CorpusLifecycleState;
  enabled: boolean;
  warnings: string[];
  metadata: Record<string, unknown>;
};

export type CorpusIngestionManifest = {
  version: string;
  generated_at: string;
  adapter_catalog_version: string;
  knowledge_root: string;
  item_count: number;
  enabled_adapter_count: number;
  approved_item_count: number;
  needs_review_item_count: number;
  items: CorpusIngestionItem[];
};

export type RetrievalStrategyProfile = {
  strategy_id: string;
  label: string;
  status: string;
  technique_family: string;
  description: string;
  intended_use: string[];
  avoid_when: string[];
  query_transformations: string[];
  retrieval_modes: string[];
  required_runtime: string[];
  compatible_filters: string[];
  risk_controls: string[];
  roadmap_refs: string[];
  metadata: Record<string, unknown>;
};

export type RetrievalStrategyCatalog = {
  version: string;
  strategies: RetrievalStrategyProfile[];
};

export type McpResourceSpec = {
  resource_id: string;
  uri: string;
  name: string;
  title: string;
  description: string;
  mime_type: string;
  provider_key: string;
  permission_scope: string;
  tags: string[];
  roadmap_refs: string[];
};

export type McpResourceCatalog = {
  version: string;
  resources: McpResourceSpec[];
};

export type McpPromptArgument = {
  name: string;
  description: string;
  required: boolean;
  default?: string | null;
  value_hint?: string | null;
};

export type McpPromptSpec = {
  prompt_id: string;
  name: string;
  title: string;
  description: string;
  task_type: string;
  template: string;
  arguments: McpPromptArgument[];
  recommended_tools: string[];
  evidence_required: boolean;
  write_actions_allowed: boolean;
  tags: string[];
  roadmap_refs: string[];
};

export type McpPromptCatalog = {
  version: string;
  prompts: McpPromptSpec[];
};

export type RetrievalJudgmentValue =
  | "relevant"
  | "partial"
  | "irrelevant"
  | "not_relevant"
  | "unsafe"
  | "stale"
  | "source_policy_blocked";

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
  unsafe_count: number;
  stale_count: number;
  source_policy_blocked_count: number;
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
  unsafe_count: number;
  stale_count: number;
  source_policy_blocked_count: number;
  coverage_at_k: number;
  hit_rate_at_k: number;
  precision_at_k: number;
  judged_precision?: number | null;
  average_precision_at_k: number;
  mrr_at_k: number;
  ndcg_at_k?: number | null;
  average_rating?: number | null;
  unjudged_evidence_ids: string[];
  judgment_ids: string[];
  evaluation_readiness: {
    status: string;
    label: string;
    message: string;
    min_judged_count: number;
    min_coverage_at_k: number;
  };
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

export type RetrievalActiveLearningSourceKind =
  | "low_confidence_retrieval"
  | "unsupported_claim"
  | "reviewer_correction"
  | "weak_support"
  | "negative_judgment";

export type RetrievalActiveLearningStatus =
  | "open"
  | "accepted"
  | "rejected"
  | "promoted"
  | "archived";

export type RetrievalActiveLearningPriority = "low" | "normal" | "high" | "critical";

export type RetrievalActiveLearningCandidate = {
  candidate_id: string;
  owner_user_id: string;
  candidate_key: string;
  query_hash: string;
  query: string;
  source_kind: RetrievalActiveLearningSourceKind;
  trigger_reason: string;
  priority: RetrievalActiveLearningPriority;
  status: RetrievalActiveLearningStatus;
  evidence_id?: string | null;
  source_id?: string | null;
  source_type?: string | null;
  source_version?: string | null;
  run_id?: string | null;
  workflow_id?: string | null;
  judgment_id?: string | null;
  claim_id?: string | null;
  support_status?: RetrievalSupportStatus | null;
  suggested_expected_evidence_ids: string[];
  suggested_filters: Record<string, unknown>;
  benchmark_metadata: Record<string, unknown>;
  metadata: Record<string, unknown>;
  reviewer_user_id?: string | null;
  reviewer_note?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type RetrievalActiveLearningSummary = {
  total_count: number;
  open_count: number;
  accepted_count: number;
  rejected_count: number;
  promoted_count: number;
  archived_count: number;
  critical_count: number;
  high_count: number;
  source_kind_counts: Record<RetrievalActiveLearningSourceKind, number>;
  latest_updated_at?: string | null;
  sample_limit: number;
};

export type RetrievalActiveLearningCandidatePayload = {
  source_kind: RetrievalActiveLearningSourceKind;
  query: string;
  trigger_reason: string;
  priority?: RetrievalActiveLearningPriority;
  evidence_id?: string | null;
  source_id?: string | null;
  source_type?: string | null;
  source_version?: string | null;
  run_id?: string | null;
  workflow_id?: string | null;
  judgment_id?: string | null;
  claim_id?: string | null;
  support_status?: RetrievalSupportStatus | null;
  suggested_expected_evidence_ids?: string[];
  suggested_filters?: Record<string, unknown>;
  benchmark_metadata?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
};

export type RetrievalActiveLearningCandidateUpdatePayload = {
  status?: RetrievalActiveLearningStatus | null;
  priority?: RetrievalActiveLearningPriority | null;
  reviewer_note?: string | null;
  benchmark_metadata?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
};

export type RetrievalSearchFilters = {
  trust_level?: string | null;
  clinical_domain?: string | null;
  standard_system?: string | null;
  source_type?: string | null;
  source_id?: string | null;
  corpus_partition?: string | null;
  corpus_visibility?: "global" | "organization" | "private" | null;
  organization_id?: string | null;
  diversity_enabled?: boolean | null;
  diversity_lambda?: number | null;
};

export type PrivateCorpusIngestPayload = {
  data?: string | null;
  artifact_id?: string | null;
  title?: string | null;
  source_ref?: string | null;
  input_format?: string | null;
  redaction_action?: string | null;
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
  authority?: string | null;
  access_mode?: string | null;
  ingestion_mode?: string | null;
  license_id?: string | null;
  license_name?: string | null;
  reviewer_state?: CorpusLifecycleState | null;
  lifecycle_state?: CorpusLifecycleState | null;
  content_hash?: string | null;
  canonical_source_id?: string | null;
  chunk_profile?: string | null;
  resource_type?: string | null;
  corpus_partition_id?: string | null;
  corpus_partition_label?: string | null;
  corpus_partition_purpose?: string | null;
  corpus_visibility?: string | null;
  organization_id?: string | null;
  external_provider_allowed?: boolean | null;
  phi_allowed?: boolean | null;
  retention_policy_id?: string | null;
};

export type CorpusPartitionPurpose =
  | "global_standard"
  | "tenant_policy"
  | "private_document"
  | "shared_reference";

export type CorpusPartitionVisibility = "global" | "organization" | "private";

export type CorpusPartitionPolicy = {
  partition_id: string;
  label: string;
  purpose: CorpusPartitionPurpose;
  visibility: CorpusPartitionVisibility;
  description: string;
  source_id_prefixes: string[];
  local_path_prefixes: string[];
  allowed_source_types: string[];
  default_for_uncataloged: boolean;
  required_permission_scopes: string[];
  external_provider_allowed: boolean;
  phi_allowed: boolean;
  requires_reviewer_approval: boolean;
  retention_policy_id?: string | null;
  metadata: Record<string, unknown>;
};

export type CorpusPartitionCatalog = {
  version: string;
  default_partition_id: string;
  partitions: CorpusPartitionPolicy[];
};

export type PrivateCorpusIngestionResult = {
  ingestion_id: string;
  source_id: string;
  source: RetrievalSource;
  chunk_count: number;
  organization_id: string;
  owner_user_id: string;
  title: string;
  source_ref?: string | null;
  artifact_id?: string | null;
  original_text_sha256: string;
  indexed_text_sha256: string;
  redaction_preview: Record<string, unknown>;
  retention_policy: Record<string, unknown>;
  external_provider_allowed: boolean;
  requires_review: boolean;
  warnings: string[];
  metadata: Record<string, unknown>;
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

export type RetrievalFreshnessStatus = "ready" | "watch" | "needs_review" | "blocked";

export type MedicalSourceQualitySignal = {
  rule_id: string;
  dimension: string;
  matched_value: string;
  score_delta: number;
  severity: string;
  message: string;
  suggested_action: string;
  metadata: Record<string, unknown>;
};

export type MedicalSourceQualityScore = {
  policy_version: string;
  score: number;
  status: RetrievalFreshnessStatus;
  severity: string;
  base_score: number;
  positive_delta: number;
  negative_delta: number;
  top_action: string;
  signals: MedicalSourceQualitySignal[];
  dimensions: Record<string, unknown>;
};

export type RetrievalFreshnessSource = {
  source_id: string;
  title: string;
  source_type: string;
  authority?: string | null;
  standard_system?: string | null;
  clinical_domain?: string | null;
  release_version?: string | null;
  refresh_cadence?: string | null;
  lifecycle_state?: CorpusLifecycleState | null;
  reviewer_state?: CorpusLifecycleState | null;
  indexed_chunk_count: number;
  manifest_item_count: number;
  last_observed_at?: string | null;
  age_days?: number | null;
  freshness_window_days?: number | null;
  status: RetrievalFreshnessStatus;
  severity: string;
  issues: string[];
  recommended_actions: string[];
  source_urls: Record<string, string>;
  quality?: MedicalSourceQualityScore | null;
  metadata: Record<string, unknown>;
};

export type RetrievalFreshnessReport = {
  version: string;
  generated_at: string;
  status: RetrievalFreshnessStatus;
  score: number;
  source_count: number;
  ready_count: number;
  watch_count: number;
  needs_review_count: number;
  blocked_count: number;
  stale_count: number;
  unindexed_count: number;
  missing_policy_count: number;
  average_quality_score: number;
  low_quality_count: number;
  quality_review_count: number;
  adapter_catalog_version: string;
  manifest_version: string;
  policy_catalog_version: string;
  quality_policy_version?: string | null;
  sources: RetrievalFreshnessSource[];
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
  embedding_generation_id?: string | null;
  corpus?: {
    files_seen: number;
    files_indexed: number;
    chunks_indexed: number;
    skipped_files: string[];
    manifest?: CorpusIngestionManifest | null;
  } | null;
};

export type AssistantChatPayload = {
  message: string;
  context?: Record<string, unknown>;
  execute_write_actions?: boolean;
  session_id?: string;
};

export type AssistantToolSpec = {
  name: string;
  description: string;
  permission_scope: string;
  permission_tags: string[];
  risk_level: string;
  approval_reason?: string | null;
  requires_approval: boolean;
  input_schema: Record<string, unknown>;
};

export type AssistantExample = {
  example_id: string;
  label: string;
  description: string;
  message: string;
  context: Record<string, unknown>;
};

export type AssistantAnswerTemplateSection = {
  section_id: string;
  title: string;
  purpose: string;
  required: boolean;
};

export type AssistantAnswerTemplate = {
  template_id: string;
  label: string;
  description: string;
  tool_names: string[];
  sections: AssistantAnswerTemplateSection[];
  evidence_required: boolean;
  review_required_when: string[];
  output_constraints: string[];
};

export type AssistantMemoryValue = string | number | boolean;

export type AssistantMemoryPreferenceDefinition = {
  key: string;
  label: string;
  description: string;
  category: string;
  value_type: "string" | "boolean" | "number" | "enum";
  allowed_values: AssistantMemoryValue[];
  default_value?: AssistantMemoryValue | null;
  max_length: number;
  safety_tags: string[];
};

export type AssistantMemoryPolicy = {
  version: string;
  preferences: AssistantMemoryPreferenceDefinition[];
  rejected_key_terms: string[];
  rejected_value_patterns: string[];
};

export type AssistantMemoryPreference = {
  owner_user_id: string;
  key: string;
  value: AssistantMemoryValue;
  category: string;
  source: "user" | "system" | "admin";
  policy_version: string;
  created_at: string;
  updated_at: string;
};

export type AssistantMemorySnapshot = {
  policy_version: string;
  preferences: AssistantMemoryPreference[];
  context: Record<string, AssistantMemoryValue>;
};

export type AssistantMemoryPreferencePayload = {
  value: AssistantMemoryValue;
  source?: "user" | "system" | "admin";
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

export type AssistantToolPlan = {
  tool_name: string;
  arguments: Record<string, unknown>;
  rationale: string;
};

export type AssistantPlan = {
  message: string;
  tool_calls: AssistantToolPlan[];
  warnings: string[];
};

export type AssistantFinding = {
  title: string;
  detail: string;
  severity: "info" | "warning" | "error" | "action_required";
  source_tool?: string | null;
  source_ids: string[];
};

export type AssistantEvidenceSummary = {
  evidence_id?: string | null;
  source_id: string;
  source_type?: string | null;
  claim: string;
  trust_level: string;
  confidence?: number | null;
  locator?: Record<string, unknown>;
  match_explanation?: Record<string, unknown>;
};

export type AssistantResponse = {
  message: string;
  mode: "deterministic" | "llm";
  synthesis_mode: "deterministic" | "llm";
  model?: string | null;
  findings: AssistantFinding[];
  evidence_summary: AssistantEvidenceSummary[];
  tool_calls: AssistantToolResult[];
  suggestions: string[];
  warnings: string[];
};

export type AssistantChatSessionSummary = {
  session_id: string;
  owner_user_id: string;
  title: string;
  message_count: number;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type AssistantChatMessage = {
  message_id: string;
  session_id: string;
  owner_user_id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  workflow_refs: string[];
  payload: Record<string, unknown>;
  created_at: string;
};

export type AssistantStreamReplay = {
  stream_id: string;
  session_id: string;
  owner_user_id: string;
  status: "completed" | "failed" | "cancelled";
  events: AssistantStreamEvent[];
  created_at: string;
  completed_at: string;
};

export type AssistantChatSessionDetail = {
  session: AssistantChatSessionSummary;
  messages: AssistantChatMessage[];
};

export type AssistantSessionCreatePayload = {
  title?: string;
};

export type AssistantSessionRenamePayload = {
  title: string;
};

export type AssistantSessionMessagePayload = {
  role: "user" | "assistant" | "system" | "tool";
  content?: string;
  workflow_refs?: string[];
  payload?: Record<string, unknown>;
};

export type AssistantStreamEvent =
  | {
      type: "stream_opened";
      message: string;
    }
  | {
      type: "planning_started";
      mode: "deterministic" | "llm";
      model?: string | null;
      available_tool_count?: number;
      max_tool_calls?: number;
      message: string;
    }
  | {
      type: "planning_progress";
      mode: "deterministic" | "llm";
      elapsed_seconds: number;
      message: string;
    }
  | {
      type: "planning_step";
      mode: "deterministic" | "llm";
      label: string;
      message: string;
    }
  | {
      type: "planning_delta";
      mode: "deterministic" | "llm";
      delta: string;
    }
  | {
      type: "plan_ready";
      mode: "deterministic" | "llm";
      plan: AssistantPlan;
    }
  | {
      type: "tool_started";
      index: number;
      tool_call: AssistantToolPlan;
    }
  | {
      type: "tool_progress";
      index: number;
      tool_name: string;
      stage_id: string;
      label: string;
      message: string;
      progress?: number | null;
    }
  | {
      type: "tool_completed";
      index: number;
      tool_result: AssistantToolResult;
    }
  | {
      type: "synthesis_started";
      mode: "deterministic" | "llm";
      message: string;
    }
  | {
      type: "answer_delta";
      delta: string;
    }
  | {
      type: "warning";
      message: string;
    }
  | {
      type: "cancelled";
      message: string;
    }
  | {
      type: "error";
      code: string;
      message: string;
      details?: Record<string, unknown>;
    }
  | {
      type: "final";
      response: AssistantResponse;
    };

export type AssistantTranscriptItem = {
  id: string;
  message: string;
  context: Record<string, unknown>;
  response?: AssistantResponse;
  stream_events?: AssistantStreamEvent[];
  streamed_answer?: string;
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

export type ClinicalFieldProvenance = {
  target_path: string;
  source_field?: string | null;
  source_value?: unknown | null;
  location?: ValidationIssue["location"] | null;
  evidence_ids: string[];
  derivation: "source" | "derived" | "defaulted" | "review_required" | "unmapped";
  note: string;
};

export type ClinicalResourceRecord = {
  resource_id: string;
  resource_type: string;
  resource: Record<string, unknown>;
  field_provenance: ClinicalFieldProvenance[];
  source_row?: number | null;
  review_required: boolean;
  warnings: string[];
};

export type ClinicalOperationOutcomeIssue = {
  severity: string;
  code: string;
  diagnostics: string;
  expression: string[];
  issue_id?: string | null;
  location?: ValidationIssue["location"] | null;
  requires_review: boolean;
};

export type TerminologyCandidate = {
  candidate_id: string;
  source_field: string;
  source_value: string;
  standard_system: string;
  code: string;
  display: string;
  confidence: number;
  matched_aliases: string[];
  source_uri?: string | null;
  location?: ValidationIssue["location"] | null;
  status: "candidate" | "review_required" | "accepted" | "rejected";
  requires_review: boolean;
  metadata: Record<string, unknown>;
};

export type UnitValidationResult = {
  validation_id: string;
  source_field: string;
  source_unit: string;
  normalized_unit?: string | null;
  standard_system: string;
  status: "valid" | "missing" | "unknown" | "not_preferred";
  confidence: number;
  message: string;
  location?: ValidationIssue["location"] | null;
  requires_review: boolean;
  metadata: Record<string, unknown>;
};

export type ClinicalSemanticNormalizationGate = {
  gate_id: string;
  gate_type:
    | "lab_name"
    | "unit"
    | "date"
    | "patient_identifier"
    | "diagnosis"
    | "medication"
    | "procedure";
  source_field: string;
  source_value?: unknown | null;
  target_resource_type: string;
  target_path: string;
  location?: ValidationIssue["location"] | null;
  candidate_id?: string | null;
  unit_validation_id?: string | null;
  proposed_system?: string | null;
  proposed_code?: string | null;
  proposed_display?: string | null;
  proposed_value?: unknown | null;
  confidence?: number | null;
  status: "review_required" | "approved" | "rejected" | "not_applicable";
  requires_review: boolean;
  blocks_automatic_change: boolean;
  reason: string;
  metadata: Record<string, unknown>;
};

export type ClinicalPackage = {
  package_type: "ojtflow_clinical_package";
  schema_version: string;
  package_id: string;
  workflow_id: string;
  raw_input: {
    dataset_ref: string;
    input_hash: string;
    declared_format?: string | null;
    detected_format: string;
  };
  clinical_bundle: {
    resourceType: "Bundle";
    type: string;
    entry: Array<Record<string, unknown>>;
    resources: ClinicalResourceRecord[];
  };
  operation_outcome: {
    resourceType: "OperationOutcome";
    issue: ClinicalOperationOutcomeIssue[];
  };
  validation_report_id?: string | null;
  evidence: Evidence[];
  terminology_candidates: TerminologyCandidate[];
  unit_validations: UnitValidationResult[];
  semantic_normalization_gates: ClinicalSemanticNormalizationGate[];
  provenance: Array<Record<string, unknown>>;
  review?: HumanReview | null;
  audit_event_refs: string[];
  output_refs: string[];
  handoff_context: Record<string, unknown>;
  warnings: string[];
  created_at: string;
  updated_at: string;
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
  clinical_package?: ClinicalPackage | null;
  failure?: WorkflowFailure | null;
  provenance: WorkflowProvenanceRecord[];
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

export type ExtractedDocument = {
  filename: string;
  source_format: string;
  extractor_used: string;
  page_count?: number | null;
  char_count: number;
  word_count: number;
  text: string;
  warnings: string[];
  artifact_id?: string | null;
  job_id?: string | null;
  trace_id?: string | null;
  text_dataset_id?: string | null;
  text_storage_ref?: string | null;
  source?: string | null;
};

export type RuntimeHealth = {
  status: string;
};

export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

export type JobType =
  | "retrieval_reindex"
  | "file_parse"
  | "ocr_extract"
  | "embedding_reindex"
  | "external_ingest"
  | "export_package";

export type BackgroundJob = {
  job_id: string;
  owner_user_id: string;
  job_type: JobType;
  status: JobStatus;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  error?: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  } | null;
  progress: {
    current: number;
    total?: number | null;
    message: string;
  };
  attempts: number;
  max_attempts: number;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  completed_at?: string | null;
};

export type ArtifactRetentionPolicy = {
  policy_id: string;
  sensitivity_class: string;
  action: string;
  retain_until?: string | null;
  reason: string;
  mode?: string | null;
  source?: string | null;
  tenant_id?: string | null;
};

export type UploadedArtifact = {
  artifact_id: string;
  owner_user_id: string;
  filename: string;
  mime_type: string;
  extension: string;
  byte_size: number;
  sha256: string;
  source: string;
  storage_ref: string;
  dataset_id?: string | null;
  duplicate_of_artifact_id?: string | null;
  retention_policy: ArtifactRetentionPolicy;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ExtractionStepTrace = {
  step_id: string;
  extractor: string;
  status: string;
  started_at?: string | null;
  completed_at?: string | null;
  summary: string;
  warnings: string[];
  input_ref?: string | null;
  output_ref?: string | null;
  confidence?: number | null;
  metadata: Record<string, unknown>;
};

export type ParsingPipelineTrace = {
  trace_id: string;
  artifact_id: string;
  owner_user_id: string;
  job_id?: string | null;
  source_format: string;
  requested_extractor: string;
  extractor_chosen: string;
  fallback_path: string[];
  warnings: string[];
  char_count: number;
  token_count_estimate: number;
  confidence: number;
  text_sha256?: string | null;
  text_storage_ref?: string | null;
  text_dataset_id?: string | null;
  page_count?: number | null;
  steps: ExtractionStepTrace[];
  metadata: Record<string, unknown>;
  started_at: string;
  completed_at?: string | null;
};

export type UploadParseJobResponse = {
  job: BackgroundJob;
  artifact: UploadedArtifact;
  trace?: ParsingPipelineTrace | null;
  extracted_document?: ExtractedDocument | null;
};

export type RetrievalReindexJobPayload = RetrievalReindexPayload & {
  execute_now?: boolean;
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

export type MigrationDiagnosticItem = {
  version: string;
  name: string;
  checksum?: string | null;
  status: "applied" | "pending" | "checksum_mismatch" | "unknown_applied";
  applied_at?: string | null;
  duration_ms?: number | null;
  failure_reason?: string | null;
};

export type MigrationDiagnostics = {
  status: "ok" | "warning" | "error" | "not_required";
  storage_backend: string;
  required: boolean;
  postgres_configured: boolean;
  dependency_available: boolean;
  connection_ok?: boolean | null;
  table_exists: boolean;
  manifest_count: number;
  applied_count: number;
  pending_count: number;
  unknown_applied_count: number;
  checksum_mismatch_count: number;
  latest_available_version?: string | null;
  latest_applied_version?: string | null;
  bootstrap_code?: string | null;
  bootstrap_summary: string;
  migrations: MigrationDiagnosticItem[];
};

export type RuntimeRetrievalSettings = {
  embedding_provider: "deterministic" | "openai" | "huggingface";
  embedding_model: string;
  embedding_dimensions: number;
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

export type RuntimeRetrievalRulePack = {
  name: string;
  status: "ok" | "missing" | "error";
  source: "knowledge" | "override" | string;
  env_var: string;
  configured: boolean;
  rule_count: number;
  version?: string | null;
  content_hash?: string | null;
  error?: string;
};

export type RuntimeAssistantSettings = {
  llm_provider: "disabled" | "openai";
  llm_model: string;
  llm_planning_model: string;
  llm_synthesis_model: string;
  llm_vision_model: string;
  llm_base_url: string;
  llm_timeout_seconds: number;
  llm_max_tool_calls: number;
  llm_planning_progress_interval_seconds: number;
  external_openai_llm_enabled: boolean;
  external_openai_llm_allow_phi: boolean;
  external_openai_ocr_enabled: boolean;
  external_openai_ocr_allow_phi: boolean;
  external_openai_ocr_allow_unknown: boolean;
  external_openai_embeddings_enabled: boolean;
  external_openai_embeddings_allow_phi: boolean;
  external_medical_search_enabled: boolean;
  external_medical_search_allow_phi: boolean;
};

export type RuntimeAssistantSettingsPayload = Partial<RuntimeAssistantSettings>;

export type RuntimeAssistantSettingsUpdate = {
  settings: RuntimeAssistantSettings;
  reloaded: boolean;
};

export type AiRmfFunction = "GOVERN" | "MAP" | "MEASURE" | "MANAGE";

export type AiRiskLevel = "low" | "medium" | "high" | "critical";

export type AiRiskControl = {
  control_id: string;
  title: string;
  implementation_ref: string;
  status: "implemented" | "partial" | "planned";
};

export type AiRiskRegisterItem = {
  risk_id: string;
  title: string;
  intended_use: string;
  limitation: string;
  nist_ai_rmf_functions: AiRmfFunction[];
  genai_profile_risk_areas: string[];
  severity: AiRiskLevel;
  likelihood: AiRiskLevel;
  residual_risk: AiRiskLevel;
  owner_role: string;
  monitoring_signals: string[];
  human_oversight: string;
  controls: AiRiskControl[];
  evidence_refs: string[];
};

export type AiRiskRegister = {
  version: string;
  standard_refs: string[];
  intended_system_use: string;
  prohibited_uses: string[];
  risks: AiRiskRegisterItem[];
};

export type OwaspLlmCategoryId =
  | "LLM01"
  | "LLM02"
  | "LLM03"
  | "LLM04"
  | "LLM05"
  | "LLM06"
  | "LLM07"
  | "LLM08"
  | "LLM09"
  | "LLM10";

export type OwaspMitigationStatus = "implemented" | "partial" | "planned";

export type ThreatRiskLevel = "low" | "medium" | "high" | "critical";

export type OwaspLlmMitigation = {
  mitigation_id: string;
  title: string;
  status: OwaspMitigationStatus;
  owner_role: string;
  implementation_refs: string[];
  test_refs: string[];
  notes: string;
};

export type OwaspLlmThreatCategory = {
  category_id: OwaspLlmCategoryId;
  category_name: string;
  owasp_ref: string;
  risk_statement: string;
  applicable_surfaces: string[];
  mitigations: OwaspLlmMitigation[];
  monitoring_signals: string[];
  residual_risk: ThreatRiskLevel;
  residual_risk_note: string;
  roadmap_refs: string[];
  evidence_refs: string[];
};

export type OwaspLlmThreatModel = {
  version: string;
  standard_ref: string;
  source_url: string;
  categories: OwaspLlmThreatCategory[];
};

export type DisclaimerSeverity = "info" | "caution" | "critical";

export type DisclaimerSurface =
  | "global"
  | "assistant"
  | "workbench"
  | "workflows"
  | "workflow_detail"
  | "reviews"
  | "retrieval"
  | "audit"
  | "schemas"
  | "settings"
  | "help";

export type DisclaimerMessage = {
  surface_id: DisclaimerSurface;
  title: string;
  message: string;
  severity: DisclaimerSeverity;
  review_required: boolean;
  prohibited_uses: string[];
  human_review_text: string;
  evidence_text: string;
};

export type DisclaimerPolicy = {
  version: string;
  intended_use: string;
  non_diagnostic_statement: string;
  human_review_requirement: string;
  prohibited_uses: string[];
  surfaces: DisclaimerMessage[];
};

export type RuntimeConfig = {
  status: string;
  product_mode: "local_dev" | "demo" | "pilot" | "production";
  storage_backend: string;
  persistent_storage: boolean;
  postgres_configured: boolean;
  redis_configured: boolean;
  data_dir_configured: boolean;
  audit?: {
    hash_chain_written: boolean;
    hash_chain_required: boolean;
    hash_chain_required_configured: boolean;
  };
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
    planning_model?: string;
    synthesis_model?: string;
    vision_model?: string;
    openai_configured: boolean;
    base_url?: string;
    base_url_configured: boolean;
    timeout_seconds: number;
    max_tool_calls: number;
    planning_progress_interval_seconds?: number;
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
    rule_packs?: RuntimeRetrievalRulePack[];
  };
  upload: {
    max_upload_bytes: number;
    max_inline_data_bytes: number;
    read_chunk_bytes: number;
    allowed_extensions: string[];
  };
  retention?: {
    artifact_rule_count: number;
    artifact_policy_configured: boolean;
  };
  tools?: {
    registered_count: number;
    approval_required_count: number;
    write_gates_enabled: boolean;
  };
  rate_limit?: {
    enabled: boolean;
    backend: "auto" | "memory" | "redis" | string;
    policy_configured: boolean;
    redis_prefix_configured: boolean;
  };
  cost_controls?: {
    policy_configured: boolean;
    llm_max_request_chars: number;
    ocr_max_openai_vision_bytes: number;
    embedding_max_request_inputs: number;
    embedding_max_request_chars: number;
    batch_max_total_bytes: number;
  };
  review_policy?: {
    default_human_review_required: boolean;
    ocr_low_confidence_threshold: number;
  };
  policy: {
    no_mock_data: boolean;
    effective_no_mock_data: boolean;
    requires_real_llm: boolean;
    requires_persistent_storage: boolean;
  };
};
