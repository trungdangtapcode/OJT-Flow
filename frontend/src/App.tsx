import {
  AlertTriangle,
  ArrowRight,
  Check,
  ClipboardCheck,
  Database,
  FileCode,
  FileSearch,
  FileUp,
  History,
  Layers,
  Loader2,
  Play,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  API_BASE_URL,
  createWorkflow,
  getWorkflow,
  listReviews,
  listSchemas,
  listWorkflowEvents,
  listWorkflows,
  submitReview,
  uploadFileWorkflow,
} from "./api";
import type { SchemaEntry, WorkflowEvent, WorkflowState } from "./types";

const sampleCsv =
  "date,patient_id,lab_name,value,unit\n" +
  "2026-01-01,P001,HbA1c,7.4,%\n" +
  "2026/01/02,P002,HbA1c,,\n" +
  "2026-01-03,P003,LDL,131,\n";

type View = "workbench" | "workflows" | "reviews" | "schemas" | "audit" | "settings";

type LoadState = {
  loading: boolean;
  error: string | null;
};

const navItems: Array<{ id: View; label: string; icon: React.ElementType }> = [
  { id: "workbench", label: "Workbench", icon: Play },
  { id: "workflows", label: "Workflows", icon: Layers },
  { id: "reviews", label: "Reviews", icon: ClipboardCheck },
  { id: "schemas", label: "Schemas", icon: Database },
  { id: "audit", label: "Audit", icon: History },
  { id: "settings", label: "Settings", icon: SlidersHorizontal },
];

function App() {
  const [view, setView] = useState<View>("workbench");
  const [workflows, setWorkflows] = useState<WorkflowState[]>([]);
  const [reviews, setReviews] = useState<WorkflowState[]>([]);
  const [schemas, setSchemas] = useState<SchemaEntry[]>([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowState | null>(null);
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [loadState, setLoadState] = useState<LoadState>({ loading: false, error: null });

  const refresh = useCallback(async () => {
    setLoadState({ loading: true, error: null });
    try {
      const [workflowData, reviewData, schemaData] = await Promise.all([
        listWorkflows(),
        listReviews("pending"),
        listSchemas(),
      ]);
      setWorkflows(workflowData);
      setReviews(reviewData);
      setSchemas(schemaData);
      const nextWorkflowId = selectedWorkflowId ?? workflowData[0]?.workflow_id ?? null;
      if (nextWorkflowId) {
        const [workflow, workflowEvents] = await Promise.all([
          getWorkflow(nextWorkflowId),
          listWorkflowEvents(nextWorkflowId),
        ]);
        setSelectedWorkflowId(nextWorkflowId);
        setSelectedWorkflow(workflow);
        setEvents(workflowEvents);
      }
      setLoadState({ loading: false, error: null });
    } catch (error) {
      setLoadState({ loading: false, error: error instanceof Error ? error.message : String(error) });
    }
  }, [selectedWorkflowId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const selectWorkflow = async (workflowId: string) => {
    setSelectedWorkflowId(workflowId);
    setLoadState({ loading: true, error: null });
    try {
      const [workflow, workflowEvents] = await Promise.all([
        getWorkflow(workflowId),
        listWorkflowEvents(workflowId),
      ]);
      setSelectedWorkflow(workflow);
      setEvents(workflowEvents);
      setLoadState({ loading: false, error: null });
    } catch (error) {
      setLoadState({ loading: false, error: error instanceof Error ? error.message : String(error) });
    }
  };

  const handleWorkflowCreated = async (workflow: WorkflowState) => {
    setSelectedWorkflowId(workflow.workflow_id);
    setSelectedWorkflow(workflow);
    setView("workflows");
    const workflowEvents = await listWorkflowEvents(workflow.workflow_id);
    setEvents(workflowEvents);
    await refresh();
  };

  const handleReviewDecision = async (reviewId: string, decision: string) => {
    setLoadState({ loading: true, error: null });
    try {
      const workflow = await submitReview(reviewId, decision);
      setSelectedWorkflowId(workflow.workflow_id);
      setSelectedWorkflow(workflow);
      const workflowEvents = await listWorkflowEvents(workflow.workflow_id);
      setEvents(workflowEvents);
      await refresh();
      setLoadState({ loading: false, error: null });
    } catch (error) {
      setLoadState({ loading: false, error: error instanceof Error ? error.message : String(error) });
    }
  };

  const stats = useMemo(() => buildStats(workflows, reviews), [workflows, reviews]);

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">
          <div className="brand-mark">OF</div>
          <div>
            <div className="brand-name">OJTFlow</div>
            <div className="brand-subtitle">Healthcare data workflow</div>
          </div>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={view === item.id ? "nav-item active" : "nav-item"}
                onClick={() => setView(item.id)}
                title={item.label}
                type="button"
              >
                <Icon size={18} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>{pageTitle(view)}</h1>
            <p>{pageSubtitle(view)}</p>
          </div>
          <div className="topbar-actions">
            <span className="api-chip">API {API_BASE_URL}</span>
            <button className="icon-button" onClick={() => void refresh()} title="Refresh data" type="button">
              {loadState.loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
            </button>
          </div>
        </header>

        {loadState.error ? (
          <div className="error-banner" role="alert">
            <AlertTriangle size={18} />
            <span>{loadState.error}</span>
          </div>
        ) : null}

        <section className="metric-strip" aria-label="Workflow summary">
          {stats.map((stat) => (
            <div className="metric" key={stat.label}>
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </div>
          ))}
        </section>

        {view === "workbench" ? (
          <Workbench schemas={schemas} onCreated={(workflow) => void handleWorkflowCreated(workflow)} />
        ) : null}
        {view === "workflows" ? (
          <WorkflowSurface
            workflows={workflows}
            selectedWorkflow={selectedWorkflow}
            events={events}
            onSelect={(workflowId) => void selectWorkflow(workflowId)}
            onReviewDecision={(reviewId, decision) => void handleReviewDecision(reviewId, decision)}
          />
        ) : null}
        {view === "reviews" ? (
          <ReviewQueue
            reviews={reviews}
            onOpen={(workflowId) => {
              setView("workflows");
              void selectWorkflow(workflowId);
            }}
          />
        ) : null}
        {view === "schemas" ? <SchemaRegistry schemas={schemas} /> : null}
        {view === "audit" ? (
          <AuditSurface workflows={workflows} selectedWorkflow={selectedWorkflow} events={events} onSelect={selectWorkflow} />
        ) : null}
        {view === "settings" ? <SettingsSurface /> : null}
      </main>
    </div>
  );
}

function Workbench({
  schemas,
  onCreated,
}: {
  schemas: SchemaEntry[];
  onCreated: (workflow: WorkflowState) => void;
}) {
  const [mode, setMode] = useState<"text" | "file">("text");

  // Text mode state
  const [instruction, setInstruction] = useState("Clean this CSV, convert it to JSON, and explain anomalies.");
  const [data, setData] = useState(sampleCsv);
  const [inputFormat, setInputFormat] = useState("csv");
  const [targetFormat, setTargetFormat] = useState("json");
  const [schemaId, setSchemaId] = useState("lab_result_v1");
  const [requireReview, setRequireReview] = useState(true);

  // File mode state
  const [file, setFile] = useState<File | null>(null);
  const [fileInstruction, setFileInstruction] = useState("Extract and validate the content of this document.");
  const [fileTargetFormat, setFileTargetFormat] = useState("json");
  const [fileSchemaId, setFileSchemaId] = useState("");
  const [fileRequireReview, setFileRequireReview] = useState(true);
  const [extractor, setExtractor] = useState("auto");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitText = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const workflow = await createWorkflow({
        instruction,
        data,
        input_format: inputFormat === "auto" ? null : inputFormat,
        target_format: targetFormat,
        schema_id: schemaId || null,
        require_human_review: requireReview,
      });
      onCreated(workflow);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  const submitFile = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) { setError("Please select a file first."); return; }
    setSubmitting(true);
    setError(null);
    try {
      const workflow = await uploadFileWorkflow(file, {
        instruction: fileInstruction,
        targetFormat: fileTargetFormat,
        schemaId: fileSchemaId || null,
        requireHumanReview: fileRequireReview,
        extractor,
      });
      onCreated(workflow);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="workbench-layout">
      <form
        className="panel intake-panel"
        onSubmit={(event) => void (mode === "file" ? submitFile(event) : submitText(event))}
      >
        <div className="panel-heading">
          <FileCode size={20} />
          <div>
            <h2>Workflow intake</h2>
            <p>Structured healthcare data in, auditable workflow out.</p>
          </div>
        </div>

        {/* Mode toggle */}
        <div className="mode-toggle">
          <button
            type="button"
            className={mode === "text" ? "mode-btn active" : "mode-btn"}
            onClick={() => { setMode("text"); setError(null); }}
          >
            <FileCode size={15} /> Text / paste
          </button>
          <button
            type="button"
            className={mode === "file" ? "mode-btn active" : "mode-btn"}
            onClick={() => { setMode("file"); setError(null); }}
          >
            <FileUp size={15} /> Upload file
          </button>
        </div>

        {mode === "text" ? (
          <>
            <label>
              Instruction
              <input value={instruction} onChange={(event) => setInstruction(event.target.value)} />
            </label>

            <div className="field-grid">
              <label>
                Source
                <select value={inputFormat} onChange={(event) => setInputFormat(event.target.value)}>
                  <option value="auto">Auto detect</option>
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                  <option value="yaml">YAML</option>
                </select>
              </label>
              <label>
                Target
                <select value={targetFormat} onChange={(event) => setTargetFormat(event.target.value)}>
                  <option value="json">JSON</option>
                  <option value="yaml">YAML</option>
                  <option value="csv">CSV</option>
                </select>
              </label>
              <label>
                Schema
                <select value={schemaId} onChange={(event) => setSchemaId(event.target.value)}>
                  <option value="">No schema</option>
                  {schemas.map((schema) => (
                    <option key={schema.schema_id} value={schema.schema_id}>
                      {schema.schema_id}
                    </option>
                  ))}
                </select>
              </label>
              <label className="switch-row">
                <input
                  checked={requireReview}
                  onChange={(event) => setRequireReview(event.target.checked)}
                  type="checkbox"
                />
                Human review
              </label>
            </div>

            <label>
              Source data
              <textarea value={data} onChange={(event) => setData(event.target.value)} spellCheck={false} />
            </label>
          </>
        ) : (
          <>
            <label>
              Instruction
              <input value={fileInstruction} onChange={(event) => setFileInstruction(event.target.value)} />
            </label>

            <div className="field-grid">
              <label>
                Extractor
                <select value={extractor} onChange={(event) => setExtractor(event.target.value)}>
                  <option value="auto">Auto (markitdown → minerU)</option>
                  <option value="markitdown">markitdown</option>
                  <option value="mineru">minerU</option>
                </select>
              </label>
              <label>
                Target
                <select value={fileTargetFormat} onChange={(event) => setFileTargetFormat(event.target.value)}>
                  <option value="json">JSON</option>
                  <option value="yaml">YAML</option>
                  <option value="csv">CSV</option>
                </select>
              </label>
              <label>
                Schema
                <select value={fileSchemaId} onChange={(event) => setFileSchemaId(event.target.value)}>
                  <option value="">No schema</option>
                  {schemas.map((schema) => (
                    <option key={schema.schema_id} value={schema.schema_id}>
                      {schema.schema_id}
                    </option>
                  ))}
                </select>
              </label>
              <label className="switch-row">
                <input
                  checked={fileRequireReview}
                  onChange={(event) => setFileRequireReview(event.target.checked)}
                  type="checkbox"
                />
                Human review
              </label>
            </div>

            {/* File drop zone */}
            <div
              className={`drop-zone ${file ? "has-file" : ""}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const dropped = e.dataTransfer.files[0];
                if (dropped) setFile(dropped);
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.png,.jpg,.jpeg,.tiff,.html,.md,.txt,.csv,.json,.yaml"
                style={{ display: "none" }}
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              {file ? (
                <div className="file-selected">
                  <FileUp size={20} />
                  <div>
                    <strong>{file.name}</strong>
                    <small>{(file.size / 1024).toFixed(1)} KB</small>
                  </div>
                  <button
                    type="button"
                    className="icon-button"
                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <div className="drop-hint">
                  <FileUp size={24} />
                  <span>Click or drag a file here</span>
                  <small>PDF, DOCX, XLSX, PPTX, PNG, JPG, CSV, JSON…</small>
                </div>
              )}
            </div>
          </>
        )}

        {error ? <div className="inline-error">{error}</div> : null}

        <button className="primary-button" disabled={submitting} type="submit">
          {submitting ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
          Start workflow
        </button>
      </form>

      <div className="panel product-frame">
        <div className="panel-heading">
          <ShieldCheck size={20} />
          <div>
            <h2>Operating model</h2>
            <p>Built for B2B healthcare data teams and reviewer-controlled decisions.</p>
          </div>
        </div>
        <div className="persona-grid">
          {[
            ["Implementation analyst", "Onboard messy customer files without one-off scripts."],
            ["Integration engineer", "Inspect schemas, hashes, diffs, and API-ready output."],
            ["Clinical reviewer", "Approve medically meaningful changes with evidence in view."],
            ["Compliance reviewer", "Reconstruct decisions from event timelines and artifacts."],
          ].map(([title, body]) => (
            <div className="persona" key={title}>
              <strong>{title}</strong>
              <span>{body}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function WorkflowSurface({
  workflows,
  selectedWorkflow,
  events,
  onSelect,
  onReviewDecision,
}: {
  workflows: WorkflowState[];
  selectedWorkflow: WorkflowState | null;
  events: WorkflowEvent[];
  onSelect: (workflowId: string) => void;
  onReviewDecision: (reviewId: string, decision: string) => void;
}) {
  return (
    <div className="workflow-layout">
      <div className="panel list-panel">
        <h2>Workflow runs</h2>
        <div className="table-list">
          {workflows.map((workflow) => (
            <button
              className={
                selectedWorkflow?.workflow_id === workflow.workflow_id ? "list-row selected" : "list-row"
              }
              key={workflow.workflow_id}
              onClick={() => onSelect(workflow.workflow_id)}
              type="button"
            >
              <span>
                <strong>{workflow.workflow_id}</strong>
                <small>{workflow.user_instruction}</small>
              </span>
              <StatusBadge status={workflow.status} />
            </button>
          ))}
        </div>
      </div>

      <WorkflowDetail workflow={selectedWorkflow} events={events} onReviewDecision={onReviewDecision} />
    </div>
  );
}

function WorkflowDetail({
  workflow,
  events,
  onReviewDecision,
}: {
  workflow: WorkflowState | null;
  events: WorkflowEvent[];
  onReviewDecision: (reviewId: string, decision: string) => void;
}) {
  if (!workflow) {
    return (
      <div className="panel empty-panel">
        <FileSearch size={28} />
        <p>No workflow selected.</p>
      </div>
    );
  }

  const issues = workflow.validation_report?.issues ?? [];
  const output = workflow.output?.transformation;

  return (
    <div className="detail-stack">
      <div className="panel workflow-header">
        <div>
          <div className="eyebrow">Workflow</div>
          <h2>{workflow.workflow_id}</h2>
          <p>{workflow.user_instruction}</p>
        </div>
        <StatusBadge status={workflow.status} />
      </div>

      <div className="detail-grid">
        <div className="panel">
          <h3>Steps</h3>
          <ol className="step-list">
            {workflow.steps.map((step) => (
              <li key={step.step_id}>
                <span className={`step-dot ${step.status}`} />
                <div>
                  <strong>{humanize(step.name)}</strong>
                  <small>{step.summary}</small>
                </div>
                <em>{step.issue_count}</em>
              </li>
            ))}
          </ol>
        </div>

        <div className="panel">
          <h3>Validation issues</h3>
          <IssueTable issues={issues} />
        </div>

        <div className="panel inspector">
          <h3>Evidence</h3>
          <div className="evidence-list">
            {workflow.retrieved_context.map((evidence) => (
              <div className="evidence" key={evidence.evidence_id}>
                <strong>{evidence.source_id}</strong>
                <span>{evidence.claim}</span>
                <small>
                  {evidence.source_type} / {evidence.trust_level}
                </small>
              </div>
            ))}
          </div>
        </div>
      </div>

      {workflow.review && workflow.status === "needs_human_review" ? (
        <div className="panel review-panel">
          <div>
            <h3>{workflow.review.question}</h3>
            <p>
              Trigger: {workflow.review.trigger}. Review ID: {workflow.review.review_id}
            </p>
          </div>
          <div className="decision-row">
            {workflow.review.allowed_decisions.map((decision) => (
              <button
                className={decision === "approve" ? "primary-button compact" : "secondary-button compact"}
                key={decision}
                onClick={() => onReviewDecision(workflow.review!.review_id, decision)}
                type="button"
              >
                {decision === "approve" ? <Check size={16} /> : <X size={16} />}
                {humanize(decision)}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="detail-grid two">
        <div className="panel">
          <h3>Output</h3>
          {output ? (
            <dl className="kv">
              <dt>Format</dt>
              <dd>{output.output_format}</dd>
              <dt>Output ref</dt>
              <dd>{output.output_ref ?? "not stored"}</dd>
              <dt>Output hash</dt>
              <dd>{output.output_hash ?? "not generated"}</dd>
              <dt>Warnings</dt>
              <dd>{output.warnings.length ? output.warnings.join(", ") : "none"}</dd>
            </dl>
          ) : (
            <p className="muted">Output appears after approval or safe completion.</p>
          )}
        </div>
        <div className="panel">
          <h3>Explanation</h3>
          {workflow.explanation ? (
            <div className="explanation">
              <p>{workflow.explanation.summary}</p>
              <strong>Limitations</strong>
              <ul>
                {workflow.explanation.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="muted">Explanation is generated after transformation.</p>
          )}
        </div>
      </div>

      <div className="panel">
        <h3>Audit timeline</h3>
        <EventTimeline events={events} />
      </div>
    </div>
  );
}

function ReviewQueue({
  reviews,
  onOpen,
}: {
  reviews: WorkflowState[];
  onOpen: (workflowId: string) => void;
}) {
  return (
    <div className="panel">
      <h2>Pending reviews</h2>
      <div className="data-table">
        <div className="table-head five">
          <span>Workflow</span>
          <span>Trigger</span>
          <span>Issues</span>
          <span>Updated</span>
          <span>Action</span>
        </div>
        {reviews.map((workflow) => (
          <div className="table-row five" key={workflow.workflow_id}>
            <span>{workflow.workflow_id}</span>
            <span>{workflow.review?.trigger}</span>
            <span>{workflow.validation_report?.issues.length ?? 0}</span>
            <span>{formatDate(workflow.updated_at)}</span>
            <button className="secondary-button compact" onClick={() => onOpen(workflow.workflow_id)} type="button">
              <ArrowRight size={16} />
              Open
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function SchemaRegistry({ schemas }: { schemas: SchemaEntry[] }) {
  return (
    <div className="schema-grid">
      {schemas.map((schema) => (
        <div className="panel" key={schema.schema_id}>
          <div className="panel-heading">
            <Database size={20} />
            <div>
              <h2>{schema.schema_id}</h2>
              <p>
                {schema.title} / {schema.version}
              </p>
            </div>
          </div>
          <dl className="kv">
            <dt>Required</dt>
            <dd>{schema.required.join(", ")}</dd>
            <dt>Fields</dt>
            <dd>{schema.field_count}</dd>
            <dt>Source</dt>
            <dd>{schema.source_ref}</dd>
          </dl>
          <div className="field-list">
            {schema.fields.map((field) => (
              <span key={field.name}>
                <strong>{field.name}</strong>
                <small>{field.type}</small>
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function AuditSurface({
  workflows,
  selectedWorkflow,
  events,
  onSelect,
}: {
  workflows: WorkflowState[];
  selectedWorkflow: WorkflowState | null;
  events: WorkflowEvent[];
  onSelect: (workflowId: string) => void;
}) {
  return (
    <div className="workflow-layout">
      <div className="panel list-panel">
        <h2>Audit search</h2>
        <div className="table-list">
          {workflows.map((workflow) => (
            <button className="list-row" key={workflow.workflow_id} onClick={() => onSelect(workflow.workflow_id)} type="button">
              <span>
                <strong>{workflow.workflow_id}</strong>
                <small>{formatDate(workflow.updated_at)}</small>
              </span>
              <StatusBadge status={workflow.status} />
            </button>
          ))}
        </div>
      </div>
      <div className="detail-stack">
        <div className="panel">
          <h2>Audit packet</h2>
          {selectedWorkflow ? (
            <dl className="kv">
              <dt>Input hash</dt>
              <dd>{selectedWorkflow.input?.input_hash ?? "none"}</dd>
              <dt>Output hash</dt>
              <dd>{selectedWorkflow.output?.transformation?.output_hash ?? "none"}</dd>
              <dt>Review</dt>
              <dd>{selectedWorkflow.review?.status ?? "none"}</dd>
              <dt>Events</dt>
              <dd>{events.length}</dd>
            </dl>
          ) : (
            <p className="muted">Select a workflow to reconstruct it.</p>
          )}
        </div>
        <div className="panel">
          <h3>Event trace</h3>
          <EventTimeline events={events} />
        </div>
      </div>
    </div>
  );
}

function SettingsSurface() {
  return (
    <div className="settings-grid">
      {[
        ["Tenant and workspace", "Reserved for B2B account isolation, project context, and customer boundaries."],
        ["Roles and review policy", "Reserved for reviewer assignment, approval rules, and least-privilege scopes."],
        ["Integrations", "Reserved for API keys, webhooks, FHIR exports, storage destinations, and audit packet sinks."],
        ["Runtime credentials", "Use environment variables or mounted ADC credentials. Do not commit secrets to the repo."],
      ].map(([title, body]) => (
        <div className="panel" key={title}>
          <h2>{title}</h2>
          <p>{body}</p>
        </div>
      ))}
    </div>
  );
}

function IssueTable({ issues }: { issues: Array<{ issue_id: string; severity: string; kind: string; field?: string | null; row?: number | null; message: string; requires_review: boolean }> }) {
  if (!issues.length) {
    return <p className="muted">No validation issues recorded.</p>;
  }
  return (
    <div className="data-table">
      <div className="table-head five">
        <span>Severity</span>
        <span>Kind</span>
        <span>Field</span>
        <span>Row</span>
        <span>Message</span>
      </div>
      {issues.map((issue) => (
        <div className="table-row five" key={issue.issue_id}>
          <SeverityBadge severity={issue.severity} />
          <span>{issue.kind}</span>
          <span>{issue.field ?? "-"}</span>
          <span>{issue.row ?? "-"}</span>
          <span>{issue.message}</span>
        </div>
      ))}
    </div>
  );
}

function EventTimeline({ events }: { events: WorkflowEvent[] }) {
  if (!events.length) {
    return <p className="muted">No events loaded.</p>;
  }
  return (
    <ol className="event-list">
      {events.map((event) => (
        <li key={event.event_id}>
          <span className={`event-severity ${event.severity}`} />
          <div>
            <strong>{event.event_type}</strong>
            <small>
              {formatDate(event.timestamp)} / {event.actor_type}:{event.actor_id}
            </small>
            <p>{event.summary}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

function StatusBadge({ status }: { status: string }) {
  return <span className={`status-badge ${status}`}>{humanize(status)}</span>;
}

function SeverityBadge({ severity }: { severity: string }) {
  return <span className={`severity-badge ${severity}`}>{severity}</span>;
}

function buildStats(workflows: WorkflowState[], reviews: WorkflowState[]) {
  return [
    { label: "Workflows", value: workflows.length },
    { label: "Pending reviews", value: reviews.length },
    { label: "Completed", value: workflows.filter((workflow) => workflow.status === "completed").length },
    { label: "Review gated", value: workflows.filter((workflow) => workflow.review).length },
  ];
}

function pageTitle(view: View) {
  const titles: Record<View, string> = {
    workbench: "Workbench",
    workflows: "Workflow operations",
    reviews: "Review queue",
    schemas: "Schema registry",
    audit: "Audit",
    settings: "Settings",
  };
  return titles[view];
}

function pageSubtitle(view: View) {
  const subtitles: Record<View, string> = {
    workbench: "Create governed data workflows from messy healthcare inputs.",
    workflows: "Inspect state, issues, evidence, reviews, output, and events.",
    reviews: "Approve or reject risky transformations with context visible.",
    schemas: "Trusted schema and field definitions for retrieval and validation.",
    audit: "Reconstruct workflow decisions from hashes, reviews, and event timelines.",
    settings: "B2B operating surfaces for deployment, roles, integrations, and security.",
  };
  return subtitles[view];
}

function humanize(value: string) {
  return value.replaceAll("_", " ").replaceAll(".", " ");
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export default App;
