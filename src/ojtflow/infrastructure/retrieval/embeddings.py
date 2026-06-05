"""Embedding provider adapters for retrieval."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Protocol

import httpx

from ojtflow.config import Settings
from ojtflow.core.errors import DependencyUnavailableError, OJTFlowError
from ojtflow.infrastructure.retrieval.engine import (
    DeterministicEmbeddingProvider,
    NullEmbeddingProvider,
)


class EmbeddingProvider(Protocol):
    """Small provider surface used by retrieval ranking and indexing."""

    provider_name: str
    model: str
    dimensions: int

    def embed_query(self, text: str) -> list[float]:
        """Embed a user/search query."""

    def embed_document(self, text: str) -> list[float]:
        """Embed a trusted knowledge chunk."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed trusted knowledge chunks in a batch."""

    def metadata(self) -> dict[str, Any]:
        """Return non-secret provider metadata for traces."""


class OpenAIEmbeddingProvider:
    """OpenAI embeddings adapter using the project HTTP client dependency."""

    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimensions: int,
        base_url: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise DependencyUnavailableError(
                "OpenAI embeddings require OJT_OPENAI_API_KEY or OPENAI_API_KEY.",
                details={"provider": self.provider_name, "model": model},
            )
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._client = client
        self._cache: dict[str, list[float]] = {}

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text, purpose="query")

    def embed_document(self, text: str) -> list[float]:
        return self._embed_one(text, purpose="document")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        missing = [text for text in texts if self._cache_key("document", text) not in self._cache]
        if missing:
            embeddings = self._request_embeddings(missing)
            for text, embedding in zip(missing, embeddings, strict=True):
                self._cache[self._cache_key("document", text)] = embedding
        return [self._cache[self._cache_key("document", text)] for text in texts]

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "dimensions": self.dimensions,
            "normalized": True,
        }

    def _embed_one(self, text: str, *, purpose: str) -> list[float]:
        key = self._cache_key(purpose, text)
        if key not in self._cache:
            self._cache[key] = self._request_embeddings([text])[0]
        return self._cache[key]

    def _cache_key(self, purpose: str, text: str) -> str:
        return f"{purpose}:{text}"

    def _request_embeddings(self, texts: list[str]) -> list[list[float]]:
        clean_texts = [text.strip() for text in texts]
        if any(not text for text in clean_texts):
            raise OJTFlowError(
                "Embedding input cannot be blank.",
                details={"provider": self.provider_name, "model": self.model},
            )
        payload: dict[str, Any] = {
            "model": self.model,
            "input": clean_texts,
            "encoding_format": "float",
        }
        if self.model.startswith("text-embedding-3-"):
            payload["dimensions"] = self.dimensions

        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        close_client = self._client is None
        try:
            response = client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            raise DependencyUnavailableError(
                "OpenAI embeddings request failed.",
                details={
                    "provider": self.provider_name,
                    "model": self.model,
                    "status_code": exc.response.status_code,
                },
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise DependencyUnavailableError(
                "OpenAI embeddings service is unavailable.",
                details={"provider": self.provider_name, "model": self.model},
            ) from exc
        finally:
            if close_client:
                client.close()

        data = body.get("data")
        if not isinstance(data, list) or len(data) != len(clean_texts):
            raise DependencyUnavailableError(
                "OpenAI embeddings response had an unexpected shape.",
                details={"provider": self.provider_name, "model": self.model},
            )

        by_index: dict[int, list[float]] = {}
        for item in data:
            index = item.get("index")
            embedding = item.get("embedding")
            if not isinstance(index, int) or not isinstance(embedding, list):
                raise DependencyUnavailableError(
                    "OpenAI embeddings response included an invalid item.",
                    details={"provider": self.provider_name, "model": self.model},
                )
            vector = [float(value) for value in embedding]
            if len(vector) != self.dimensions:
                raise DependencyUnavailableError(
                    "OpenAI embeddings response dimension does not match configuration.",
                    details={
                        "provider": self.provider_name,
                        "model": self.model,
                        "expected_dimensions": self.dimensions,
                        "actual_dimensions": len(vector),
                    },
                )
            by_index[index] = _normalize(vector)

        try:
            return [by_index[index] for index in range(len(clean_texts))]
        except KeyError as exc:
            raise DependencyUnavailableError(
                "OpenAI embeddings response did not include all requested inputs.",
                details={"provider": self.provider_name, "model": self.model},
            ) from exc


class HuggingFaceEmbeddingProvider:
    """GPU-ready local SentenceTransformers embedding adapter."""

    provider_name = "huggingface"

    def __init__(
        self,
        *,
        model: str,
        dimensions: int,
        device: str,
        batch_size: int,
        cache_dir: Path,
        model_instance: Any | None = None,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self.device = device
        self.batch_size = batch_size
        self.cache_dir = cache_dir
        self._model = model_instance

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text, query=True)

    def embed_document(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._encode(texts, query=False)

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "dimensions": self.dimensions,
            "device": self.device,
            "batch_size": self.batch_size,
            "normalized": True,
        }

    def _embed_one(self, text: str, *, query: bool) -> list[float]:
        return self._encode([text], query=query)[0]

    def _encode(self, texts: list[str], *, query: bool) -> list[list[float]]:
        clean_texts = [text.strip() for text in texts]
        if any(not text for text in clean_texts):
            raise OJTFlowError(
                "Embedding input cannot be blank.",
                details={"provider": self.provider_name, "model": self.model},
            )

        model = self._load_model()
        method_name = "encode_query" if query else "encode_document"
        encode = getattr(model, method_name, None) or getattr(model, "encode")
        try:
            raw_vectors = encode(
                clean_texts,
                batch_size=self.batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=False,
            )
        except TypeError:
            raw_vectors = encode(clean_texts)
        except Exception as exc:
            raise DependencyUnavailableError(
                "Hugging Face embedding model failed to encode text.",
                details={"provider": self.provider_name, "model": self.model},
            ) from exc

        vectors = [_coerce_vector(vector) for vector in raw_vectors]
        for vector in vectors:
            if len(vector) != self.dimensions:
                raise DependencyUnavailableError(
                    "Hugging Face embedding dimension does not match configuration.",
                    details={
                        "provider": self.provider_name,
                        "model": self.model,
                        "expected_dimensions": self.dimensions,
                        "actual_dimensions": len(vector),
                    },
                )
        return [_normalize(vector) for vector in vectors]

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise DependencyUnavailableError(
                "Hugging Face embeddings require sentence-transformers. "
                "Install the project with the embeddings-local extra.",
                details={"provider": self.provider_name, "model": self.model},
            ) from exc

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        model_kwargs: dict[str, Any] = {
            "cache_folder": str(self.cache_dir),
        }
        if self.device != "auto":
            model_kwargs["device"] = self.device
        try:
            self._model = SentenceTransformer(self.model, **model_kwargs)
        except Exception as exc:
            raise DependencyUnavailableError(
                "Hugging Face embedding model could not be loaded.",
                details={
                    "provider": self.provider_name,
                    "model": self.model,
                    "device": self.device,
                },
            ) from exc
        return self._model


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Build the configured embedding provider."""

    if settings.embedding_provider == "deterministic":
        return DeterministicEmbeddingProvider(settings.embedding_dimensions)
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            base_url=settings.openai_embedding_base_url,
            timeout_seconds=settings.openai_embedding_timeout_seconds,
        )
    if settings.embedding_provider == "huggingface":
        return HuggingFaceEmbeddingProvider(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            device=settings.hf_embedding_device,
            batch_size=settings.hf_embedding_batch_size,
            cache_dir=settings.resolved_hf_embedding_cache_dir,
        )
    return NullEmbeddingProvider()


def _coerce_vector(vector: Any) -> list[float]:
    if hasattr(vector, "tolist"):
        vector = vector.tolist()
    return [float(value) for value in vector]


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]
