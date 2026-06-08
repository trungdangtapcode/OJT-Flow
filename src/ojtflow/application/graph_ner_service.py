"""Deterministic Graph-NER handoff for retrieval packages."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, NamedTuple

from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import RetrievalPackage, RetrievalQuery


# Reuse the same seed registry (and path override) as deterministic query
# normalization in ojtflow.infrastructure.retrieval.query_analysis, so both
# consumers stay aligned with one source of truth for concept-to-code mapping.
DEFAULT_CONCEPT_REGISTRY = (
    Path(__file__).resolve().parents[3] / "knowledge" / "terminologies" / "medical_concepts.json"
)
DEFAULT_GRAPH_NER_RULES = (
    Path(__file__).resolve().parents[3] / "knowledge" / "terminologies" / "graph_ner_rules.json"
)
DEFAULT_FHIR_SEARCH_PARAMETERS = (
    Path(__file__).resolve().parents[3]
    / "knowledge"
    / "terminologies"
    / "fhir_search_parameters.json"
)
CONCEPT_REGISTRY_ENV_VAR = "OJT_MEDICAL_CONCEPT_REGISTRY_PATH"
GRAPH_NER_RULES_ENV_VAR = "OJT_GRAPH_NER_RULES_PATH"
FHIR_SEARCH_PARAMETERS_ENV_VAR = "OJT_FHIR_SEARCH_PARAMETERS_PATH"


class AliasRule(NamedTuple):
    """One normalized alias mapping loaded from trusted Graph-NER rules."""

    entity_id: str
    label: str
    entity_type: str
    alias: str
    confidence: float
    rule_source: str


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


def _concept_registry_path() -> str:
    return os.environ.get(CONCEPT_REGISTRY_ENV_VAR) or str(DEFAULT_CONCEPT_REGISTRY)


def _concept_registry() -> tuple[dict[str, Any], ...]:
    return _load_concept_registry(_concept_registry_path())


@lru_cache(maxsize=4)
def _load_graph_ner_rules(path_text: str) -> tuple[dict[str, Any], ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    rules = raw.get("entity_rules") if isinstance(raw, dict) else None
    if not isinstance(rules, list):
        return ()
    valid: list[dict[str, Any]] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if not {
            "entity_id",
            "label",
            "type",
            "aliases",
        }.issubset(rule):
            continue
        if not isinstance(rule["aliases"], list):
            continue
        valid.append(rule)
    return tuple(valid)


def _graph_ner_rules_path() -> str:
    return os.environ.get(GRAPH_NER_RULES_ENV_VAR) or str(DEFAULT_GRAPH_NER_RULES)


@lru_cache(maxsize=4)
def _rule_alias_index(path_text: str) -> dict[str, AliasRule]:
    index: dict[str, AliasRule] = {}
    for rule in _load_graph_ner_rules(path_text):
        confidence = _coerce_confidence(rule.get("confidence"), default=0.8)
        for alias in rule["aliases"]:
            key = _normalize_alias(str(alias))
            if not key:
                continue
            index.setdefault(
                key,
                AliasRule(
                    entity_id=str(rule["entity_id"]),
                    label=str(rule["label"]),
                    entity_type=str(rule["type"]),
                    alias=key,
                    confidence=confidence,
                    rule_source="graph_ner_rules",
                ),
            )
    return index


@lru_cache(maxsize=4)
def _rule_alias_pattern(path_text: str) -> re.Pattern[str] | None:
    aliases = sorted(_rule_alias_index(path_text), key=len, reverse=True)
    if not aliases:
        return None
    return re.compile(r"\b(" + "|".join(re.escape(alias) for alias in aliases) + r")\b", re.I)


@lru_cache(maxsize=4)
def _load_fhir_search_parameters(path_text: str) -> tuple[dict[str, Any], ...]:
    path = Path(path_text)
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    resources = raw.get("resources") if isinstance(raw, dict) else None
    if not isinstance(resources, list):
        return ()
    valid: list[dict[str, Any]] = []
    for resource in resources:
        if (
            isinstance(resource, dict)
            and isinstance(resource.get("resource_type"), str)
            and isinstance(resource.get("parameters"), list)
        ):
            valid.append(resource)
    return tuple(valid)


def _fhir_search_parameters_path() -> str:
    return os.environ.get(FHIR_SEARCH_PARAMETERS_ENV_VAR) or str(DEFAULT_FHIR_SEARCH_PARAMETERS)


@lru_cache(maxsize=4)
def _concept_alias_index(path_text: str) -> dict[str, dict[str, Any]]:
    """Map normalized alias text to its registry concept entry."""

    index: dict[str, dict[str, Any]] = {}
    for concept in _load_concept_registry(path_text):
        for alias in concept["aliases"]:
            key = _normalize_alias(str(alias))
            if key:
                index.setdefault(key, concept)
    return index


@lru_cache(maxsize=4)
def _concept_alias_pattern(path_text: str) -> re.Pattern[str] | None:
    """Compile one whole-word/phrase pattern over every registry alias.

    Longer aliases are listed first so a phrase such as "blood glucose" wins
    over the shorter "glucose" alias when both could match the same span.
    """

    aliases = sorted(_concept_alias_index(path_text), key=len, reverse=True)
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
            entity = _node(f"field:{field.lower()}", field, "data_field", confidence=0.9)
            _upsert_node(nodes, entity)
            edges.append(_edge(query_node["id"], "mentions_field", entity["id"]))

        for entity in _entities_from_text(query.query):
            _upsert_node(nodes, entity)
            edges.append(_edge(query_node["id"], "mentions_entity", entity["id"]))
            code_node = _standard_code_node(entity)
            if code_node is not None:
                _upsert_node(nodes, code_node)
                edges.append(_edge(entity["id"], "normalizes_to", code_node["id"]))

        if query.resource_type:
            entity = _node(
                f"resource:{query.resource_type.lower()}",
                query.resource_type,
                "fhir_resource",
                confidence=0.95,
            )
            _upsert_node(nodes, entity)
            edges.append(_edge(query_node["id"], "requests_resource", entity["id"]))
            self._attach_fhir_search_parameter_nodes(
                resource_type=query.resource_type,
                nodes=nodes,
                edges=edges,
                parent_node_id=entity["id"],
            )

        for ev in evidence:
            evidence_node = _node(f"evidence:{ev.evidence_id}", ev.source_id, "evidence")
            _upsert_node(nodes, evidence_node)
            claim_entities = _entities_from_text(ev.claim)
            locator = ev.locator or {}
            for locator_key in ("standard_system", "clinical_domain"):
                value = locator.get(locator_key)
                if value:
                    claim_entities.append(
                        {
                            "id": f"{locator_key}:{str(value).lower()}",
                            "label": str(value),
                            "type": locator_key,
                            "confidence": 0.85,
                            "rule_source": "evidence_locator",
                        }
                    )
            for entity in claim_entities:
                _upsert_node(nodes, entity)
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
                    _upsert_node(nodes, code_node)
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
        limited_nodes = list(nodes.values())[: self.max_entities]
        limited_edges = deduped_edges[: self.max_triples]
        limited_triples = triples[: self.max_triples]
        return {
            "graph_contract": "graph_ner_handoff.v0",
            "nodes": limited_nodes,
            "edges": limited_edges,
            "triples": limited_triples,
            "summary": {
                "node_count": len(limited_nodes),
                "edge_count": len(limited_edges),
                "triple_count": len(limited_triples),
                "rule_source_count": len(_load_graph_ner_rules(_graph_ner_rules_path())),
                "concept_registry_count": len(_concept_registry()),
            },
            "limits": {
                "max_entities": self.max_entities,
                "max_triples": self.max_triples,
            },
        }

    def _attach_fhir_search_parameter_nodes(
        self,
        *,
        resource_type: str,
        nodes: dict[str, dict[str, Any]],
        edges: list[dict[str, Any]],
        parent_node_id: str,
    ) -> None:
        resource_key = resource_type.lower()
        for resource in _load_fhir_search_parameters(_fhir_search_parameters_path()):
            if str(resource["resource_type"]).lower() != resource_key:
                continue
            for parameter in resource.get("parameters", []):
                if not isinstance(parameter, dict) or not parameter.get("name"):
                    continue
                parameter_name = str(parameter["name"])
                parameter_node = _node(
                    f"fhir_search_parameter:{resource_key}:{parameter_name.lower()}",
                    parameter_name,
                    "fhir_search_parameter",
                    confidence=0.9,
                )
                parameter_node["target_field"] = parameter.get("target_field")
                parameter_node["search_type"] = parameter.get("type")
                parameter_node["example"] = parameter.get("example")
                parameter_node["rule_source"] = "fhir_search_parameters"
                _upsert_node(nodes, parameter_node)
                edges.append(_edge(parent_node_id, "has_search_parameter", parameter_node["id"]))
                for standard in parameter.get("standard_systems", []):
                    standard_node = _node(
                        f"standard:{str(standard).lower()}",
                        str(standard),
                        "standard",
                        confidence=0.9,
                    )
                    standard_node["rule_source"] = "fhir_search_parameters"
                    _upsert_node(nodes, standard_node)
                    edges.append(_edge(parameter_node["id"], "uses_standard", standard_node["id"]))
            return


def _entities_from_text(text: str) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    entities.extend(_rule_entities_from_text(text))
    entities.extend(_concept_entities_from_text(text))
    return _dedupe_nodes(entities)


def _rule_entities_from_text(text: str) -> list[dict[str, Any]]:
    pattern = _rule_alias_pattern(_graph_ner_rules_path())
    if pattern is None:
        return []
    index = _rule_alias_index(_graph_ner_rules_path())
    entities: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        rule = index.get(_normalize_alias(match.group(0)))
        if rule is not None:
            node = _node(
                rule.entity_id,
                rule.label,
                rule.entity_type,
                confidence=rule.confidence,
            )
            node["matched_text"] = match.group(0)
            node["rule_source"] = rule.rule_source
            entities.append(node)
    return entities


def _concept_entities_from_text(text: str) -> list[dict[str, Any]]:
    """Recognize clinical concepts via the medical-concept registry and
    attach their canonical standard code (e.g. LOINC) as normalization."""

    path_text = _concept_registry_path()
    pattern = _concept_alias_pattern(path_text)
    if pattern is None:
        return []
    index = _concept_alias_index(path_text)
    entities: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        label = match.group(0)
        concept = index.get(_normalize_alias(label))
        if concept is not None:
            entities.append(_concept_entity(label, concept))
    return entities


def _concept_entity(label: str, concept: dict[str, Any]) -> dict[str, Any]:
    node = _node(
        f"clinical_concept:{concept['concept_id']}",
        label,
        "clinical_concept",
        confidence=0.92,
    )
    node["normalized_code"] = f"{concept['standard_system']}:{concept['code']}"
    node["normalized_system"] = concept["standard_system"]
    node["normalized_display"] = concept["display_name"]
    node["clinical_domain"] = concept.get("clinical_domain")
    node["concept_registry_id"] = concept["concept_id"]
    node["rule_source"] = "medical_concepts"
    return node


def _standard_code_node(entity: dict[str, Any]) -> dict[str, Any] | None:
    """Build the canonical-code node a normalized entity points to, if any."""

    code = entity.get("normalized_code")
    system = entity.get("normalized_system")
    if not code or not system:
        return None
    node = _node(f"code:{str(code).lower()}", str(code), "standard_code", confidence=0.92)
    node["standard_system"] = system
    display = entity.get("normalized_display")
    if display:
        node["display_name"] = display
    return node


def _node(
    node_id: str,
    label: str,
    node_type: str,
    *,
    confidence: float | None = None,
) -> dict[str, Any]:
    node = {"id": node_id, "label": label, "type": node_type}
    if confidence is not None:
        node["confidence"] = confidence
    return node


def _upsert_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    existing = nodes.get(node["id"])
    if existing is None:
        nodes[node["id"]] = node
        return
    if _is_better_label(existing, node):
        existing["label"] = node["label"]
        if "matched_text" in node:
            existing["matched_text"] = node["matched_text"]
    if _is_more_specific_rule_source(existing, node):
        existing.update(
            {
                key: value
                for key, value in node.items()
                if key not in {"id", "type"} and value is not None
            }
        )


def _is_better_label(existing: dict[str, Any], node: dict[str, Any]) -> bool:
    if existing.get("type") != node.get("type"):
        return False
    if existing.get("type") != "clinical_concept":
        return False
    return len(str(node.get("label", ""))) > len(str(existing.get("label", "")))


def _is_more_specific_rule_source(existing: dict[str, Any], node: dict[str, Any]) -> bool:
    source_rank = {
        "fhir_search_parameters": 1,
        "evidence_locator": 2,
        "graph_ner_rules": 3,
        "medical_concepts": 4,
    }
    existing_rank = source_rank.get(str(existing.get("rule_source")), 0)
    node_rank = source_rank.get(str(node.get("rule_source")), 0)
    return node_rank > existing_rank


def _normalize_alias(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _coerce_confidence(value: Any, *, default: float) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    return default


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
