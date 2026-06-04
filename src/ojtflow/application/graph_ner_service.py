"""Deterministic Graph-NER handoff for retrieval packages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import RetrievalPackage, RetrievalQuery


STANDARD_PATTERNS = {
    "FHIR": re.compile(r"\b(FHIR|Observation|Bundle|Patient|DiagnosticReport)\b", re.I),
    "LOINC": re.compile(r"\b(LOINC)\b", re.I),
    "UCUM": re.compile(r"\b(UCUM|unit|units)\b", re.I),
    "RxNorm": re.compile(r"\b(RxNorm|medication|drug)\b", re.I),
    "OMOP": re.compile(r"\b(OMOP|CDM|Common Data Model)\b", re.I),
}
FIELD_PATTERN = re.compile(r"\b(date|patient_id|lab_name|value|unit|status|code|subject)\b", re.I)
LAB_PATTERN = re.compile(r"\b(HbA1c|A1c|glucose|laboratory|lab result)\b", re.I)


@dataclass(frozen=True)
class GraphNERService:
    """Builds a small evidence graph from retrieved context."""

    max_entities: int = 40
    max_triples: int = 80

    def augment_package(
        self,
        package: RetrievalPackage,
        query: RetrievalQuery,
    ) -> RetrievalPackage:
        graph_context = self.build_graph_context(package.evidence, query)
        handoff_context = {
            **package.handoff_context,
            "graph_context": graph_context,
        }
        return package.model_copy(update={"handoff_context": handoff_context})

    def build_graph_context(
        self,
        evidence: list[Evidence],
        query: RetrievalQuery,
    ) -> dict[str, Any]:
        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []
        triples: list[dict[str, Any]] = []

        query_node = _node("query:current", "Retrieval Query", "query")
        nodes[query_node["id"]] = query_node

        for field in query.fields:
            entity = _node(f"field:{field.lower()}", field, "data_field")
            nodes.setdefault(entity["id"], entity)
            edges.append(_edge(query_node["id"], "mentions_field", entity["id"]))

        if query.resource_type:
            entity = _node(
                f"resource:{query.resource_type.lower()}",
                query.resource_type,
                "fhir_resource",
            )
            nodes.setdefault(entity["id"], entity)
            edges.append(_edge(query_node["id"], "requests_resource", entity["id"]))

        for ev in evidence:
            evidence_node = _node(f"evidence:{ev.evidence_id}", ev.source_id, "evidence")
            nodes[evidence_node["id"]] = evidence_node
            claim_entities = _entities_from_claim(ev.claim)
            locator = ev.locator or {}
            for locator_key in ("standard_system", "clinical_domain"):
                value = locator.get(locator_key)
                if value:
                    claim_entities.append(
                        {
                            "id": f"{locator_key}:{str(value).lower()}",
                            "label": str(value),
                            "type": locator_key,
                        }
                    )
            for entity in claim_entities:
                nodes.setdefault(entity["id"], entity)
                edges.append(_edge(evidence_node["id"], "supports", entity["id"], ev.evidence_id))
                triples.append(
                    {
                        "subject": ev.source_id,
                        "predicate": "supports",
                        "object": entity["label"],
                        "evidence_id": ev.evidence_id,
                    }
                )

        deduped_edges = _dedupe_edges(edges)
        return {
            "graph_contract": "graph_ner_handoff.v0",
            "nodes": list(nodes.values())[: self.max_entities],
            "edges": deduped_edges[: self.max_triples],
            "triples": triples[: self.max_triples],
            "limits": {
                "max_entities": self.max_entities,
                "max_triples": self.max_triples,
            },
        }


def _entities_from_claim(claim: str) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    for entity_type, pattern in STANDARD_PATTERNS.items():
        for match in pattern.finditer(claim):
            label = match.group(0)
            normalized = entity_type if entity_type in {"FHIR", "LOINC", "UCUM", "OMOP"} else label
            entities.append(_node(f"standard:{normalized.lower()}", normalized, "standard"))
    for pattern, entity_type in [(FIELD_PATTERN, "data_field"), (LAB_PATTERN, "clinical_concept")]:
        for match in pattern.finditer(claim):
            label = match.group(0)
            entities.append(_node(f"{entity_type}:{label.lower()}", label, entity_type))
    return _dedupe_nodes(entities)


def _node(node_id: str, label: str, node_type: str) -> dict[str, Any]:
    return {"id": node_id, "label": label, "type": node_type}


def _edge(
    source: str,
    relation: str,
    target: str,
    evidence_id: str | None = None,
) -> dict[str, Any]:
    edge = {"source": source, "relation": relation, "target": target}
    if evidence_id:
        edge["evidence_id"] = evidence_id
    return edge


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for node in nodes:
        deduped.setdefault(node["id"], node)
    return list(deduped.values())


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str, str, str | None], dict[str, Any]] = {}
    for edge in edges:
        key = (
            edge["source"],
            edge["relation"],
            edge["target"],
            edge.get("evidence_id"),
        )
        deduped.setdefault(key, edge)
    return list(deduped.values())
