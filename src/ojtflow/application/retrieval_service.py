"""Application service for evidence retrieval."""

from __future__ import annotations

from ojtflow.application.ports import RetrievalRepository
from ojtflow.core.contracts.data import DataProfile
from ojtflow.core.contracts.retrieval import RetrievalPackage, RetrievalQuery, RetrievalSource


class RetrievalService:
    """Builds retrieval queries and delegates ranking to replaceable adapters."""

    def __init__(self, repository: RetrievalRepository) -> None:
        self.repository = repository

    def search(self, query: RetrievalQuery) -> RetrievalPackage:
        """Run direct retrieval."""

        return self.repository.search(query)

    def list_sources(self) -> list[RetrievalSource]:
        """List configured retrieval sources."""

        return self.repository.list_sources()

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
