"""API request schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from ojtflow.core.contracts.base import ContractModel, NonBlankStr, NonBlankText
from ojtflow.core.contracts.enums import (
    DataFormat,
    EvidenceSourceType,
    ReviewDecision,
    TrustLevel,
)
from ojtflow.core.contracts.redaction import RedactionActionType
from ojtflow.medical.contracts import OcrEvidenceInput


class StartWorkflowRequest(ContractModel):
    instruction: NonBlankStr
    data: NonBlankText
    input_format: DataFormat | None = None
    target_format: DataFormat = DataFormat.JSON
    schema_id: NonBlankStr | None = "lab_result_v1"
    require_human_review: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
                    "data": (
                        "date,patient_id,lab_name,value,unit\n"
                        "2026-01-01,P001,HbA1c,7.4,%\n"
                        "2026/01/02,P002,HbA1c,,\n"
                    ),
                    "input_format": "csv",
                    "target_format": "json",
                    "schema_id": "lab_result_v1",
                    "require_human_review": True,
                }
            ]
        }
    }


class SubmitReviewRequest(ContractModel):
    decision: ReviewDecision
    decided_by: str | None = Field(
        default=None,
        deprecated=True,
        description="Deprecated. The API records the authenticated user as the reviewer.",
    )
    payload: dict = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "decision": "approve",
                    "payload": {},
                },
                {
                    "decision": "clarify",
                    "payload": {
                        "question": "Confirm whether blank units should be preserved as null."
                    },
                },
            ]
        }
    }


class ConvertRequest(ContractModel):
    data: NonBlankText
    input_format: DataFormat | None = None
    target_format: DataFormat = DataFormat.JSON

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n",
                    "input_format": "csv",
                    "target_format": "json",
                },
                {
                    "data": (
                        '[{"date":"2026-01-01","patient_id":"P001",'
                        '"lab_name":"HbA1c","value":7.4,"unit":"%"}]'
                    ),
                    "input_format": "json",
                    "target_format": "yaml",
                }
            ]
        }
    }


class ValidateRequest(ContractModel):
    data: NonBlankText
    input_format: DataFormat | None = None
    schema_id: NonBlankStr | None = "lab_result_v1"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": "date,patient_id,lab_name,value,unit\n2026/01/02,P002,HbA1c,,\n",
                    "input_format": "csv",
                    "schema_id": "lab_result_v1",
                }
            ]
        }
    }


class RedactionPreviewRequest(ContractModel):
    data: NonBlankText
    input_format: DataFormat | None = None
    redaction_action: RedactionActionType | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": (
                        "patient_id,ssn,email,value\n"
                        "P001,123-45-6789,patient@example.com,7.4\n"
                    ),
                    "input_format": "csv",
                    "redaction_action": "mask",
                },
                {
                    "data": "patient_id,ssn\nP001,123-45-6789\n",
                    "input_format": "csv",
                    "redaction_action": "tokenize_placeholder",
                }
            ]
        }
    }


class FhirProfileRequest(ContractModel):
    data: NonBlankStr

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": (
                        '{"resourceType":"Observation","status":"final",'
                        '"code":{"text":"HbA1c"}}'
                    )
                }
            ]
        }
    }


class OcrEvidenceFieldRequest(OcrEvidenceInput):
    """OCR evidence field submitted through the public API."""


class OcrEvidenceRequest(ContractModel):
    fields: list[OcrEvidenceFieldRequest] = Field(min_length=1)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fields": [
                        {
                            "page": 1,
                            "name": "patient_id",
                            "value": "P001",
                            "bbox": [72.0, 144.0, 96.0, 18.0],
                            "confidence": 0.72,
                            "source_ref": "storage://uploads/lab-report-page-1",
                        }
                    ]
                }
            ]
        }
    }


class RetrievalSearchFilters(ContractModel):
    trust_level: TrustLevel | None = None
    clinical_domain: NonBlankStr | None = None
    standard_system: NonBlankStr | None = None
    source_type: EvidenceSourceType | None = None
    source_id: NonBlankStr | None = None
    diversity_enabled: bool | None = None
    diversity_lambda: float | None = Field(default=None, ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "trust_level": "approved",
                    "clinical_domain": "laboratory",
                    "standard_system": "UCUM",
                    "source_type": "terminology_system",
                    "source_id": "terminology:ucum",
                    "diversity_enabled": True,
                    "diversity_lambda": 0.72,
                }
            ]
        }
    }


class RetrievalSearchRequest(ContractModel):
    query: NonBlankStr
    top_k: int = Field(default=5, ge=1, le=20)
    schema_id: NonBlankStr | None = None
    workflow_id: NonBlankStr | None = None
    fields: list[NonBlankStr] = Field(default_factory=list)
    detected_format: NonBlankStr | None = None
    resource_type: NonBlankStr | None = None
    clinical_domain: NonBlankStr | None = None
    standard_system: NonBlankStr | None = None
    trust_level: TrustLevel | None = TrustLevel.APPROVED
    source_type: EvidenceSourceType | None = None
    filters: RetrievalSearchFilters = Field(default_factory=RetrievalSearchFilters)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "HbA1c lab CSV missing units FHIR Observation",
                    "top_k": 5,
                    "schema_id": "lab_result_v1",
                    "fields": ["date", "patient_id", "lab_name", "value", "unit"],
                    "clinical_domain": "laboratory",
                    "trust_level": "approved",
                }
            ]
        }
    }


class RetrievalJudgmentRequest(ContractModel):
    query: NonBlankStr
    evidence_id: NonBlankStr
    value: Literal["relevant", "partial", "not_relevant"]
    rating: int | None = Field(default=None, ge=0, le=3)
    source_id: NonBlankStr | None = None
    source_type: EvidenceSourceType | None = None
    source_version: NonBlankStr | None = None
    run_id: NonBlankStr | None = None
    search_signature: NonBlankStr | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "FHIR Observation HbA1c unit",
                    "evidence_id": "ev_schema_lab_result_v1",
                    "source_id": "schema:lab_result_v1",
                    "source_type": "schema",
                    "value": "relevant",
                    "rating": 3,
                    "run_id": "browser-run-1",
                    "search_signature": "{\"query\":\"FHIR Observation HbA1c unit\"}",
                    "metadata": {"review_surface": "retrieval_console"},
                }
            ]
        }
    }


class RetrievalJudgmentEvaluationRequest(ContractModel):
    query: NonBlankStr
    ranked_evidence_ids: list[NonBlankStr] = Field(min_length=1, max_length=100)
    cutoff: int | None = Field(default=None, ge=1, le=100)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "FHIR Observation HbA1c unit",
                    "ranked_evidence_ids": [
                        "ev_schema_lab_result_v1",
                        "ev_terminology_ucum",
                    ],
                    "cutoff": 5,
                }
            ]
        }
    }


class RetrievalReindexRequest(ContractModel):
    include_seeded: bool = True
    include_corpus: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "include_seeded": True,
                    "include_corpus": True,
                }
            ]
        }
    }


class RetrievalReindexJobRequest(RetrievalReindexRequest):
    execute_now: bool = True


class RuntimeRetrievalSettingsRequest(ContractModel):
    embedding_provider: Literal["deterministic", "openai", "huggingface"] | None = None
    embedding_model: NonBlankStr | None = None
    embedding_dimensions: int | None = Field(default=None, ge=1, le=4096)
    retrieval_framework: Literal["custom", "llamaindex"] | None = None
    retrieval_candidate_multiplier: int | None = Field(default=None, ge=1, le=20)
    retrieval_min_candidates: int | None = Field(default=None, ge=1, le=200)
    retrieval_vector_weight: float | None = Field(default=None, ge=0, le=1)
    retrieval_bm25_weight: float | None = Field(default=None, ge=0, le=1)
    retrieval_diversity_enabled: bool | None = None
    retrieval_diversity_lambda: float | None = Field(default=None, ge=0, le=1)
    retrieval_hnsw_ef_search: int | None = Field(default=None, ge=1, le=1000)

    @model_validator(mode="after")
    def _has_runtime_update(self) -> "RuntimeRetrievalSettingsRequest":
        if not self.model_dump(exclude_none=True):
            raise ValueError("At least one retrieval setting must be provided.")
        if (
            self.retrieval_vector_weight is not None
            and self.retrieval_bm25_weight is not None
            and self.retrieval_vector_weight + self.retrieval_bm25_weight <= 0
        ):
            raise ValueError(
                "retrieval_vector_weight and retrieval_bm25_weight cannot both be zero."
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "embedding_provider": "openai",
                    "embedding_model": "text-embedding-3-small",
                    "embedding_dimensions": 384,
                    "retrieval_framework": "llamaindex",
                    "retrieval_candidate_multiplier": 4,
                    "retrieval_min_candidates": 12,
                    "retrieval_vector_weight": 0.62,
                    "retrieval_bm25_weight": 0.38,
                    "retrieval_diversity_enabled": True,
                    "retrieval_diversity_lambda": 0.72,
                    "retrieval_hnsw_ef_search": 100,
                }
            ]
        }
    }


class RuntimeAssistantSettingsRequest(ContractModel):
    llm_provider: Literal["disabled", "openai"] | None = None
    llm_model: NonBlankStr | None = None
    llm_planning_model: NonBlankStr | None = None
    llm_synthesis_model: NonBlankStr | None = None
    llm_vision_model: NonBlankStr | None = None
    llm_base_url: NonBlankStr | None = None
    llm_timeout_seconds: float | None = Field(default=None, gt=0, le=300)
    llm_max_tool_calls: int | None = Field(default=None, ge=1, le=12)
    llm_planning_progress_interval_seconds: float | None = Field(
        default=None,
        gt=0,
        le=30,
    )
    external_openai_llm_enabled: bool | None = None
    external_openai_llm_allow_phi: bool | None = None
    external_openai_ocr_enabled: bool | None = None
    external_openai_ocr_allow_phi: bool | None = None
    external_openai_ocr_allow_unknown: bool | None = None
    external_openai_embeddings_enabled: bool | None = None
    external_openai_embeddings_allow_phi: bool | None = None
    external_medical_search_enabled: bool | None = None
    external_medical_search_allow_phi: bool | None = None

    @model_validator(mode="after")
    def _has_runtime_update(self) -> "RuntimeAssistantSettingsRequest":
        if not self.model_dump(exclude_none=True):
            raise ValueError("At least one assistant setting must be provided.")
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "llm_provider": "openai",
                    "llm_model": "gpt-4.1-mini",
                    "llm_planning_model": "gpt-4.1-mini",
                    "llm_synthesis_model": "gpt-4.1",
                    "llm_vision_model": "gpt-4.1-mini",
                    "llm_base_url": "https://api.openai.com/v1",
                    "llm_timeout_seconds": 30.0,
                    "llm_max_tool_calls": 4,
                    "llm_planning_progress_interval_seconds": 2.0,
                    "external_openai_llm_enabled": True,
                    "external_openai_llm_allow_phi": False,
                    "external_openai_ocr_enabled": True,
                    "external_openai_ocr_allow_phi": False,
                    "external_openai_ocr_allow_unknown": True,
                    "external_openai_embeddings_enabled": True,
                    "external_openai_embeddings_allow_phi": False,
                    "external_medical_search_enabled": True,
                    "external_medical_search_allow_phi": False,
                }
            ]
        }
    }


class AssistantChatRequest(ContractModel):
    message: NonBlankStr
    context: dict[str, Any] = Field(default_factory=dict)
    execute_write_actions: bool = False
    session_id: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Find trusted evidence for HbA1c CSV rows with missing units.",
                    "context": {
                        "schema_id": "lab_result_v1",
                        "fields": ["lab_name", "value", "unit"],
                        "clinical_domain": "laboratory",
                    },
                    "execute_write_actions": False,
                    "session_id": "chat_abc123",
                },
                {
                    "message": "Validate this messy lab CSV and explain it with trusted evidence.",
                    "context": {
                        "data": (
                            "date,patient_id,lab_name,value,unit\n"
                            "2026/01/02,P002,HbA1c,,\n"
                        ),
                        "input_format": "csv",
                        "schema_id": "lab_result_v1",
                        "clinical_domain": "laboratory",
                    },
                    "execute_write_actions": False,
                },
            ]
        }
    }


class AssistantSessionCreateRequest(ContractModel):
    title: NonBlankStr = "New chat"


class AssistantSessionRenameRequest(ContractModel):
    title: NonBlankStr


class AssistantSessionMessageRequest(ContractModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str = ""
    workflow_refs: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class AssistantMemoryPreferenceRequest(ContractModel):
    value: str | int | float | bool
    source: Literal["user", "system", "admin"] = "user"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "value": "detailed",
                    "source": "user",
                }
            ]
        }
    }
