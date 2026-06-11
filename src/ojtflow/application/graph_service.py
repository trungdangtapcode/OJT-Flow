"""Persistence and export service for Graph-NER contexts."""

from __future__ import annotations

import json
from typing import Any

from ojtflow.application.ports import GraphRepository
from ojtflow.core.contracts.graph import GraphContextRecord, GraphExport, GraphExportFormat
from ojtflow.core.contracts.retrieval import RetrievalPackage, RetrievalQuery
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


class GraphService:
    """Stores Graph-NER handoff contexts and exports graph records."""

    def __init__(self, repository: GraphRepository) -> None:
        self.repository = repository

    def persist_retrieval_package(
        self,
        package: RetrievalPackage,
        query: RetrievalQuery,
        *,
        owner_user_id: str | None,
    ) -> RetrievalPackage:
        graph_context = package.handoff_context.get("graph_context")
        if not isinstance(graph_context, dict):
            return package
        summary = graph_context.get("summary")
        summary = summary if isinstance(summary, dict) else {}
        record = self.repository.save_context(
            GraphContextRecord(
                graph_id=new_id("graph"),
                owner_user_id=owner_user_id,
                workflow_id=query.workflow_id,
                request_id=package.trace.request_id,
                search_signature=_optional_str(package.handoff_context.get("search_signature")),
                query=query.query,
                resource_type=query.resource_type,
                fields=[field for field in query.fields if field.strip()],
                node_count=_non_negative_int(summary.get("node_count")),
                edge_count=_non_negative_int(summary.get("edge_count")),
                triple_count=_non_negative_int(summary.get("triple_count")),
                graph_context=graph_context,
                created_at=utc_now().isoformat(),
            )
        )
        handoff_context = {
            **package.handoff_context,
            "graph_record": _record_summary(record),
        }
        return package.model_copy(update={"handoff_context": handoff_context})

    def list_contexts(
        self,
        *,
        owner_user_id: str | None,
        workflow_id: str | None = None,
        limit: int = 100,
    ) -> list[GraphContextRecord]:
        return self.repository.list_contexts(
            owner_user_id=owner_user_id,
            workflow_id=workflow_id,
            limit=limit,
        )

    def export_contexts(
        self,
        *,
        owner_user_id: str | None,
        workflow_id: str | None = None,
        limit: int = 100,
        export_format: GraphExportFormat = "jsonl",
    ) -> GraphExport:
        records = self.list_contexts(
            owner_user_id=owner_user_id,
            workflow_id=workflow_id,
            limit=limit,
        )
        lines = (
            _rdf_jsonl_lines(records)
            if export_format == "rdf_jsonl"
            else _graph_jsonl_lines(records)
        )
        return GraphExport(
            format=export_format,
            content_type="application/x-ndjson",
            graph_count=len(records),
            node_count=sum(record.node_count for record in records),
            edge_count=sum(record.edge_count for record in records),
            triple_count=sum(record.triple_count for record in records),
            generated_at=utc_now().isoformat(),
            content="\n".join(json.dumps(line, sort_keys=True) for line in lines),
        )


def _graph_jsonl_lines(records: list[GraphContextRecord]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for record in records:
        base = _record_line_base(record)
        graph = record.graph_context
        for node in graph.get("nodes") or []:
            if isinstance(node, dict):
                lines.append({**base, "record_type": "node", "node": node})
        for edge in graph.get("edges") or []:
            if isinstance(edge, dict):
                lines.append({**base, "record_type": "edge", "edge": edge})
        for triple in graph.get("triples") or []:
            if isinstance(triple, dict):
                lines.append({**base, "record_type": "triple", "triple": triple})
    return lines


def _rdf_jsonl_lines(records: list[GraphContextRecord]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for record in records:
        base = _record_line_base(record)
        for triple in record.graph_context.get("triples") or []:
            if isinstance(triple, dict):
                lines.append(
                    {
                        **base,
                        "subject": triple.get("subject"),
                        "predicate": triple.get("predicate"),
                        "object": triple.get("object"),
                        "evidence_id": triple.get("evidence_id"),
                    }
                )
    return lines


def _record_line_base(record: GraphContextRecord) -> dict[str, Any]:
    return {
        "graph_id": record.graph_id,
        "owner_user_id": record.owner_user_id,
        "workflow_id": record.workflow_id,
        "search_signature": record.search_signature,
        "created_at": record.created_at,
    }


def _record_summary(record: GraphContextRecord) -> dict[str, Any]:
    return {
        "graph_id": record.graph_id,
        "workflow_id": record.workflow_id,
        "search_signature": record.search_signature,
        "node_count": record.node_count,
        "edge_count": record.edge_count,
        "triple_count": record.triple_count,
        "created_at": record.created_at,
    }


def _non_negative_int(value: Any) -> int:
    if isinstance(value, int) and value >= 0:
        return value
    return 0


def _optional_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
