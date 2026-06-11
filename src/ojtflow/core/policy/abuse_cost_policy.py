"""Abuse and cost-control policy helpers."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.abuse_cost import AbuseCostPolicy
from ojtflow.core.errors import PolicyBlockedError


def load_abuse_cost_policy(path: Path) -> AbuseCostPolicy:
    """Load a versioned abuse/cost policy file."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    return AbuseCostPolicy.model_validate(raw)


def require_llm_budget(
    policy: AbuseCostPolicy,
    *,
    surface: str,
    request_chars: int,
) -> None:
    _require_limit(
        surface=surface,
        metric="request_chars",
        value=request_chars,
        limit=policy.llm.max_request_chars,
    )


def require_openai_vision_budget(
    policy: AbuseCostPolicy,
    *,
    surface: str,
    byte_count: int,
) -> None:
    _require_limit(
        surface=surface,
        metric="byte_count",
        value=byte_count,
        limit=policy.ocr.max_openai_vision_bytes,
    )


def markitdown_ocr_allowed(
    policy: AbuseCostPolicy,
    *,
    byte_count: int,
) -> bool:
    return byte_count <= policy.ocr.max_markitdown_ocr_bytes


def require_embedding_budget(
    policy: AbuseCostPolicy,
    *,
    surface: str,
    texts: list[str],
) -> None:
    _require_limit(
        surface=surface,
        metric="input_count",
        value=len(texts),
        limit=policy.embeddings.max_request_inputs,
    )
    total_chars = sum(len(text) for text in texts)
    _require_limit(
        surface=surface,
        metric="request_chars",
        value=total_chars,
        limit=policy.embeddings.max_request_chars,
    )
    longest = max((len(text) for text in texts), default=0)
    _require_limit(
        surface=surface,
        metric="single_text_chars",
        value=longest,
        limit=policy.embeddings.max_single_text_chars,
    )


def require_batch_ingestion_budget(
    policy: AbuseCostPolicy,
    *,
    total_bytes: int,
) -> None:
    _require_limit(
        surface="batch_ingestion",
        metric="total_bytes",
        value=total_bytes,
        limit=policy.batch_ingestion.max_batch_total_bytes,
    )


def _require_limit(
    *,
    surface: str,
    metric: str,
    value: int,
    limit: int,
) -> None:
    if value <= limit:
        return
    raise PolicyBlockedError(
        "Request exceeds configured abuse/cost control limits.",
        details={
            "surface": surface,
            "metric": metric,
            "value": value,
            "limit": limit,
            "policy": "abuse_cost_policy.v1",
        },
    )
