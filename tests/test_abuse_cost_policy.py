import json
from pathlib import Path

import pytest

from ojtflow.config import clear_settings_cache
from ojtflow.core.errors import PolicyBlockedError
from ojtflow.core.policy.abuse_cost_policy import (
    load_abuse_cost_policy,
    require_batch_ingestion_budget,
)
from ojtflow.data_tools.extract import Extractor, extract_document
from ojtflow.infrastructure.retrieval.embeddings import OpenAIEmbeddingProvider


ROOT = Path(__file__).resolve().parents[1]


def test_default_abuse_cost_policy_loads() -> None:
    policy = load_abuse_cost_policy(ROOT / "knowledge/security/abuse_cost_policy.json")

    assert policy.llm.max_request_chars > 0
    assert policy.ocr.max_openai_vision_bytes > 0
    assert policy.embeddings.max_request_inputs > 0
    assert policy.batch_ingestion.max_batch_total_bytes > 0


def test_batch_ingestion_budget_blocks_oversized_batch() -> None:
    policy = load_abuse_cost_policy(ROOT / "knowledge/security/abuse_cost_policy.json")

    with pytest.raises(PolicyBlockedError) as exc:
        require_batch_ingestion_budget(
            policy,
            total_bytes=policy.batch_ingestion.max_batch_total_bytes + 1,
        )

    assert exc.value.details["surface"] == "batch_ingestion"
    assert exc.value.details["metric"] == "total_bytes"


def test_openai_embedding_budget_blocks_before_http() -> None:
    policy_path = ROOT / "knowledge/security/abuse_cost_policy.json"
    policy = load_abuse_cost_policy(policy_path)
    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        model="text-embedding-3-small",
        dimensions=384,
        base_url="https://example.invalid/v1",
        timeout_seconds=1,
        abuse_cost_policy=policy,
    )

    with pytest.raises(PolicyBlockedError) as exc:
        provider.embed_documents(["x" * (policy.embeddings.max_single_text_chars + 1)])

    assert exc.value.details["surface"] == "openai_embeddings"
    assert exc.value.details["metric"] == "single_text_chars"


def test_openai_vision_budget_blocks_before_http(monkeypatch, tmp_path: Path) -> None:
    policy_path = tmp_path / "abuse_cost_policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "version": "abuse_cost_policy.v1",
                "llm": {"max_request_chars": 1000},
                "ocr": {
                    "max_openai_vision_bytes": 4,
                    "max_markitdown_ocr_bytes": 4,
                },
                "embeddings": {
                    "max_request_inputs": 2,
                    "max_request_chars": 1000,
                    "max_single_text_chars": 500,
                },
                "batch_ingestion": {"max_batch_total_bytes": 10},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OJT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("OJT_ABUSE_COST_POLICY_PATH", str(policy_path))
    monkeypatch.setenv("OJT_OPENAI_API_KEY", "test-key")
    clear_settings_cache()

    try:
        with pytest.raises(PolicyBlockedError) as exc:
            extract_document(b"not-an-image", "scan.png", prefer=Extractor.OPENAI_VISION)
    finally:
        clear_settings_cache()

    assert exc.value.details["surface"] == "openai_vision_ocr"
    assert exc.value.details["metric"] == "byte_count"
