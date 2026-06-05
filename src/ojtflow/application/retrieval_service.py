"""Application service for evidence retrieval."""

from __future__ import annotations

from collections.abc import Sequence
import json
from hashlib import sha256
from typing import Any

from ojtflow.application.graph_ner_service import GraphNERService
from ojtflow.application.ports import RetrievalRepository
from ojtflow.core.contracts.data import DataProfile
from ojtflow.core.contracts.retrieval import (
    RetrievalIntegrityReport,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalSource,
)


class RetrievalService:
    """Builds retrieval queries and delegates ranking to replaceable adapters."""

    def __init__(
        self,
        repository: RetrievalRepository,
        graph_ner: GraphNERService | None = None,
        rule_packs: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        self.repository = repository
        self.graph_ner = graph_ner or GraphNERService()
        self.rule_packs = [dict(pack) for pack in rule_packs or ()]

    def search(self, query: RetrievalQuery) -> RetrievalPackage:
        """Run direct retrieval."""

        package = self.repository.search(query)
        package = self._attach_search_metadata(package, query)
        package = self._attach_rule_pack_metadata(package)
        return self.graph_ner.augment_package(package, query)

    def list_sources(self) -> list[RetrievalSource]:
        """List configured retrieval sources."""

        return self.repository.list_sources()

    def reindex(self, *, include_seeded: bool = True, include_corpus: bool = True) -> dict:
        """Refresh retrieval index from configured trusted sources."""

        return self.repository.reindex(
            include_seeded=include_seeded,
            include_corpus=include_corpus,
        )

    def integrity_report(
        self,
        *,
        include_seeded: bool = True,
        include_corpus: bool = False,
    ) -> RetrievalIntegrityReport:
        """Check whether indexed retrieval knowledge matches trusted sources."""

        return self.repository.integrity_report(
            include_seeded=include_seeded,
            include_corpus=include_corpus,
        )

    def search_for_workflow(
        self,
        *,
        workflow_id: str,
        instruction: str,
        profile: DataProfile,
        schema_id: str | None,
        resource_type: str | None = None,
        query_terms: list[str] | None = None,
        top_k: int = 5,
    ) -> RetrievalPackage:
        """Build workflow-aware retrieval context from instruction and profile."""

        field_names = [field.name for field in profile.fields]
        query_parts = [
            instruction,
            f"fields: {', '.join(field_names)}" if field_names else "",
            f"schema: {schema_id}" if schema_id else "",
            f"format: {profile.format.value}",
            f"FHIR resource: {resource_type}" if resource_type else "",
            " ".join(query_terms or []),
        ]
        query = RetrievalQuery(
            query=" ".join(part for part in query_parts if part),
            workflow_id=workflow_id,
            fields=field_names,
            schema_id=schema_id,
            detected_format=profile.format.value,
            resource_type=resource_type,
            top_k=top_k,
            filters={"trust_level": "approved"},
        )
        return self.search(query)

    def _attach_rule_pack_metadata(self, package: RetrievalPackage) -> RetrievalPackage:
        if not self.rule_packs:
            return package
        handoff_context = {
            **package.handoff_context,
            "retrieval_rule_packs": self.rule_packs,
        }
        return package.model_copy(update={"handoff_context": handoff_context})

    def _attach_search_metadata(
        self,
        package: RetrievalPackage,
        query: RetrievalQuery,
    ) -> RetrievalPackage:
        request = _search_request_payload(query)
        handoff_context = {
            **package.handoff_context,
            "search_request": request,
            "search_signature": _search_request_signature(request),
        }
        return package.model_copy(update={"handoff_context": handoff_context})


def _search_request_payload(query: RetrievalQuery) -> dict[str, Any]:
    return {
        "query": query.query,
        "workflow_id": query.workflow_id,
        "fields": list(query.fields),
        "schema_id": query.schema_id,
        "detected_format": query.detected_format,
        "resource_type": query.resource_type,
        "top_k": query.top_k,
        "filters": dict(query.filters),
    }


def _search_request_signature(request: dict[str, Any]) -> str:
    encoded = json.dumps(
        request,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"sha256:{sha256(encoded.encode('utf-8')).hexdigest()}"
