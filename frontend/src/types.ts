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
  token_type: "bearer";
  access_token: string;
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

export type ValidationIssue = {
  issue_id: string;
  kind: string;
  severity: string;
  message: string;
  field?: string | null;
  row?: number | null;
  source_ref?: string | null;
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
  audit_event_refs: string[];
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
