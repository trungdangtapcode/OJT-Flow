"""API request schemas."""

from __future__ import annotations

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.contracts.enums import DataFormat, ReviewDecision


class StartWorkflowRequest(ContractModel):
    instruction: str
    data: str
    input_format: DataFormat | None = None
    target_format: DataFormat = DataFormat.JSON
    schema_id: str | None = "lab_result_v1"
    require_human_review: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "instruction": "Clean this CSV, convert it to JSON, and explain anomalies.",
                    "data": "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n2026/01/02,P002,HbA1c,,\n",
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
    decided_by: str = "user"
    payload: dict = Field(default_factory=dict)


class ConvertRequest(ContractModel):
    data: str
    input_format: DataFormat | None = None
    target_format: DataFormat = DataFormat.JSON

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": "a,b\n1,2\n",
                    "input_format": "csv",
                    "target_format": "json",
                }
            ]
        }
    }


class ValidateRequest(ContractModel):
    data: str
    input_format: DataFormat | None = None
    schema_id: str | None = "lab_result_v1"


class FhirProfileRequest(ContractModel):
    data: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": "{\"resourceType\":\"Observation\",\"status\":\"final\",\"code\":{\"text\":\"HbA1c\"}}"
                }
            ]
        }
    }


class OcrEvidenceFieldRequest(ContractModel):
    page: int
    name: str
    value: str
    bbox: list[float]
    confidence: float
    source_ref: str
    normalized_to: str | None = None


class OcrEvidenceRequest(ContractModel):
    fields: list[OcrEvidenceFieldRequest]
