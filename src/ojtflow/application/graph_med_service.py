"""Application service for graph-med-backed knowledge-graph imports."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from ojtflow.core.contracts.knowledge_graph import (
    GraphMedLinkedEntity,
    GraphMedStatus,
    GraphScope,
    KnowledgeGraphChunk,
    KnowledgeGraphImportResult,
    KnowledgeGraphMention,
    KnowledgeGraphNode,
)
from ojtflow.core.errors import DependencyUnavailableError, ToolExecutionError
from ojtflow.core.time import utc_now

if TYPE_CHECKING:
    from ojtflow.application.ports import (
        GraphMedAnnotationPort,
        KnowledgeGraphRepository,
    )


class GraphMedService:
    """Orchestrate graph-med annotation and OJT provenance writes."""

    def __init__(
        self,
        repository: KnowledgeGraphRepository,
        graph_med_annotator: GraphMedAnnotationPort | None = None,
    ) -> None:
        self._repo = repository
        self._graph_med = graph_med_annotator

    def status(self) -> GraphMedStatus:
        if self._graph_med is None:
            return GraphMedStatus(
                enabled=False,
                available=False,
                ontology_loaded=False,
                gpu_required=False,
                gpu_available=False,
                gnn_endpoint_configured=False,
                gnn_endpoint_reachable=False,
                embedding_endpoint_configured=False,
                llm_endpoint_configured=False,
                embedding_endpoint_reachable=False,
                llm_endpoint_reachable=False,
                icd_vector_index="icd_disease_embedding",
                icd_disease_count=0,
                hpo_phenotype_count=0,
                umls_count=0,
                message="graph-med annotation service is not configured.",
            )
        return self._graph_med.status()

    def import_text(
        self,
        *,
        text: str,
        organization_id: str,
        scope: GraphScope = "organization",
        document_id: str | None = None,
        source_id: str | None = None,
        patient_id: str | None = None,
        encounter_id: str | None = None,
        concat_text: str | None = None,
        narrative_text: str | None = None,
    ) -> KnowledgeGraphImportResult:
        if scope != "organization":
            raise ToolExecutionError("graph-med imports must be organization-scoped.")
        status = self.status()
        if self._graph_med is None or not status.available:
            raise DependencyUnavailableError(
                status.message,
                details={"graph_med_status": status.model_dump()},
            )
        concat = (concat_text or "").strip()
        narrative = (narrative_text or text or "").strip()
        if not concat and not narrative:
            raise ToolExecutionError("Knowledge graph import requires text.")

        digest_source = "\n".join(part for part in (concat, narrative) if part)
        digest = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()[:12]  # noqa: S324
        chunk_id = f"import_{digest}"
        linked = self._graph_med.annotate_text(
            patient_id=patient_id or f"import_patient_{digest}",
            encounter_id=encounter_id or f"import_encounter_{digest}",
            concat_text=concat,
            narrative_text=narrative,
        )
        counts = self._upsert_graph_med_annotations(
            linked,
            chunk_id=chunk_id,
            chunk_text=narrative or concat,
            organization_id=organization_id,
            document_id=document_id or chunk_id,
            source_id=source_id,
        )
        return KnowledgeGraphImportResult(
            backend="graph-med",
            status="imported",
            chunks=counts["chunks"],
            nodes=counts["nodes"],
            edges=counts["edges"],
            entities=len(linked),
            linked_entities=sum(1 for entity in linked if entity.icd_id),
            message="Imported graph-med patient annotations.",
            graph_med_status=self.status(),
            annotations=linked,
        )

    def _upsert_graph_med_annotations(
        self,
        annotations: list[GraphMedLinkedEntity],
        *,
        chunk_id: str,
        chunk_text: str,
        organization_id: str,
        document_id: str,
        source_id: str | None,
    ) -> dict[str, int]:
        now = utc_now().isoformat()
        linked = [entity for entity in annotations if entity.icd_id and entity.icd_label]
        nodes = [
            KnowledgeGraphNode(
                node_id=f"icd-10:{entity.icd_id}",
                scope="organization",
                organization_id=organization_id,
                node_type="icd_disease",
                label=entity.icd_label or entity.text,
                normalized_code=entity.icd_id,
                code_system="ICD-10",
                aliases=[entity.text],
                attributes={
                    "graph_med_source": "patient_annotation",
                    "mention_text": entity.text,
                    "mention_label": entity.label,
                    "assertion": entity.assertion,
                    "temporality": entity.temporality,
                    "linking_rationale": entity.linking_rationale,
                },
                confidence=entity.confidence,
                review_state="accepted" if entity.assertion == "present" else "pending",
                created_at=now,
                updated_at=now,
            )
            for entity in linked
        ]
        if not nodes:
            self._repo.append_provenance(
                KnowledgeGraphChunk(
                    chunk_id=chunk_id,
                    scope="organization",
                    organization_id=organization_id,
                    document_id=document_id,
                    source_id=source_id,
                    snippet=chunk_text[:280],
                    created_at=now,
                ),
                [],
            )
            return {"chunks": 1, "nodes": 0, "edges": 0}

        self._repo.upsert_concepts(nodes)
        unique_node_ids = list(dict.fromkeys(node.node_id for node in nodes))
        self._repo.append_provenance(
            KnowledgeGraphChunk(
                chunk_id=chunk_id,
                scope="organization",
                organization_id=organization_id,
                document_id=document_id,
                source_id=source_id,
                snippet=chunk_text[:280],
                created_at=now,
            ),
            [
                KnowledgeGraphMention(chunk_id=chunk_id, node_id=node_id)
                for node_id in unique_node_ids
            ],
        )
        return {"chunks": 1, "nodes": len(unique_node_ids), "edges": 0}
