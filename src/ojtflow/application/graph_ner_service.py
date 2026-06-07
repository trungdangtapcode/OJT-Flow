"""Deterministic Graph-NER handoff for retrieval packages."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
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
LAB_PATTERN = re.compile(r"\b(laboratory|lab result)\b", re.I)

# Reuse the same seed registry (and path override) as deterministic query
# normalization in ojtflow.infrastructure.retrieval.query_analysis, so both
# consumers stay aligned with one source of truth for concept-to-code mapping.
DEFAULT_CONCEPT_REGISTRY = (
    Path(__file__).resolve().parents[3] / "knowledge" / "terminologies" / "medical_concepts.json"
)
CONCEPT_REGISTRY_ENV_VAR = "OJT_MEDICAL_CONCEPT_REGISTRY_PATH"


@lru_cache(maxsize=4)
def _load_concept_registry(path_text: str) -> tuple[dict[str, Any], ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    concepts = raw.get("concepts") if isinstance(raw, dict) else None
    if not isinstance(concepts, list):
        return ()
    required = {"concept_id", "display_name", "standard_system", "code", "aliases"}
    valid: list[dict[str, Any]] = []
    for concept in concepts:
        if isinstance(concept, dict) and required.issubset(concept) and isinstance(concept["aliases"], list):
            valid.append(concept)
    return tuple(valid)


def _concept_registry() -> tuple[dict[str, Any], ...]:
    path = os.environ.get(CONCEPT_REGISTRY_ENV_VAR)
    return _load_concept_registry(path or str(DEFAULT_CONCEPT_REGISTRY))


@lru_cache(maxsize=1)
def _concept_alias_index() -> dict[str, dict[str, Any]]:
    """Map normalized alias text to its registry concept entry."""

    index: dict[str, dict[str, Any]] = {}
    for concept in _concept_registry():
        for alias in concept["aliases"]:
            key = " ".join(str(alias).strip().lower().split())
            if key:
                index.setdefault(key, concept)
    return index


@lru_cache(maxsize=1)
def _concept_alias_pattern() -> re.Pattern[str] | None:
    """Compile one whole-word/phrase pattern over every registry alias.

    Longer aliases are listed first so a phrase such as "blood glucose" wins
    over the shorter "glucose" alias when both could match the same span.
    """

    aliases = sorted(_concept_alias_index(), key=len, reverse=True)
    if not aliases:
        return None
    return re.compile(r"\b(" + "|".join(re.escape(alias) for alias in aliases) + r")\b", re.I)


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
                code_node = _standard_code_node(entity)
                if code_node is not None:
                    nodes.setdefault(code_node["id"], code_node)
                    edges.append(_edge(entity["id"], "normalizes_to", code_node["id"], ev.evidence_id))
                    triples.append(
                        {
                            "subject": entity["label"],
                            "predicate": "normalizes_to",
                            "object": code_node["label"],
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
    entities.extend(_concept_entities_from_claim(claim))
    return _dedupe_nodes(entities)


def _concept_entities_from_claim(claim: str) -> list[dict[str, Any]]:
    """Recognize clinical concepts via the medical-concept registry and
    attach their canonical standard code (e.g. LOINC) as normalization."""

    pattern = _concept_alias_pattern()
    if pattern is None:
        return []
    index = _concept_alias_index()
    entities: list[dict[str, Any]] = []
    for match in pattern.finditer(claim):
        label = match.group(0)
        concept = index.get(" ".join(label.lower().split()))
        if concept is not None:
            entities.append(_concept_entity(label, concept))
    return entities


def _concept_entity(label: str, concept: dict[str, Any]) -> dict[str, Any]:
    node = _node(f"clinical_concept:{concept['concept_id']}", label, "clinical_concept")
    node["normalized_code"] = f"{concept['standard_system']}:{concept['code']}"
    node["normalized_system"] = concept["standard_system"]
    node["normalized_display"] = concept["display_name"]
    return node


def _standard_code_node(entity: dict[str, Any]) -> dict[str, Any] | None:
    """Build the canonical-code node a normalized entity points to, if any."""

    code = entity.get("normalized_code")
    system = entity.get("normalized_system")
    if not code or not system:
        return None
    node = _node(f"code:{str(code).lower()}", str(code), "standard_code")
    node["standard_system"] = system
    display = entity.get("normalized_display")
    if display:
        node["display_name"] = display
    return node


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
