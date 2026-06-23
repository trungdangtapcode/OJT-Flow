"""API request schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from ojtflow.core.contracts.base import ContractModel, NonBlankStr, NonBlankText
from ojtflow.core.contracts.clinical import ClinicalPackage
from ojtflow.core.contracts.medsiglip import MedSiglipClassificationRequest
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


class BulkFhirNdjsonImportRequest(ContractModel):
    data: NonBlankStr
    source_ref: NonBlankStr | None = None
    allowed_resource_types: list[NonBlankStr] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": (
                        '{"resourceType":"Patient","id":"P001"}\n'
                        '{"resourceType":"Observation","id":"O001","status":"final"}\n'
                    ),
                    "source_ref": "bulk-fhir://demo/patient-observation.ndjson",
                    "allowed_resource_types": ["Patient", "Observation"],
                }
            ]
        }
    }


class BulkFhirNdjsonExportRequest(ContractModel):
    package: ClinicalPackage
    require_approval: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "package": {
                        "package_type": "ojtflow_clinical_package",
                        "schema_version": "clinical_package.v0",
                        "workflow_id": "wf_demo",
                        "raw_input": {
                            "dataset_ref": "storage://datasets/demo",
                            "input_hash": "sha256:demo",
                            "declared_format": "csv",
                            "detected_format": "csv",
                        },
                        "clinical_bundle": {
                            "resourceType": "Bundle",
                            "type": "collection",
                            "entry": [],
                            "resources": [],
                        },
                        "operation_outcome": {"resourceType": "OperationOutcome", "issue": []},
                    },
                    "require_approval": True,
                }
            ]
        }
    }


class ClinicalPackageImportValidationRequest(ContractModel):
    payload: dict[str, Any]
    require_hash_match: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "payload": {
                        "export_type": "ojtflow_clinical_package_export",
                        "schema_version": "clinical_package_export.v0",
                        "workflow_id": "wf_demo",
                        "package_id": "cpkg_demo",
                        "package_hash": "expected-package-sha256",
                        "fhir_like_bundle_hash": "expected-bundle-sha256",
                        "approved_for_export": True,
                        "clinical_package": {
                            "package_type": "ojtflow_clinical_package",
                            "schema_version": "clinical_package.v0",
                            "workflow_id": "wf_demo",
                            "raw_input": {
                                "dataset_ref": "storage://datasets/demo",
                                "input_hash": "sha256:demo",
                                "declared_format": "csv",
                                "detected_format": "csv",
                            },
                            "clinical_bundle": {
                                "resourceType": "Bundle",
                                "type": "collection",
                                "entry": [],
                                "resources": [],
                            },
                            "operation_outcome": {
                                "resourceType": "OperationOutcome",
                                "issue": [],
                            },
                        },
                        "fhir_like_bundle": {
                            "resourceType": "Bundle",
                            "type": "collection",
                            "entry": [],
                        },
                    },
                    "require_hash_match": True,
                }
            ]
        }
    }


class Hl7V2MapRequest(ContractModel):
    data: NonBlankStr
    source_ref: NonBlankStr | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": (
                        "MSH|^~\\&|LAB|HOSP|OJT|OJT|202606111200||ORU^R01|MSG1|P|2.5\r"
                        "PID|1||P001^^^MRN||DOE^JANE\r"
                        "OBR|1||ORD1|LAB^Lab panel\r"
                        "OBX|1|NM|4548-4^HbA1c^LN||7.4|%^percent|4.0-5.6|H|||F|||20260611\r"
                    ),
                    "source_ref": "hl7v2://demo/oru-r01",
                }
            ]
        }
    }


class DicomMetadataProfileRequest(ContractModel):
    metadata: dict[str, Any]
    source_ref: NonBlankStr | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "metadata": {
                        "StudyInstanceUID": "1.2.3",
                        "SeriesInstanceUID": "1.2.3.4",
                        "SOPInstanceUID": "1.2.3.4.5",
                        "Modality": "MR",
                        "AccessionNumber": "ACC-001",
                        "PatientIdentityRemoved": "YES",
                    },
                    "source_ref": "dicom://study/1.2.3",
                }
            ]
        }
    }


class DocumentReferenceMapRequest(ContractModel):
    document_id: NonBlankStr
    filename: NonBlankStr
    content_type: NonBlankStr
    source_ref: NonBlankStr
    description: NonBlankStr | None = None
    status: NonBlankStr = "current"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "document_id": "artifact_123",
                    "filename": "lab-report.pdf",
                    "content_type": "application/pdf",
                    "source_ref": "storage://uploads/lab-report.pdf",
                    "description": "Uploaded lab report",
                }
            ]
        }
    }


class OmopPreviewRequest(ContractModel):
    package: ClinicalPackage

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "package": {
                        "package_type": "ojtflow_clinical_package",
                        "schema_version": "clinical_package.v0",
                        "workflow_id": "wf_demo",
                        "raw_input": {
                            "dataset_ref": "storage://datasets/demo",
                            "input_hash": "sha256:demo",
                            "declared_format": "csv",
                            "detected_format": "csv",
                        },
                        "clinical_bundle": {
                            "resourceType": "Bundle",
                            "type": "collection",
                            "entry": [],
                            "resources": [],
                        },
                        "operation_outcome": {"resourceType": "OperationOutcome", "issue": []},
                    }
                }
            ]
        }
    }


class ExternalApiCacheMetadataRequest(ContractModel):
    connector_id: NonBlankStr
    endpoint_url: NonBlankStr
    query: NonBlankStr
    source_release_version: NonBlankStr
    response_text: str | None = None
    fetched_at: NonBlankStr | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "connector_id": "pubmed",
                    "endpoint_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                    "query": "HbA1c LOINC Observation",
                    "source_release_version": "fetched:2026-06-11",
                    "response_text": "{\"count\":\"2\"}",
                    "metadata": {"workspace_id": "default"},
                }
            ]
        }
    }


class SourceIngestionApprovalPreviewRequest(ContractModel):
    connector_id: NonBlankStr
    document_id: NonBlankStr
    source_url: NonBlankStr
    source_release_version: NonBlankStr
    license_accepted: bool = False
    reviewer_approved: bool = False
    contains_phi: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "connector_id": "pubmed",
                    "document_id": "pubmed-123",
                    "source_url": "https://pubmed.ncbi.nlm.nih.gov/123/",
                    "source_release_version": "fetched:2026-06-11",
                    "license_accepted": True,
                    "reviewer_approved": False,
                    "contains_phi": False,
                }
            ]
        }
    }


class ExternalLinkLaunchRequest(ContractModel):
    launcher_id: NonBlankStr
    query: NonBlankStr

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "launcher_id": "pubmed",
                    "query": "HbA1c unit standard",
                }
            ]
        }
    }


class EtlExportPackageRequest(ContractModel):
    package: ClinicalPackage
    include_resources: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "package": {
                        "package_type": "ojtflow_clinical_package",
                        "schema_version": "clinical_package.v0",
                        "workflow_id": "wf_demo",
                        "raw_input": {
                            "dataset_ref": "storage://datasets/demo",
                            "input_hash": "sha256:demo",
                            "declared_format": "csv",
                            "detected_format": "csv",
                        },
                        "clinical_bundle": {
                            "resourceType": "Bundle",
                            "type": "collection",
                            "entry": [],
                            "resources": [],
                        },
                        "operation_outcome": {"resourceType": "OperationOutcome", "issue": []},
                    },
                    "include_resources": False,
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


class MedSiglipClassificationJobRequest(MedSiglipClassificationRequest):
    """Create a durable MedSigLIP classification job."""

    execute_now: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "images": [
                        {
                            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB...",
                            "mime_type": "image/png",
                            "source_ref": "upload://demo/chest-xray.png",
                        }
                    ],
                    "candidate_labels": [
                        "a chest x-ray with cardiomegaly",
                        "a chest x-ray without cardiomegaly",
                    ],
                    "include_embeddings": False,
                    "execute_now": True,
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
    corpus_partition: NonBlankStr | None = None
    corpus_visibility: Literal["global", "organization", "private"] | None = None
    organization_id: NonBlankStr | None = None
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
                    "corpus_partition": "global_standards",
                    "corpus_visibility": "global",
                    "diversity_enabled": True,
                    "diversity_lambda": 0.72,
                }
            ]
        }
    }


class PrivateCorpusIngestRequest(ContractModel):
    data: NonBlankText | None = None
    artifact_id: NonBlankStr | None = None
    title: NonBlankStr | None = None
    source_ref: NonBlankStr | None = None
    input_format: DataFormat | None = None
    redaction_action: RedactionActionType | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Private tenant lab policy",
                    "data": (
                        "patient_id,ssn,lab_name,value\n"
                        "P001,123-45-6789,HbA1c,7.4\n"
                    ),
                    "input_format": "csv",
                    "redaction_action": "mask",
                    "source_ref": "tenant://policies/lab/private-policy.csv",
                },
                {
                    "artifact_id": "art_uploaded_lab_policy",
                    "title": "Uploaded private data dictionary",
                },
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
    value: Literal[
        "relevant",
        "partial",
        "irrelevant",
        "not_relevant",
        "unsafe",
        "stale",
        "source_policy_blocked",
    ]
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
                    "value": "source_policy_blocked",
                    "rating": 0,
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


class RetrievalActiveLearningCandidateRequest(ContractModel):
    source_kind: Literal[
        "low_confidence_retrieval",
        "unsupported_claim",
        "reviewer_correction",
        "weak_support",
        "negative_judgment",
    ]
    query: NonBlankStr
    trigger_reason: NonBlankStr
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    evidence_id: NonBlankStr | None = None
    source_id: NonBlankStr | None = None
    source_type: EvidenceSourceType | None = None
    source_version: NonBlankStr | None = None
    run_id: NonBlankStr | None = None
    workflow_id: NonBlankStr | None = None
    judgment_id: NonBlankStr | None = None
    claim_id: NonBlankStr | None = None
    support_status: Literal["strong", "partial", "weak", "unsupported"] | None = None
    suggested_expected_evidence_ids: list[NonBlankStr] = Field(default_factory=list)
    suggested_filters: dict[str, Any] = Field(default_factory=dict)
    benchmark_metadata: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source_kind": "unsupported_claim",
                    "query": "HbA1c FHIR Observation unit mapping",
                    "trigger_reason": "Answer contained an unsupported unit normalization claim.",
                    "priority": "high",
                    "evidence_id": "ev_terminology_ucum",
                    "source_id": "terminology:ucum",
                    "support_status": "unsupported",
                    "suggested_filters": {"standard_system": "ucum"},
                    "benchmark_metadata": {"expected_support_status": "strong"},
                }
            ]
        }
    }


class RetrievalActiveLearningCandidateUpdateRequest(ContractModel):
    status: Literal["open", "accepted", "rejected", "promoted", "archived"] | None = None
    priority: Literal["low", "normal", "high", "critical"] | None = None
    reviewer_note: NonBlankStr | None = None
    benchmark_metadata: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "accepted",
                    "priority": "high",
                    "reviewer_note": "Promote into the UCUM benchmark pack.",
                    "benchmark_metadata": {"case_family": "ucum_unit_checks"},
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


class EmbeddingReindexJobRequest(RetrievalReindexRequest):
    approval_token: NonBlankStr
    execute_now: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "include_seeded": True,
                    "include_corpus": True,
                    "approval_token": "approve_embedding_reindex_abc123",
                    "execute_now": True,
                }
            ]
        }
    }


class RuntimeRetrievalSettingsRequest(ContractModel):
    change_reason: NonBlankStr | None = None
    embedding_provider: Literal["openai", "huggingface"] | None = None
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
        if not self.model_dump(exclude_none=True, exclude={"change_reason"}):
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
    change_reason: NonBlankStr | None = None
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
        if not self.model_dump(exclude_none=True, exclude={"change_reason"}):
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


class RuntimeSettingsRollbackRequest(ContractModel):
    change_id: NonBlankStr
    reason: NonBlankStr | None = None


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
