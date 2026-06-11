"""Abuse and cost-control policy contracts."""

from __future__ import annotations

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel, NonBlankStr


class LlmCostPolicy(ContractModel):
    max_request_chars: int = Field(gt=0)


class OcrCostPolicy(ContractModel):
    max_openai_vision_bytes: int = Field(gt=0)
    max_markitdown_ocr_bytes: int = Field(gt=0)


class EmbeddingCostPolicy(ContractModel):
    max_request_inputs: int = Field(gt=0)
    max_request_chars: int = Field(gt=0)
    max_single_text_chars: int = Field(gt=0)


class BatchIngestionCostPolicy(ContractModel):
    max_batch_total_bytes: int = Field(gt=0)


class AbuseCostPolicy(ContractModel):
    version: NonBlankStr = "abuse_cost_policy.v1"
    llm: LlmCostPolicy
    ocr: OcrCostPolicy
    embeddings: EmbeddingCostPolicy
    batch_ingestion: BatchIngestionCostPolicy
