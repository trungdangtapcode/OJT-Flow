"""Persistence and export service for Graph-NER contexts."""

from __future__ import annotations

import json
from typing import Any

from ojtflow.application.ports import GraphRepository
from ojtflow.core.contracts.graph import (
    GraphContextRecord,
    GraphExport,
    GraphExportFormat,
    GraphNeighborhood,
    GraphNeighborhoodQuery,
)
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

    def neighborhood(
        self,
        *,
        owner_user_id: str | None,
        query: GraphNeighborhoodQuery,
    ) -> GraphNeighborhood:
        records = self.list_contexts(
            owner_user_id=owner_user_id,
            workflow_id=query.workflow_id,
            limit=query.limit,
        )
        nodes: dict[tuple[str, str], dict[str, Any]] = {}
        edges: dict[tuple[str, str, str, str, str | None], dict[str, Any]] = {}
        triples: dict[tuple[str, str, str, str, str | None], dict[str, Any]] = {}
        source_graph_ids: set[str] = set()
        matched_node_ids: set[str] = set()
        matched_evidence_ids: set[str] = set()
        explicit_criteria = _has_explicit_neighborhood_criteria(query)

        for record in records:
            graph = record.graph_context
            record_nodes = [
                node for node in graph.get("nodes") or []
                if isinstance(node, dict) and _node_id(node)
            ]
            record_edges = [
                edge for edge in graph.get("edges") or []
                if isinstance(edge, dict)
                and _edge_endpoint(edge, "source")
                and _edge_endpoint(edge, "target")
            ]
            record_triples = [
                triple for triple in graph.get("triples") or []
                if isinstance(triple, dict)
            ]
            nodes_by_id = {_node_id(node): node for node in record_nodes}
            label_to_ids = _node_label_index(record_nodes)
            seed_ids = _seed_node_ids(
                record=record,
                query=query,
                nodes=record_nodes,
                edges=record_edges,
                triples=record_triples,
                nodes_by_id=nodes_by_id,
                label_to_ids=label_to_ids,
                explicit_criteria=explicit_criteria,
            )
            if not seed_ids:
                continue
            source_graph_ids.add(record.graph_id)
            matched_node_ids.update(seed_ids)
            expanded_ids = set(seed_ids)
            included_edges = _expand_edges(
                seed_ids=seed_ids,
                edges=record_edges,
                max_depth=query.max_depth,
            )
            for edge in included_edges:
                source = _edge_endpoint(edge, "source")
                target = _edge_endpoint(edge, "target")
                if source:
                    expanded_ids.add(source)
                if target:
                    expanded_ids.add(target)
                evidence_id = _optional_str(edge.get("evidence_id"))
                if evidence_id:
                    matched_evidence_ids.add(evidence_id)
                edges[
                    (
                        record.graph_id,
                        source or "",
                        _optional_str(edge.get("relation")) or "",
                        target or "",
                        evidence_id,
                    )
                ] = _with_record_ref(record, edge)
            for node_id in expanded_ids:
                node = nodes_by_id.get(node_id)
                if node is not None:
                    nodes[(record.graph_id, node_id)] = _with_record_ref(record, node)
                    evidence_id = _evidence_id_from_node(node)
                    if evidence_id:
                        matched_evidence_ids.add(evidence_id)
            included_labels = {
                str(nodes_by_id[node_id].get("label")).casefold()
                for node_id in expanded_ids
                if node_id in nodes_by_id and nodes_by_id[node_id].get("label")
            }
            for triple in record_triples:
                if _include_triple(
                    triple,
                    query=query,
                    included_labels=included_labels,
                    matched_evidence_ids=matched_evidence_ids,
                    explicit_criteria=explicit_criteria,
                ):
                    evidence_id = _optional_str(triple.get("evidence_id"))
                    if evidence_id:
                        matched_evidence_ids.add(evidence_id)
                    triples[
                        (
                            record.graph_id,
                            _optional_str(triple.get("subject")) or "",
                            _optional_str(triple.get("predicate")) or "",
                            _optional_str(triple.get("object")) or "",
                            evidence_id,
                        )
                    ] = _with_record_ref(record, triple)

        warnings = []
        if not records:
            warnings.append("No persisted graph contexts matched the owner/workflow scope.")
        elif not nodes and explicit_criteria:
            warnings.append("No graph neighborhood matched the supplied criteria.")

        return GraphNeighborhood(
            query=query,
            source_graph_ids=sorted(source_graph_ids),
            graph_count=len(source_graph_ids),
            node_count=len(nodes),
            edge_count=len(edges),
            triple_count=len(triples),
            matched_node_ids=sorted(matched_node_ids),
            matched_evidence_ids=sorted(matched_evidence_ids),
            nodes=list(nodes.values()),
            edges=list(edges.values()),
            triples=list(triples.values()),
            warnings=warnings,
            generated_at=utc_now().isoformat(),
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


def _seed_node_ids(
    *,
    record: GraphContextRecord,
    query: GraphNeighborhoodQuery,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    triples: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
    label_to_ids: dict[str, set[str]],
    explicit_criteria: bool,
) -> set[str]:
    if not explicit_criteria:
        return {_node_id(node) for node in nodes if _node_id(node)}
    seed_ids = {
        _node_id(node)
        for node in nodes
        if _node_id(node) and _node_matches(node, query=query, record_query=record.query)
    }
    for edge in edges:
        if _edge_matches(edge, query=query, nodes_by_id=nodes_by_id):
            source = _edge_endpoint(edge, "source")
            target = _edge_endpoint(edge, "target")
            if source:
                seed_ids.add(source)
            if target:
                seed_ids.add(target)
    for triple in triples:
        if _triple_matches(triple, query=query):
            evidence_id = _optional_str(triple.get("evidence_id"))
            if evidence_id:
                seed_ids.add(f"evidence:{evidence_id}")
            for value in (triple.get("subject"), triple.get("object")):
                seed_ids.update(label_to_ids.get(str(value).casefold(), set()))
    if query.q and _text_matches(record.query, query.q):
        seed_ids.update(_node_id(node) for node in nodes if _node_id(node))
    return {node_id for node_id in seed_ids if node_id in nodes_by_id}


def _expand_edges(
    *,
    seed_ids: set[str],
    edges: list[dict[str, Any]],
    max_depth: int,
) -> list[dict[str, Any]]:
    if max_depth <= 0:
        return []
    frontier = set(seed_ids)
    seen_nodes = set(seed_ids)
    included: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str, str | None]] = set()
    for _depth in range(max_depth):
        next_frontier: set[str] = set()
        for edge in edges:
            source = _edge_endpoint(edge, "source")
            target = _edge_endpoint(edge, "target")
            if not source or not target:
                continue
            if source not in frontier and target not in frontier:
                continue
            key = (
                source,
                _optional_str(edge.get("relation")) or "",
                target,
                _optional_str(edge.get("evidence_id")),
            )
            if key not in seen_edges:
                included.append(edge)
                seen_edges.add(key)
            for node_id in (source, target):
                if node_id not in seen_nodes:
                    next_frontier.add(node_id)
                    seen_nodes.add(node_id)
        frontier = next_frontier
        if not frontier:
            break
    return included


def _include_triple(
    triple: dict[str, Any],
    *,
    query: GraphNeighborhoodQuery,
    included_labels: set[str],
    matched_evidence_ids: set[str],
    explicit_criteria: bool,
) -> bool:
    evidence_id = _optional_str(triple.get("evidence_id"))
    if evidence_id and evidence_id in matched_evidence_ids:
        return True
    subject = _optional_str(triple.get("subject"))
    object_value = _optional_str(triple.get("object"))
    if subject and subject.casefold() in included_labels:
        return True
    if object_value and object_value.casefold() in included_labels:
        return True
    return explicit_criteria and _triple_matches(triple, query=query)


def _node_matches(
    node: dict[str, Any],
    *,
    query: GraphNeighborhoodQuery,
    record_query: str = "",
) -> bool:
    node_id = _node_id(node)
    if query.node_id and node_id == query.node_id:
        return True
    if query.evidence_id and node_id == f"evidence:{query.evidence_id}":
        return True
    node_type = _node_type(node)
    if query.source_id and node_type == "evidence":
        if _text_equals(node.get("label"), query.source_id):
            return True
    if query.normalized_code:
        if _text_equals(node.get("normalized_code"), query.normalized_code):
            return True
        if node_type == "standard_code" and _text_equals(
            node.get("label"),
            query.normalized_code,
        ):
            return True
    if query.resource_type and node_type == "fhir_resource":
        if _text_equals(node.get("label"), query.resource_type):
            return True
    if query.field and node_type == "data_field":
        if _text_equals(node.get("label"), query.field) or _text_matches(node_id, query.field):
            return True
    if query.q:
        searchable = [
            node_id,
            node.get("label"),
            node_type,
            node.get("matched_text"),
            node.get("normalized_code"),
            node.get("normalized_display"),
            node.get("clinical_domain"),
            node.get("standard_system"),
            record_query,
        ]
        return any(_text_matches(value, query.q) for value in searchable)
    return False


def _edge_matches(
    edge: dict[str, Any],
    *,
    query: GraphNeighborhoodQuery,
    nodes_by_id: dict[str, dict[str, Any]],
) -> bool:
    if query.relation and _text_equals(edge.get("relation"), query.relation):
        return True
    if query.evidence_id and _text_equals(edge.get("evidence_id"), query.evidence_id):
        return True
    for endpoint in (_edge_endpoint(edge, "source"), _edge_endpoint(edge, "target")):
        node = nodes_by_id.get(endpoint or "")
        if node is not None and _node_matches(node, query=query):
            return True
    return False


def _triple_matches(triple: dict[str, Any], *, query: GraphNeighborhoodQuery) -> bool:
    if query.relation and _text_equals(triple.get("predicate"), query.relation):
        return True
    if query.evidence_id and _text_equals(triple.get("evidence_id"), query.evidence_id):
        return True
    if query.source_id and _text_equals(triple.get("subject"), query.source_id):
        return True
    if query.normalized_code:
        if _text_equals(triple.get("subject"), query.normalized_code):
            return True
        if _text_equals(triple.get("object"), query.normalized_code):
            return True
    if query.q:
        return any(
            _text_matches(value, query.q)
            for value in (triple.get("subject"), triple.get("predicate"), triple.get("object"))
        )
    return False


def _node_label_index(nodes: list[dict[str, Any]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for node in nodes:
        label = _optional_str(node.get("label"))
        node_id = _node_id(node)
        if label and node_id:
            index.setdefault(label.casefold(), set()).add(node_id)
    return index


def _with_record_ref(record: GraphContextRecord, value: dict[str, Any]) -> dict[str, Any]:
    return {
        "graph_id": record.graph_id,
        "workflow_id": record.workflow_id,
        "search_signature": record.search_signature,
        **value,
    }


def _has_explicit_neighborhood_criteria(query: GraphNeighborhoodQuery) -> bool:
    return any(
        (
            query.q,
            query.node_id,
            query.evidence_id,
            query.source_id,
            query.normalized_code,
            query.resource_type,
            query.field,
            query.relation,
        )
    )


def _node_id(node: dict[str, Any]) -> str:
    value = node.get("id") or node.get("node_id")
    return value if isinstance(value, str) and value.strip() else ""


def _node_type(node: dict[str, Any]) -> str | None:
    value = node.get("type") or node.get("kind")
    return value if isinstance(value, str) and value.strip() else None


def _edge_endpoint(edge: dict[str, Any], key: str) -> str | None:
    return _optional_str(edge.get(key))


def _evidence_id_from_node(node: dict[str, Any]) -> str | None:
    node_id = _node_id(node)
    if node_id.startswith("evidence:"):
        return node_id.removeprefix("evidence:")
    return None


def _text_equals(left: Any, right: str) -> bool:
    return isinstance(left, str) and left.casefold() == right.casefold()


def _text_matches(value: Any, query: str) -> bool:
    if not isinstance(value, str):
        return False
    haystack = value.casefold()
    needle = query.casefold()
    if needle in haystack:
        return True
    tokens = [token for token in needle.replace(":", " ").split() if len(token) >= 2]
    return any(token in haystack for token in tokens)


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
