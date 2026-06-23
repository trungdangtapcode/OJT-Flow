"""Contracts for natural-language assistant and tool orchestration."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr
from ojtflow.core.contracts.phi import PhiClassification
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


AssistantToolStatus = Literal["completed", "failed", "requires_approval", "skipped"]
AssistantFindingSeverity = Literal["info", "warning", "error", "action_required"]
AssistantMessageRole = Literal["user", "assistant", "system", "tool"]
AssistantToolProgressEvent = Literal["before_execute", "after_execute"]
AssistantMemoryValue = str | int | float | bool


class AssistantToolSpec(ContractModel):
    """Model-visible tool contract for assistant planning."""

    name: str
    description: str
    permission_scope: str
    permission_tags: list[str] = Field(default_factory=list)
    risk_level: str = "low"
    approval_reason: str | None = None
    requires_approval: bool = False
    input_schema: dict[str, Any] = Field(default_factory=dict)


class AssistantToolPlan(ContractModel):
    """A proposed tool call from governed LLM planning."""

    tool_name: NonBlankStr
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""


class AssistantToolResult(ContractModel):
    """Executed or skipped assistant tool call."""

    tool_name: str
    status: AssistantToolStatus
    arguments: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    error: str | None = None
    requires_approval: bool = False


class AssistantToolProgressStage(ContractModel):
    """Data-driven progress marker streamed while an assistant tool runs."""

    stage_id: NonBlankStr
    label: NonBlankStr
    message: NonBlankStr
    progress: int | None = Field(default=None, ge=0, le=100)
    event: AssistantToolProgressEvent = "before_execute"


class AssistantToolProgressPolicy(ContractModel):
    """Progress stages for one assistant tool."""

    tool_name: NonBlankStr
    stages: list[AssistantToolProgressStage] = Field(default_factory=list)


class AssistantToolProgressCatalog(ContractModel):
    """Data-driven assistant progress stage registry."""

    version: NonBlankStr
    policies: list[AssistantToolProgressPolicy] = Field(default_factory=list)


class AssistantFinding(ContractModel):
    """Operator-ready finding synthesized from tool outputs."""

    title: str
    detail: str
    severity: AssistantFindingSeverity = "info"
    source_tool: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class AssistantEvidenceSummary(ContractModel):
    """Compact evidence item for assistant answers."""

    evidence_id: str | None = None
    source_id: str
    source_type: str | None = None
    claim: str
    trust_level: str
    confidence: float | None = None
    locator: dict[str, Any] = Field(default_factory=dict)
    match_explanation: dict[str, Any] = Field(default_factory=dict)


class AssistantPlan(ContractModel):
    """Validated LLM plan before backend execution."""

    message: str
    tool_calls: list[AssistantToolPlan] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AssistantExample(ContractModel):
    """Data-driven starter task for the Assistant UI."""

    example_id: NonBlankStr
    label: NonBlankStr
    description: NonBlankStr
    message: NonBlankStr
    context: dict[str, Any] = Field(default_factory=dict)


class AssistantAnswerTemplateSection(ContractModel):
    """One named section in a governed Assistant answer template."""

    section_id: NonBlankStr
    title: NonBlankStr
    purpose: NonBlankStr
    required: bool = True


class AssistantAnswerTemplate(ContractModel):
    """Data-driven response template for a class of Assistant task."""

    template_id: NonBlankStr
    label: NonBlankStr
    description: NonBlankStr
    tool_names: list[NonBlankStr] = Field(default_factory=list)
    sections: list[AssistantAnswerTemplateSection] = Field(default_factory=list)
    evidence_required: bool = False
    review_required_when: list[NonBlankStr] = Field(default_factory=list)
    output_constraints: list[NonBlankStr] = Field(default_factory=list)


class AssistantEvaluationCase(ContractModel):
    """One data-driven Assistant evaluation case."""

    case_id: NonBlankStr
    label: NonBlankStr
    task_type: NonBlankStr
    message: NonBlankStr
    context: dict[str, Any] = Field(default_factory=dict)
    execute_write_actions: bool = False
    expected_tool_names: list[NonBlankStr] = Field(default_factory=list)
    expected_tool_statuses: list[NonBlankStr] = Field(default_factory=list)
    required_answer_terms: list[NonBlankStr] = Field(default_factory=list)
    forbidden_answer_terms: list[NonBlankStr] = Field(default_factory=list)
    min_evidence_summaries: int = Field(default=0, ge=0)
    required_evidence_source_ids: list[NonBlankStr] = Field(default_factory=list)
    faithfulness_notes: list[NonBlankStr] = Field(default_factory=list)
    roadmap_refs: list[NonBlankStr] = Field(default_factory=list)


class AssistantEvaluationSuite(ContractModel):
    """Versioned Assistant evaluation fixture suite."""

    version: NonBlankStr
    cases: list[AssistantEvaluationCase] = Field(default_factory=list)


class AssistantSafetyCase(ContractModel):
    """One adversarial Assistant safety fixture."""

    case_id: NonBlankStr
    label: NonBlankStr
    attack_surface: NonBlankStr
    message: NonBlankStr
    context: dict[str, Any] = Field(default_factory=dict)
    execute_write_actions: bool = False
    expected_tool_names: list[NonBlankStr] = Field(default_factory=list)
    expected_tool_statuses: list[NonBlankStr] = Field(default_factory=list)
    forbidden_tool_names: list[NonBlankStr] = Field(default_factory=list)
    expected_issue_kinds: list[NonBlankStr] = Field(default_factory=list)
    expected_safety_flags: list[NonBlankStr] = Field(default_factory=list)
    required_finding_titles: list[NonBlankStr] = Field(default_factory=list)
    forbidden_answer_terms: list[NonBlankStr] = Field(default_factory=list)
    safety_notes: list[NonBlankStr] = Field(default_factory=list)
    roadmap_refs: list[NonBlankStr] = Field(default_factory=list)


class AssistantSafetySuite(ContractModel):
    """Versioned Assistant adversarial safety fixture suite."""

    version: NonBlankStr
    cases: list[AssistantSafetyCase] = Field(default_factory=list)


class AssistantMemoryPreferenceDefinition(ContractModel):
    """Policy-defined preference the Assistant may remember for a user."""

    key: NonBlankStr
    label: NonBlankStr
    description: NonBlankStr
    category: NonBlankStr = "operational"
    value_type: Literal["string", "boolean", "number", "enum"] = "string"
    allowed_values: list[AssistantMemoryValue] = Field(default_factory=list)
    default_value: AssistantMemoryValue | None = None
    max_length: int = Field(default=80, ge=1, le=500)
    safety_tags: list[NonBlankStr] = Field(default_factory=list)


class AssistantMemoryPolicy(ContractModel):
    """Data-driven allowlist and denial rules for Assistant memory."""

    version: NonBlankStr
    preferences: list[AssistantMemoryPreferenceDefinition] = Field(default_factory=list)
    rejected_key_terms: list[NonBlankStr] = Field(default_factory=list)
    rejected_value_patterns: list[NonBlankStr] = Field(default_factory=list)


class AssistantMemoryPreference(ContractModel):
    """Persisted user preference safe to pass into Assistant planning."""

    owner_user_id: str
    key: NonBlankStr
    value: AssistantMemoryValue
    category: NonBlankStr
    source: Literal["user", "system", "admin"] = "user"
    policy_version: NonBlankStr
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())


class AssistantMemorySnapshot(ContractModel):
    """User-safe memory snapshot returned to UI and injected into Assistant context."""

    policy_version: NonBlankStr
    preferences: list[AssistantMemoryPreference] = Field(default_factory=list)
    context: dict[str, AssistantMemoryValue] = Field(default_factory=dict)


class AssistantChatSessionSummary(ContractModel):
    """Persisted Assistant chat session summary."""

    session_id: str = Field(default_factory=lambda: new_id("chat"))
    owner_user_id: str
    title: str
    message_count: int = 0
    archived_at: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())


class AssistantChatMessage(ContractModel):
    """Persisted Assistant chat message or tool artifact."""

    message_id: str = Field(default_factory=lambda: new_id("msg"))
    session_id: str
    owner_user_id: str
    role: AssistantMessageRole
    content: str = ""
    workflow_refs: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    phi_classification: PhiClassification | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class AssistantStreamReplay(ContractModel):
    """Persisted SSE timeline for replay/debugging."""

    stream_id: str
    session_id: str
    owner_user_id: str
    status: Literal["completed", "failed", "cancelled"]
    events: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str
    completed_at: str


class AssistantChatSessionDetail(ContractModel):
    """Persisted Assistant session with ordered messages."""

    session: AssistantChatSessionSummary
    messages: list[AssistantChatMessage] = Field(default_factory=list)


class AssistantResponse(ContractModel):
    """Public assistant response."""

    message: str
    mode: Literal["llm", "recovery"]
    synthesis_mode: Literal["llm"] = "llm"
    model: str | None = None
    findings: list[AssistantFinding] = Field(default_factory=list)
    evidence_summary: list[AssistantEvidenceSummary] = Field(default_factory=list)
    tool_calls: list[AssistantToolResult] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
