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
  filters_applied: Record<string, unknown>;
  candidates_seen: number;
  final_hit_ids: string[];
  safety_flags: string[];
  warnings: string[];
};

export type RetrievalHit = {
  evidence: Evidence;
  score: number;
  lexical_score: number;
  vector_score: number;
  rerank_score: number;
  matched_terms: string[];
  source_locator: Record<string, unknown>;
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
  expanded_terms: string[];
  standards: string[];
  rule_ids: string[];
  query_variants: string[];
};

export type RetrievalPackage = {
  hits: RetrievalHit[];
  evidence: Evidence[];
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
  filters: Record<string, unknown>;
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
    corpus_dir_count: number;
    chunk_max_chars: number;
    chunk_overlap_chars: number;
    diversity_enabled?: boolean;
    diversity_lambda?: number;
  };
  upload: {
    max_upload_bytes: number;
    max_inline_data_bytes: number;
    read_chunk_bytes: number;
    allowed_extensions: string[];
  };
};
