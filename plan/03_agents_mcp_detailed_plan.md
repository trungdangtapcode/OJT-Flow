# Agents, MCP, and Human Review Detailed Plan

The agent layer should coordinate deterministic tools without becoming a free-form black box. Agents decide what to do next, but tools execute typed operations and validators check the result.

## Agent Design Rule

Each agent is a role-specific workflow node with:

- explicit input fields
- allowed tools
- structured output contract
- confidence or sufficiency signal
- issue list
- evidence list
- next recommended action
- audit event emission

Agents should never communicate only through prose.

## Agent Roles

| Agent | Responsibility | Allowed tools |
| --- | --- | --- |
| Orchestrator | Classify intent, plan workflow, manage state, route agents, pause/resume | Tool registry, workflow repository |
| Input Parser | Detect format, parse data, profile input | parse, profile |
| Schema Agent | Infer schema, retrieve candidate schemas, compare fields, estimate confidence | infer_schema, compare_schema, search_context |
| Validation Agent | Validate syntax, types, required fields, policy issues | validate_schema, detect_anomalies |
| Transformation Agent | Convert and apply approved cleaning plan | convert, diff, export |
| Retrieval Agent | Search trusted schemas, examples, docs, dictionaries, error guidance | search_context, get_schema_docs, rerank_context |
| Explanation Agent | Produce user-facing explanation from evidence and reports | evidence_pack, claim_check |
| Safety Agent | Check prompt injection, sensitive fields, tool permissions, review needs | risk_rules, mask_preview |
| Clinical Explainability Agent | Build healthcare explanation with intended use, limitations, uncertainty, review recommendation | claim_check, clinical_template |
| Human Review Agent | Create review request and apply decision | request_review, record_decision |

## Orchestrator Backbone

The orchestrator should be deterministic enough to test. It can use an LLM for intent parsing later, but it must not depend on an LLM for basic routing.

Initial routing:

```text
start
  -> safety.precheck
  -> parser
  -> retrieval
  -> schema
  -> validation
  -> safety.review_decision
  -> human_review if needed
  -> transformation if approved or no review needed
  -> validation.post_transform
  -> explanation
  -> audit_summary
  -> complete
```

## Agent Result Contract

All agents must return:

```json
{
  "status": "success",
  "summary": "Short human-readable summary",
  "confidence": 0.88,
  "data": {},
  "issues": [],
  "evidence": [],
  "next_recommended_action": "validation_agent"
}
```

Errors should be recoverable where possible:

- parser can return `error` with parse details
- retrieval can return `warning` with empty context
- schema can return `needs_human_review` for ambiguous candidates
- validation can return `needs_human_review` for risky cleaning
- safety can return `blocked_by_policy`

## Tool Registry

The tool registry should map tool names to:

- implementation function
- input model
- output model
- permission scope
- agent allowlist
- approval rule
- audit rule

Example:

```json
{
  "name": "convert_csv_to_json",
  "permission_scope": "data:transform",
  "allowed_agents": ["transformation_agent"],
  "requires_approval": "when_cleaning_changes_values",
  "input_model": "ConvertCsvToJsonInput",
  "output_model": "ConvertCsvToJsonOutput",
  "audit_level": "standard"
}
```

## MCP Strategy

Build direct Python services first. Wrap stable services as MCP servers after contracts stop changing.

### MCP Server Families

| Server | Resources | Tools | Prompts |
| --- | --- | --- | --- |
| `structured-data-server` | dataset refs, sample rows, format metadata | `parse_data`, `convert_csv_json`, `convert_json_yaml`, `export_file` | conversion error templates |
| `schema-validation-server` | schema registry, JSON Schema, Pydantic models | `infer_schema`, `validate_schema`, `compare_schema`, `detect_anomalies` | validation summary templates |
| `rag-context-server` | docs, chunks, data dictionaries, examples | `search_context`, `get_schema_docs`, `get_examples`, `rerank_context` | grounded explanation templates |
| `workflow-audit-server` | event stream, approval history, diffs | `record_event`, `fetch_history`, `generate_audit_report` | audit summary templates |
| `human-review-server` | pending reviews, issue reports | `request_approval`, `record_decision`, `update_plan` | review prompt templates |

### MCP MVP Transport

- Local development: stdio.
- Service deployment: Streamable HTTP later.
- Keep direct internal Python calls available for tests.

## Human Review Flow

Human review is triggered by policy and risk rules.

Flow:

1. Safety or validation agent identifies review trigger.
2. Orchestrator creates `ReviewRequest`.
3. Workflow status becomes `needs_human_review`.
4. API returns review ID and proposed action.
5. User approves, edits, rejects, or asks for clarification.
6. Decision is stored as evidence and audit event.
7. Orchestrator resumes or cancels.

Decision types:

- `approve`
- `approve_with_edits`
- `reject`
- `clarify`
- `cancel`

Review prompt should include:

- proposed action
- affected rows/fields
- why review is required
- evidence supporting the suggestion
- risks and limitations
- options

## Safety Agent Rules

The safety agent checks:

- prompt injection patterns in user data or retrieved text
- sensitive fields or PHI-like content
- external tool call requests
- data export request
- destructive transformations
- low schema confidence
- low retrieval confidence
- unsupported medical claims
- large/costly operations

The safety agent can return:

- `allow`
- `allow_with_warning`
- `needs_human_review`
- `mask_before_continue`
- `blocked_by_policy`

## Explanation Agent Rules

The explanation agent receives:

- validation report
- transformation diff
- retrieved context
- evidence package
- audit trace summary
- review decisions
- output metadata

It must produce:

- short summary
- what changed
- what did not change
- validation findings
- evidence sources
- uncertainty and limitations
- review decisions
- next suggested user action if needed

It must not:

- invent schema rules
- hide unsupported claims
- present chain-of-thought as evidence
- claim clinical diagnosis or treatment recommendation

## Clinical Explainability Contract

For healthcare workflows, attach:

```json
{
  "answer_type": "data_transformation_explanation",
  "intended_use": "Support data validation and review; not autonomous diagnosis",
  "supported_claims": [],
  "unsupported_claims": [],
  "data_quality_flags": [],
  "uncertainty": {
    "retrieval_confidence": "medium",
    "schema_confidence": 0.78,
    "requires_clinician_review": true
  },
  "limitations": []
}
```

## Agent Testing

Test agents with fake tools first.

Tests:

- Orchestrator routes normal workflow.
- Orchestrator pauses on review.
- Rejected review blocks transformation.
- Parser agent returns structured error on malformed data.
- Retrieval agent returns warning on empty context.
- Schema agent flags multiple candidates.
- Validation agent flags destructive cleaning.
- Transformation agent refuses unapproved cleaning.
- Explanation agent marks unsupported claim.
- Safety agent blocks prompt-injection-as-instruction.

## Acceptance Criteria

- Every agent output validates against `AgentResult`.
- Every tool call is logged with workflow ID.
- Agents only use tools from their allowlist.
- Review can pause and resume workflow.
- Explanation includes source evidence IDs.
- MCP wrappers match internal tool schemas.
- Direct tools remain testable without agent runtime.

## Build Sequence

1. Implement `AgentResult`, `ToolSpec`, `ToolCall`, and `ReviewRequest` contracts.
2. Implement direct parser, validation, conversion tools.
3. Implement simple orchestrator with deterministic routing.
4. Add parser, validation, transformation, safety, and review agents.
5. Add retrieval and explanation agents with stubbed retrieval.
6. Add tool registry and role allowlists.
7. Add MCP wrappers for stable tools.
8. Add progress events and workflow status API.
9. Add tests for pause/resume and blocked actions.

## Risks

| Risk | Control |
| --- | --- |
| Agents become too broad | Keep role-specific allowlists |
| LLM over-controls execution | Use deterministic routing for basic workflows |
| MCP adds complexity too early | Wrap only after direct tools stabilize |
| Human review feels bolted on | Make review part of workflow state |
| Explanation fabricates rationale | Require evidence package and claim status |
