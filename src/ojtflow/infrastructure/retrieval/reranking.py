"""Second-stage reranker adapters for retrieval."""

from __future__ import annotations

from typing import Any, Protocol

from ojtflow.config import Settings
from ojtflow.core.errors import DependencyUnavailableError, OJTFlowError
from ojtflow.infrastructure.retrieval.engine import KnowledgeChunk


class Reranker(Protocol):
    """Small provider surface used after first-stage retrieval fusion."""

    provider_name: str
    model: str
    enabled: bool

    def score(self, query_text: str, chunks: list[KnowledgeChunk]) -> dict[str, float]:
        """Return normalized rerank scores by chunk id."""

    def metadata(self) -> dict[str, Any]:
        """Return non-secret reranker metadata for traces."""


class NullReranker:
    """Disabled reranker used when no real rerank provider is configured."""

    provider_name = "none"
    model = "none"
    enabled = False

    def score(self, query_text: str, chunks: list[KnowledgeChunk]) -> dict[str, float]:
        del query_text, chunks
        return {}

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "enabled": self.enabled,
        }


class HuggingFaceCrossEncoderReranker:
    """GPU-ready SentenceTransformers CrossEncoder reranker."""

    provider_name = "huggingface"
    enabled = True

    def __init__(
        self,
        *,
        model: str,
        device: str,
        batch_size: int,
        model_instance: Any | None = None,
    ) -> None:
        self.model = model
        self.device = device
        self.batch_size = batch_size
        self._model = model_instance

    def score(self, query_text: str, chunks: list[KnowledgeChunk]) -> dict[str, float]:
        clean_query = query_text.strip()
        if not clean_query:
            raise OJTFlowError(
                "Rerank query cannot be blank.",
                details={"provider": self.provider_name, "model": self.model},
            )
        if not chunks:
            return {}

        pairs = [
            (clean_query, f"{chunk.title}\n{chunk.content}".strip())
            for chunk in chunks
        ]
        model = self._load_model()
        try:
            raw_scores = model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=False,
            )
        except TypeError:
            raw_scores = model.predict(pairs)
        except Exception as exc:
            raise DependencyUnavailableError(
                "Hugging Face rerank model failed to score retrieval candidates.",
                details={"provider": self.provider_name, "model": self.model},
            ) from exc

        normalized_scores = _normalize_scores(_coerce_scores(raw_scores))
        if len(normalized_scores) != len(chunks):
            raise DependencyUnavailableError(
                "Hugging Face rerank response did not match candidate count.",
                details={
                    "provider": self.provider_name,
                    "model": self.model,
                    "expected_count": len(chunks),
                    "actual_count": len(normalized_scores),
                },
            )
        return {
            chunk.chunk_id: score
            for chunk, score in zip(chunks, normalized_scores, strict=True)
        }

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "enabled": self.enabled,
            "device": self.device,
            "batch_size": self.batch_size,
        }

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise DependencyUnavailableError(
                "Hugging Face reranking requires sentence-transformers. "
                "Install the project with the embeddings-local extra.",
                details={"provider": self.provider_name, "model": self.model},
            ) from exc

        model_kwargs: dict[str, Any] = {}
        if self.device != "auto":
            model_kwargs["device"] = self.device
        try:
            self._model = CrossEncoder(self.model, **model_kwargs)
        except Exception as exc:
            raise DependencyUnavailableError(
                "Hugging Face rerank model could not be loaded.",
                details={
                    "provider": self.provider_name,
                    "model": self.model,
                    "device": self.device,
                },
            ) from exc
        return self._model


def build_reranker(settings: Settings) -> Reranker:
    """Build the configured retrieval reranker."""

    if settings.rerank_provider == "huggingface":
        return HuggingFaceCrossEncoderReranker(
            model=settings.rerank_model,
            device=settings.rerank_device,
            batch_size=settings.rerank_batch_size,
        )
    return NullReranker()


def _coerce_scores(raw_scores: Any) -> list[float]:
    if hasattr(raw_scores, "tolist"):
        raw_scores = raw_scores.tolist()
    if isinstance(raw_scores, (int, float)):
        raw_scores = [raw_scores]
    scores: list[float] = []
    for score in raw_scores:
        if hasattr(score, "tolist"):
            score = score.tolist()
        if isinstance(score, (list, tuple)):
            if not score:
                raise DependencyUnavailableError(
                    "Hugging Face rerank response included an empty score vector."
                )
            score = max(float(value) for value in score)
        scores.append(float(score))
    return scores


def _normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []
    minimum = min(scores)
    maximum = max(scores)
    if maximum == minimum:
        return [0.0 for _ in scores]
    span = maximum - minimum
    return [(score - minimum) / span for score in scores]
