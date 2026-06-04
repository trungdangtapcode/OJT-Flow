"""API request schemas."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr, NonBlankText
from ojtflow.core.contracts.enums import (
    DataFormat,
    EvidenceSourceType,
    ReviewDecision,
    TrustLevel,
)
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
    filters: dict[str, Any] = Field(default_factory=dict)

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
