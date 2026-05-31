"""Backbone enumerations."""

from __future__ import annotations

from enum import StrEnum


class DataFormat(StrEnum):
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    NDJSON = "ndjson"
    # Document formats — produced by extraction pipeline
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"
    UNKNOWN = "unknown"


class WorkflowStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentStatus(StrEnum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    BLOCKED_BY_POLICY = "blocked_by_policy"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ActorType(StrEnum):
    USER = "user"
    AGENT = "agent"
    TOOL = "tool"
    SYSTEM = "system"


class EventType(StrEnum):
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    TOOL_CALLED = "tool.called"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    RETRIEVAL_COMPLETED = "retrieval.completed"
    VALIDATION_COMPLETED = "validation.completed"
    REVIEW_REQUESTED = "review.requested"
    REVIEW_DECIDED = "review.decided"
    TRANSFORMATION_COMPLETED = "transformation.completed"
    EXPLANATION_COMPLETED = "explanation.completed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"


class EvidenceSourceType(StrEnum):
    INPUT_DATA = "input_data"
    SCHEMA = "schema"
    DATA_DICTIONARY = "data_dictionary"
    TERMINOLOGY_SYSTEM = "terminology_system"
    HEALTHCARE_STANDARD = "healthcare_standard"
    TRANSFORMATION_EXAMPLE = "transformation_example"
    VALIDATION_REPORT = "validation_report"
    TOOL_OUTPUT = "tool_output"
    HUMAN_DECISION = "human_decision"
    AUDIT_EVENT = "audit_event"
    OCR_BOX = "ocr_box"
    DICOM_METADATA = "dicom_metadata"
    IMAGE_MASK = "image_mask"
    VIDEO_TRACK = "video_track"


class TrustLevel(StrEnum):
    APPROVED = "approved"
    INTERNAL = "internal"
    USER_PROVIDED = "user_provided"
    UNTRUSTED = "untrusted"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    APPROVED_WITH_EDITS = "approved_with_edits"
    REJECTED = "rejected"
    CLARIFICATION_REQUESTED = "clarification_requested"
    CANCELLED = "cancelled"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    APPROVE_WITH_EDITS = "approve_with_edits"
    REJECT = "reject"
    CLARIFY = "clarify"
    CANCEL = "cancel"


class ToolPermission(StrEnum):
    DATA_READ = "data:read"
    DATA_PROFILE = "data:profile"
    DATA_VALIDATE = "data:validate"
    DATA_TRANSFORM = "data:transform"
    DATA_EXPORT = "data:export"
    RETRIEVAL_READ = "retrieval:read"
    AUDIT_WRITE = "audit:write"
    REVIEW_WRITE = "review:write"
