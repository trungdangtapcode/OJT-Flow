"""Static retrieval adapters for tests and local fallback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import RetrievalPackage, RetrievalQuery, RetrievalSource
from ojtflow.infrastructure.retrieval.engine import (
    DeterministicEmbeddingProvider,
    KnowledgeChunk,
    default_healthcare_chunks,
    rank_chunks,
    sources_from_chunks,
)


class StaticKnowledgeRepository:
    """Loads trusted schemas and fixture evidence from local files."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.schemas_dir = self.root / "schemas"

    def get_schema(self, schema_id: str | None) -> dict | None:
        if not schema_id:
            return None
        path = self.schemas_dir / f"{schema_id}.schema.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_schemas(self) -> list[dict]:
        """Return lightweight schema registry entries for the product UI."""

        schemas: list[dict] = []
        for path in sorted(self.schemas_dir.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            properties = schema.get("properties", {})
            schemas.append(
                {
                    "schema_id": schema.get("$id", path.name.removesuffix(".schema.json")),
                    "title": schema.get("title", schema.get("$id", path.stem)),
                    "version": schema.get("version", "unversioned"),
                    "required": schema.get("required", []),
                    "field_count": len(properties),
                    "fields": [
                        {
                            "name": name,
                            "type": definition.get("type", "unknown"),
                            "description": definition.get("description"),
                        }
                        for name, definition in properties.items()
                    ],
                    "source_ref": str(path.relative_to(self.root.parent)),
                }
            )
        return schemas

    def search(self, query: str, *, top_k: int = 5) -> list[Evidence]:
        """Backward-compatible evidence search for existing callers."""

        package = StaticRetrievalRepository(self.root).search(
            RetrievalQuery(query=query, top_k=top_k)
        )
        return package.evidence


class StaticRetrievalRepository:
    """Deterministic hybrid retrieval over local healthcare knowledge chunks."""

    def __init__(
        self,
        root: Path | str,
        embedding_provider: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider()
        self._chunks = default_healthcare_chunks(self.root)

    def search(self, query: RetrievalQuery) -> RetrievalPackage:
        chunks = self._filter_chunks(self._chunks, query)
        warnings = (
            []
            if chunks
            else ["No retrieval chunks matched filters; returning empty package."]
        )
        return rank_chunks(
            chunks,
            query,
            embedding_provider=self.embedding_provider,
            strategy="static_hybrid_rrf",
            warnings=warnings,
        )

    def list_sources(self) -> list[RetrievalSource]:
        return sources_from_chunks(self._chunks)

    def _filter_chunks(
        self,
        chunks: list[KnowledgeChunk],
        query: RetrievalQuery,
    ) -> list[KnowledgeChunk]:
        trust_level = query.filters.get("trust_level")
        clinical_domain = query.filters.get("clinical_domain")
        standard_system = query.filters.get("standard_system")
        filtered = chunks
        if trust_level:
            filtered = [chunk for chunk in filtered if chunk.trust_level == TrustLevel(trust_level)]
        if clinical_domain:
            filtered = [chunk for chunk in filtered if chunk.clinical_domain == clinical_domain]
        if standard_system:
            filtered = [chunk for chunk in filtered if chunk.standard_system == standard_system]
        return filtered
