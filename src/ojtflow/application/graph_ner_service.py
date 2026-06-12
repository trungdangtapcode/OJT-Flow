"""Deterministic Graph-NER handoff for retrieval packages."""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, NamedTuple

from ojtflow.core.contracts.evidence import Evidence
from ojtflow.core.contracts.retrieval import (
    RetrievalEvidenceSupportMatrix,
    RetrievalEvidenceSupportRow,
    RetrievalHit,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalScoreComponent,
)


# Reuse the same seed registry (and path override) as deterministic query
# normalization in ojtflow.infrastructure.retrieval.query_analysis, so both
# consumers stay aligned with one source of truth for concept-to-code mapping.
DEFAULT_CONCEPT_REGISTRY = (
    Path(__file__).resolve().parents[3] / "knowledge" / "terminologies" / "medical_concepts.json"
)
DEFAULT_GRAPH_NER_RULES = (
    Path(__file__).resolve().parents[3] / "knowledge" / "terminologies" / "graph_ner_rules.json"
)
DEFAULT_GRAPH_RAG_POLICY = (
    Path(__file__).resolve().parents[3]
    / "knowledge"
    / "retrieval"
    / "graph_rag_policy.json"
)
DEFAULT_FHIR_SEARCH_PARAMETERS = (
    Path(__file__).resolve().parents[3]
    / "knowledge"
    / "terminologies"
    / "fhir_search_parameters.json"
)
CONCEPT_REGISTRY_ENV_VAR = "OJT_MEDICAL_CONCEPT_REGISTRY_PATH"
GRAPH_NER_RULES_ENV_VAR = "OJT_GRAPH_NER_RULES_PATH"
GRAPH_RAG_POLICY_ENV_VAR = "OJT_GRAPH_RAG_POLICY_PATH"
FHIR_SEARCH_PARAMETERS_ENV_VAR = "OJT_FHIR_SEARCH_PARAMETERS_PATH"
GRAPH_NER_EXTRACTOR_NAME = "deterministic_graph_ner"
GRAPH_NER_EXTRACTOR_VERSION = "deterministic_graph_ner.v1"


class AliasRule(NamedTuple):
    """One normalized alias mapping loaded from trusted Graph-NER rules."""

    entity_id: str
    label: str
    entity_type: str
    alias: str
    confidence: float
    rule_source: str


@dataclass(frozen=True)
class GraphRAGPolicy:
    """Data-driven policy for GraphRAG-lite evidence scoring."""

    version: str
    enabled: bool
    shared_query_target_weight: float
    evidence_edge_weight: float
    evidence_triple_weight: float
    normalized_code_weight: float
    max_score_boost: float
    promote_weak_to_partial_min_boost: float
    promote_partial_to_strong_min_boost: float
    query_relations: tuple[str, ...]
    evidence_relations: tuple[str, ...]


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
def _load_graph_rag_policy(path_text: str) -> GraphRAGPolicy:
    path = Path(path_text)
    if not path.exists():
        return _fallback_graph_rag_policy()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return _fallback_graph_rag_policy()
    ranking = raw.get("ranking") if isinstance(raw.get("ranking"), dict) else {}
    promotion = (
        raw.get("support_promotion")
        if isinstance(raw.get("support_promotion"), dict)
        else {}
    )
    relations = raw.get("relations") if isinstance(raw.get("relations"), dict) else {}
    return GraphRAGPolicy(
        version=str(raw.get("version") or "graph_rag_policy.v1"),
        enabled=_coerce_bool(raw.get("enabled"), default=True),
        shared_query_target_weight=_coerce_float(
            ranking.get("shared_query_target_weight"),
            default=0.055,
        ),
        evidence_edge_weight=_coerce_float(
            ranking.get("evidence_edge_weight"),
            default=0.012,
        ),
        evidence_triple_weight=_coerce_float(
            ranking.get("evidence_triple_weight"),
            default=0.01,
        ),
        normalized_code_weight=_coerce_float(
            ranking.get("normalized_code_weight"),
            default=0.018,
        ),
        max_score_boost=_coerce_float(ranking.get("max_score_boost"), default=0.12),
        promote_weak_to_partial_min_boost=_coerce_float(
            promotion.get("weak_to_partial_min_boost"),
            default=0.04,
        ),
        promote_partial_to_strong_min_boost=_coerce_float(
            promotion.get("partial_to_strong_min_boost"),
            default=0.07,
        ),
        query_relations=_string_tuple(
            relations.get("query_relations"),
            default=("mentions_entity", "mentions_field", "requests_resource"),
        ),
        evidence_relations=_string_tuple(
            relations.get("evidence_relations"),
            default=("supports",),
        ),
    )


def _graph_rag_policy_path() -> str:
    return os.environ.get(GRAPH_RAG_POLICY_ENV_VAR) or str(DEFAULT_GRAPH_RAG_POLICY)


def _active_graph_rag_policy() -> GraphRAGPolicy:
    return _load_graph_rag_policy(_graph_rag_policy_path())


def _fallback_graph_rag_policy() -> GraphRAGPolicy:
    return GraphRAGPolicy(
        version="graph_rag_policy.fallback",
        enabled=True,
        shared_query_target_weight=0.055,
        evidence_edge_weight=0.012,
        evidence_triple_weight=0.01,
        normalized_code_weight=0.018,
        max_score_boost=0.12,
        promote_weak_to_partial_min_boost=0.04,
        promote_partial_to_strong_min_boost=0.07,
        query_relations=("mentions_entity", "mentions_field", "requests_resource"),
        evidence_relations=("supports",),
    )


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
        policy = _active_graph_rag_policy()
        ranked_package, graph_rag_summary = _apply_graph_rag_ranking(
            package,
            graph_context=graph_context,
            policy=policy,
        )
        handoff_context = {
            **ranked_package.handoff_context,
            "graph_context": graph_context,
            "graph_rag_lite": graph_rag_summary,
        }
        if ranked_package.interpretation is not None:
            handoff_context["interpretation"] = ranked_package.interpretation.model_dump(
                mode="json"
            )
        if ranked_package.support_matrix is not None:
            handoff_context["support_matrix"] = ranked_package.support_matrix.model_dump(
                mode="json"
            )
        trace = ranked_package.trace.model_copy(
            update={
                "fusion_diagnostics": {
                    **ranked_package.trace.fusion_diagnostics,
                    "graph_rag_lite": graph_rag_summary,
                },
                "final_hit_ids": [
                    hit.evidence.evidence_id for hit in ranked_package.hits
                ],
            }
        )
        return ranked_package.model_copy(
            update={
                "handoff_context": handoff_context,
                "trace": trace,
            }
        )

    def build_graph_context(
        self,
        evidence: list[Evidence],
        query: RetrievalQuery,
    ) -> dict[str, Any]:
        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []
        triples: list[dict[str, Any]] = []

        query_node = _node(
            "query:current",
            "Retrieval Query",
            "query",
            provenance=_graph_provenance(source="query", confidence=1.0, review_state="not_required"),
        )
        nodes[query_node["id"]] = query_node

        for field in query.fields:
            entity = _node(
                f"field:{field.lower()}",
                field,
                "data_field",
                confidence=0.9,
                provenance=_graph_provenance(source="query_field", confidence=0.9),
            )
            _upsert_node(nodes, entity)
            edges.append(
                _edge(
                    query_node["id"],
                    "mentions_field",
                    entity["id"],
                    provenance=_graph_provenance(source="query_field", confidence=0.9),
                )
            )

        for entity in _entities_from_text(query.query):
            _attach_node_provenance(entity, source="query_text")
            _upsert_node(nodes, entity)
            edges.append(
                _edge(
                    query_node["id"],
                    "mentions_entity",
                    entity["id"],
                    provenance=_graph_provenance(
                        source="query_text",
                        confidence=_node_confidence(entity),
                        normalized_code_candidates=_normalized_code_candidates(entity),
                    ),
                )
            )
            code_node = _standard_code_node(entity)
            if code_node is not None:
                _attach_node_provenance(code_node, source="query_text")
                _upsert_node(nodes, code_node)
                edges.append(
                    _edge(
                        entity["id"],
                        "normalizes_to",
                        code_node["id"],
                        provenance=_graph_provenance(
                            source="query_text",
                            confidence=_node_confidence(entity),
                            normalized_code_candidates=_normalized_code_candidates(entity),
                            review_state="candidate_requires_review",
                        ),
                    )
                )

        if query.resource_type:
            entity = _node(
                f"resource:{query.resource_type.lower()}",
                query.resource_type,
                "fhir_resource",
                confidence=0.95,
                provenance=_graph_provenance(source="query_resource_type", confidence=0.95),
            )
            _upsert_node(nodes, entity)
            edges.append(
                _edge(
                    query_node["id"],
                    "requests_resource",
                    entity["id"],
                    provenance=_graph_provenance(source="query_resource_type", confidence=0.95),
                )
            )
            self._attach_fhir_search_parameter_nodes(
                resource_type=query.resource_type,
                nodes=nodes,
                edges=edges,
                parent_node_id=entity["id"],
            )

        for ev in evidence:
            evidence_node = _node(
                f"evidence:{ev.evidence_id}",
                ev.source_id,
                "evidence",
                confidence=ev.confidence,
                provenance=_graph_provenance(
                    source="evidence_record",
                    evidence=ev,
                    confidence=ev.confidence,
                    review_state="source_evidence",
                ),
            )
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
                _attach_node_provenance(entity, source="evidence_claim", evidence=ev)
                _upsert_node(nodes, entity)
                edges.append(
                    _edge(
                        evidence_node["id"],
                        "supports",
                        entity["id"],
                        ev.evidence_id,
                        provenance=_graph_provenance(
                            source="evidence_claim",
                            evidence=ev,
                            confidence=_node_confidence(entity),
                            normalized_code_candidates=_normalized_code_candidates(entity),
                        ),
                    )
                )
                triples.append(
                    {
                        "subject": ev.source_id,
                        "predicate": "supports",
                        "object": entity["label"],
                        "evidence_id": ev.evidence_id,
                        "provenance": _graph_provenance(
                            source="evidence_claim",
                            evidence=ev,
                            confidence=_node_confidence(entity),
                            normalized_code_candidates=_normalized_code_candidates(entity),
                        ),
                    }
                )
                code_node = _standard_code_node(entity)
                if code_node is not None:
                    _attach_node_provenance(code_node, source="evidence_claim", evidence=ev)
                    _upsert_node(nodes, code_node)
                    edges.append(
                        _edge(
                            entity["id"],
                            "normalizes_to",
                            code_node["id"],
                            ev.evidence_id,
                            provenance=_graph_provenance(
                                source="evidence_claim",
                                evidence=ev,
                                confidence=_node_confidence(entity),
                                normalized_code_candidates=_normalized_code_candidates(entity),
                                review_state="candidate_requires_review",
                            ),
                        )
                    )
                    triples.append(
                        {
                            "subject": entity["label"],
                            "predicate": "normalizes_to",
                            "object": code_node["label"],
                            "evidence_id": ev.evidence_id,
                            "provenance": _graph_provenance(
                                source="evidence_claim",
                                evidence=ev,
                                confidence=_node_confidence(entity),
                                normalized_code_candidates=_normalized_code_candidates(entity),
                                review_state="candidate_requires_review",
                            ),
                        }
                    )

        deduped_edges = _dedupe_edges(edges)
        limited_nodes = list(nodes.values())[: self.max_entities]
        limited_edges = deduped_edges[: self.max_triples]
        limited_triples = triples[: self.max_triples]
        node_provenance_count = _provenance_count(limited_nodes)
        edge_provenance_count = _provenance_count(limited_edges)
        return {
            "graph_contract": "graph_ner_handoff.v0",
            "nodes": limited_nodes,
            "edges": limited_edges,
            "triples": limited_triples,
            "summary": {
                "extractor": GRAPH_NER_EXTRACTOR_NAME,
                "extractor_version": GRAPH_NER_EXTRACTOR_VERSION,
                "node_count": len(limited_nodes),
                "edge_count": len(limited_edges),
                "triple_count": len(limited_triples),
                "node_provenance_count": node_provenance_count,
                "edge_provenance_count": edge_provenance_count,
                "candidate_review_count": _candidate_review_count(
                    [*limited_nodes, *limited_edges, *limited_triples]
                ),
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
                    provenance=_graph_provenance(
                        source="fhir_search_parameters",
                        confidence=0.9,
                    ),
                )
                parameter_node["target_field"] = parameter.get("target_field")
                parameter_node["search_type"] = parameter.get("type")
                parameter_node["example"] = parameter.get("example")
                parameter_node["rule_source"] = "fhir_search_parameters"
                _upsert_node(nodes, parameter_node)
                edges.append(
                    _edge(
                        parent_node_id,
                        "has_search_parameter",
                        parameter_node["id"],
                        provenance=_graph_provenance(
                            source="fhir_search_parameters",
                            confidence=0.9,
                        ),
                    )
                )
                for standard in parameter.get("standard_systems", []):
                    standard_node = _node(
                        f"standard:{str(standard).lower()}",
                        str(standard),
                        "standard",
                        confidence=0.9,
                        provenance=_graph_provenance(
                            source="fhir_search_parameters",
                            confidence=0.9,
                        ),
                    )
                    standard_node["rule_source"] = "fhir_search_parameters"
                    _upsert_node(nodes, standard_node)
                    edges.append(
                        _edge(
                            parameter_node["id"],
                            "uses_standard",
                            standard_node["id"],
                            provenance=_graph_provenance(
                                source="fhir_search_parameters",
                                confidence=0.9,
                            ),
                        )
                    )
            return


def _apply_graph_rag_ranking(
    package: RetrievalPackage,
    *,
    graph_context: dict[str, Any],
    policy: GraphRAGPolicy,
) -> tuple[RetrievalPackage, dict[str, Any]]:
    support_by_evidence = _graph_support_by_evidence(graph_context, policy=policy)
    if not policy.enabled or not package.hits:
        return package, _graph_rag_summary(
            policy=policy,
            support_by_evidence=support_by_evidence,
            reranked=False,
            original_order=[hit.evidence.evidence_id for hit in package.hits],
            final_order=[hit.evidence.evidence_id for hit in package.hits],
        )

    original_order = [hit.evidence.evidence_id for hit in package.hits]
    adjusted_hits = [
        _apply_graph_support_to_hit(
            hit,
            support=support_by_evidence.get(hit.evidence.evidence_id),
            policy=policy,
        )
        for hit in package.hits
    ]
    adjusted_hits.sort(key=lambda hit: hit.score, reverse=True)
    support_matrix = _apply_graph_support_to_matrix(
        package.support_matrix,
        hits=adjusted_hits,
        support_by_evidence=support_by_evidence,
        policy=policy,
    )
    interpretation = _apply_graph_support_to_interpretation(
        package.interpretation,
        hits=adjusted_hits,
    )
    final_order = [hit.evidence.evidence_id for hit in adjusted_hits]
    summary = _graph_rag_summary(
        policy=policy,
        support_by_evidence=support_by_evidence,
        reranked=final_order != original_order,
        original_order=original_order,
        final_order=final_order,
    )
    return (
        package.model_copy(
            update={
                "hits": adjusted_hits,
                "evidence": [hit.evidence for hit in adjusted_hits],
                "support_matrix": support_matrix,
                "interpretation": interpretation,
            }
        ),
        summary,
    )


def _graph_support_by_evidence(
    graph_context: dict[str, Any],
    *,
    policy: GraphRAGPolicy,
) -> dict[str, dict[str, Any]]:
    query_targets = _query_graph_targets(graph_context, policy=policy)
    support: dict[str, dict[str, Any]] = {}
    for edge in graph_context.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        evidence_id = _edge_evidence_id(edge)
        if not evidence_id:
            continue
        item = support.setdefault(evidence_id, _empty_graph_support(evidence_id))
        relation = str(edge.get("relation") or "")
        target = str(edge.get("target") or "")
        if relation in policy.evidence_relations and target:
            item["evidence_targets"].add(target)
            item["edge_count"] += 1
        if relation == "normalizes_to" and target:
            item["normalized_code_targets"].add(target)
            item["normalized_code_count"] += 1
    for triple in graph_context.get("triples") or []:
        if not isinstance(triple, dict):
            continue
        evidence_id = str(triple.get("evidence_id") or "")
        if not evidence_id:
            continue
        item = support.setdefault(evidence_id, _empty_graph_support(evidence_id))
        item["triple_count"] += 1
        subject = str(triple.get("subject") or "")
        predicate = str(triple.get("predicate") or "")
        obj = str(triple.get("object") or "")
        if subject and predicate and obj:
            item["triple_refs"].append(f"{subject} / {predicate} / {obj}")

    for item in support.values():
        shared = sorted(query_targets.intersection(item["evidence_targets"]))
        raw_score = (
            len(shared) * policy.shared_query_target_weight
            + item["edge_count"] * policy.evidence_edge_weight
            + item["triple_count"] * policy.evidence_triple_weight
            + item["normalized_code_count"] * policy.normalized_code_weight
        )
        item["shared_query_targets"] = shared
        item["score_boost"] = round(min(policy.max_score_boost, raw_score), 6)
        item["evidence_targets"] = sorted(item["evidence_targets"])
        item["normalized_code_targets"] = sorted(item["normalized_code_targets"])
        item["triple_refs"] = item["triple_refs"][:8]
    return support


def _query_graph_targets(
    graph_context: dict[str, Any],
    *,
    policy: GraphRAGPolicy,
) -> set[str]:
    targets: set[str] = set()
    for edge in graph_context.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        if edge.get("source") != "query:current":
            continue
        if str(edge.get("relation") or "") not in policy.query_relations:
            continue
        target = str(edge.get("target") or "")
        if target:
            targets.add(target)
    return targets


def _empty_graph_support(evidence_id: str) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "score_boost": 0.0,
        "shared_query_targets": [],
        "evidence_targets": set(),
        "normalized_code_targets": set(),
        "edge_count": 0,
        "triple_count": 0,
        "normalized_code_count": 0,
        "triple_refs": [],
    }


def _edge_evidence_id(edge: dict[str, Any]) -> str | None:
    evidence_id = edge.get("evidence_id")
    if evidence_id:
        return str(evidence_id)
    source = str(edge.get("source") or "")
    prefix = "evidence:"
    if source.startswith(prefix):
        return source[len(prefix):]
    return None


def _apply_graph_support_to_hit(
    hit: RetrievalHit,
    *,
    support: dict[str, Any] | None,
    policy: GraphRAGPolicy,
) -> RetrievalHit:
    if not support or support.get("score_boost", 0.0) <= 0.0:
        return hit
    score_boost = float(support["score_boost"])
    graph_payload = _serializable_graph_support(support, policy=policy)
    evidence = hit.evidence.model_copy(
        update={
            "confidence": round(min(0.99, (hit.evidence.confidence or 0.0) + score_boost), 4),
            "locator": {
                **hit.evidence.locator,
                "graph_rag_lite": graph_payload,
            },
        }
    )
    source_locator = {
        **hit.source_locator,
        "graph_rag_lite": graph_payload,
    }
    match_explanation = {
        **hit.match_explanation,
        "graph_rag_lite": graph_payload,
        "top_score_driver": f"Graph support +{score_boost:.3f}",
        "support_status": _promoted_support_status(
            str(hit.match_explanation.get("support_status") or ""),
            score_boost=score_boost,
            policy=policy,
        ),
    }
    return hit.model_copy(
        update={
            "evidence": evidence,
            "score": round(hit.score + score_boost, 6),
            "rerank_score": round(hit.rerank_score + score_boost, 6),
            "score_components": [
                *hit.score_components,
                RetrievalScoreComponent(
                    component="graph_support",
                    label="Graph support",
                    value=round(score_boost, 6),
                    description=(
                        "GraphRAG-lite boost from query-to-evidence entity and "
                        "triple support."
                    ),
                    metadata=graph_payload,
                ),
            ],
            "source_locator": source_locator,
            "match_explanation": match_explanation,
        }
    )


def _apply_graph_support_to_interpretation(
    interpretation: Any,
    *,
    hits: list[RetrievalHit],
) -> Any:
    if interpretation is None or not hits:
        return interpretation
    top_hit = hits[0]
    explanation = (
        top_hit.match_explanation
        if isinstance(top_hit.match_explanation, dict)
        else {}
    )
    return interpretation.model_copy(
        update={
            "top_evidence_id": top_hit.evidence.evidence_id,
            "top_source_id": top_hit.evidence.source_id,
            "top_score_driver": _optional_text(explanation.get("top_score_driver")),
            "support_status": _optional_text(explanation.get("support_status")),
            "matched_terms": _string_list(explanation.get("matched_terms"), limit=6),
            "concept_labels": _string_list(explanation.get("concept_labels"), limit=4),
            "aspect_labels": _string_list(explanation.get("aspect_labels"), limit=4),
            "metadata": {
                **interpretation.metadata,
                "graph_rag_lite_top_evidence_id": top_hit.evidence.evidence_id,
            },
        }
    )


def _promoted_support_status(
    current: str,
    *,
    score_boost: float,
    policy: GraphRAGPolicy,
) -> str:
    normalized = current if current in {"strong", "partial", "weak"} else "weak"
    if (
        normalized == "partial"
        and score_boost >= policy.promote_partial_to_strong_min_boost
    ):
        return "strong"
    if normalized == "weak" and score_boost >= policy.promote_weak_to_partial_min_boost:
        return "partial"
    return normalized


def _apply_graph_support_to_matrix(
    matrix: RetrievalEvidenceSupportMatrix | None,
    *,
    hits: list[RetrievalHit],
    support_by_evidence: dict[str, dict[str, Any]],
    policy: GraphRAGPolicy,
) -> RetrievalEvidenceSupportMatrix | None:
    if matrix is None:
        return None
    rank_by_evidence = {
        hit.evidence.evidence_id: rank for rank, hit in enumerate(hits, start=1)
    }
    rows = [
        _apply_graph_support_to_row(
            row,
            support=support_by_evidence.get(row.evidence_id),
            rank=rank_by_evidence.get(row.evidence_id),
            policy=policy,
        )
        for row in matrix.rows
    ]
    rows.sort(key=lambda row: int(row.metadata.get("rank") or 9999))
    status_counts = Counter(row.support_status for row in rows)
    warnings = list(matrix.warnings)
    if any(row.metadata.get("graph_rag_lite") for row in rows):
        warnings.append("graph_rag_lite_support_applied")
    return matrix.model_copy(
        update={
            "row_count": len(rows),
            "strong_count": status_counts.get("strong", 0),
            "partial_count": status_counts.get("partial", 0),
            "weak_count": status_counts.get("weak", 0),
            "unsupported_count": status_counts.get("unsupported", 0),
            "rows": rows,
            "warnings": _unique_strings(warnings),
        }
    )


def _apply_graph_support_to_row(
    row: RetrievalEvidenceSupportRow,
    *,
    support: dict[str, Any] | None,
    rank: int | None,
    policy: GraphRAGPolicy,
) -> RetrievalEvidenceSupportRow:
    metadata = {**row.metadata}
    if rank is not None:
        metadata["rank"] = rank
    if not support or support.get("score_boost", 0.0) <= 0.0:
        return row.model_copy(update={"metadata": metadata})
    graph_payload = _serializable_graph_support(support, policy=policy)
    metadata["graph_rag_lite"] = graph_payload
    promoted_status = _promoted_support_status(
        row.support_status,
        score_boost=float(support["score_boost"]),
        policy=policy,
    )
    reasoning = (
        f"{row.reasoning} GraphRAG-lite linked the evidence to "
        f"{len(graph_payload['shared_query_targets'])} query graph target(s) and "
        f"{graph_payload['triple_count']} evidence triple(s)."
    )
    return row.model_copy(
        update={
            "support_status": promoted_status,
            "score": round(row.score + float(support["score_boost"]), 6),
            "confidence": (
                round(min(1.0, row.confidence + float(support["score_boost"])), 4)
                if row.confidence is not None
                else None
            ),
            "reasoning": reasoning,
            "metadata": metadata,
        }
    )


def _serializable_graph_support(
    support: dict[str, Any],
    *,
    policy: GraphRAGPolicy,
) -> dict[str, Any]:
    return {
        "evidence_id": str(support.get("evidence_id") or ""),
        "policy_version": policy.version,
        "score_boost": round(float(support.get("score_boost") or 0.0), 6),
        "shared_query_targets": list(support.get("shared_query_targets") or []),
        "evidence_targets": list(support.get("evidence_targets") or []),
        "normalized_code_targets": list(support.get("normalized_code_targets") or []),
        "edge_count": int(support.get("edge_count") or 0),
        "triple_count": int(support.get("triple_count") or 0),
        "normalized_code_count": int(support.get("normalized_code_count") or 0),
        "triple_refs": list(support.get("triple_refs") or []),
    }


def _graph_rag_summary(
    *,
    policy: GraphRAGPolicy,
    support_by_evidence: dict[str, dict[str, Any]],
    reranked: bool,
    original_order: list[str],
    final_order: list[str],
) -> dict[str, Any]:
    supported = [
        _serializable_graph_support(item, policy=policy)
        for item in support_by_evidence.values()
        if item.get("score_boost", 0.0) > 0.0
    ]
    supported.sort(
        key=lambda item: (item["score_boost"], item["evidence_id"]),
        reverse=True,
    )
    return {
        "contract": "graph_rag_lite.v0",
        "policy_version": policy.version,
        "enabled": policy.enabled,
        "reranked": reranked,
        "supported_evidence_count": len(supported),
        "original_order": original_order,
        "final_order": final_order,
        "top_supported_evidence": supported[:8],
        "weights": {
            "shared_query_target_weight": policy.shared_query_target_weight,
            "evidence_edge_weight": policy.evidence_edge_weight,
            "evidence_triple_weight": policy.evidence_triple_weight,
            "normalized_code_weight": policy.normalized_code_weight,
            "max_score_boost": policy.max_score_boost,
        },
    }


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
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    node = {"id": node_id, "label": label, "type": node_type}
    if confidence is not None:
        node["confidence"] = confidence
    node["provenance"] = provenance or _graph_provenance(
        source="graph_node",
        confidence=confidence,
    )
    return node


def _attach_node_provenance(
    node: dict[str, Any],
    *,
    source: str,
    evidence: Evidence | None = None,
    review_state: str | None = None,
) -> None:
    node["provenance"] = _graph_provenance(
        source=source,
        evidence=evidence,
        confidence=_node_confidence(node),
        normalized_code_candidates=_normalized_code_candidates(node),
        review_state=review_state,
    )


def _graph_provenance(
    *,
    source: str,
    evidence: Evidence | None = None,
    confidence: float | None = None,
    normalized_code_candidates: list[dict[str, Any]] | None = None,
    review_state: str | None = None,
    source_evidence_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "extractor": GRAPH_NER_EXTRACTOR_NAME,
        "extractor_version": GRAPH_NER_EXTRACTOR_VERSION,
        "source": source,
        "review_state": review_state or "auto_extracted",
    }
    if evidence is not None:
        payload["source_evidence_id"] = evidence.evidence_id
        payload["source_id"] = evidence.source_id
        payload["source_type"] = evidence.source_type.value
        if evidence.source_version:
            payload["source_version"] = evidence.source_version
        source_chunk_id = _source_chunk_id(evidence)
        if source_chunk_id:
            payload["source_chunk_id"] = source_chunk_id
        normalized_locator = evidence.locator.get("normalized_citation_locator")
        if isinstance(normalized_locator, dict):
            payload["normalized_citation_locator"] = normalized_locator
    elif source_evidence_id:
        payload["source_evidence_id"] = source_evidence_id
    if confidence is not None:
        payload["confidence"] = round(max(0.0, min(1.0, float(confidence))), 4)
    if normalized_code_candidates:
        payload["normalized_code_candidates"] = normalized_code_candidates[:5]
    return payload


def _source_chunk_id(evidence: Evidence) -> str | None:
    value = evidence.locator.get("chunk_id")
    if value:
        return str(value)
    normalized_locator = evidence.locator.get("normalized_citation_locator")
    if isinstance(normalized_locator, dict) and normalized_locator.get("identifier"):
        return str(normalized_locator["identifier"])
    return None


def _node_confidence(node: dict[str, Any]) -> float | None:
    value = node.get("confidence")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _normalized_code_candidates(node: dict[str, Any]) -> list[dict[str, Any]]:
    code = _optional_text(node.get("normalized_code"))
    system = _optional_text(node.get("normalized_system") or node.get("standard_system"))
    if not code and node.get("type") == "standard_code":
        code = _optional_text(node.get("label"))
    if not code:
        return []
    candidate: dict[str, Any] = {"code": code}
    if system:
        candidate["system"] = system
    display = _optional_text(node.get("normalized_display") or node.get("display_name"))
    if display:
        candidate["display"] = display
    confidence = _node_confidence(node)
    if confidence is not None:
        candidate["confidence"] = round(max(0.0, min(1.0, confidence)), 4)
    return [candidate]


def _upsert_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    existing = nodes.get(node["id"])
    if existing is None:
        nodes[node["id"]] = node
        return
    _merge_node_provenance(existing, node)
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


def _merge_node_provenance(existing: dict[str, Any], incoming: dict[str, Any]) -> None:
    incoming_provenance = incoming.get("provenance")
    if not isinstance(incoming_provenance, dict):
        return
    existing_provenance = existing.get("provenance")
    if not isinstance(existing_provenance, dict):
        existing["provenance"] = incoming_provenance
        return
    if _same_provenance(existing_provenance, incoming_provenance):
        return
    additional = existing.setdefault("additional_provenance", [])
    if not isinstance(additional, list):
        additional = []
        existing["additional_provenance"] = additional
    if not any(
        isinstance(item, dict) and _same_provenance(item, incoming_provenance)
        for item in additional
    ):
        additional.append(incoming_provenance)
    del additional[5:]


def _same_provenance(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left.get("extractor_version"),
        left.get("source"),
        left.get("source_evidence_id"),
        left.get("source_chunk_id"),
    ) == (
        right.get("extractor_version"),
        right.get("source"),
        right.get("source_evidence_id"),
        right.get("source_chunk_id"),
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


def _coerce_float(value: Any, *, default: float) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, float(value))
    return default


def _coerce_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _string_tuple(value: Any, *, default: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, list):
        return default
    values = tuple(str(item).strip() for item in value if str(item).strip())
    return values or default


def _optional_text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _string_list(value: Any, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return result[:limit]


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        result.append(text)
        seen.add(text)
    return result


def _edge(
    source: str,
    relation: str,
    target: str,
    evidence_id: str | None = None,
    *,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    edge = {"source": source, "relation": relation, "target": target}
    if evidence_id:
        edge["evidence_id"] = evidence_id
    edge["provenance"] = provenance or _graph_provenance(
        source="graph_edge",
        source_evidence_id=evidence_id,
        review_state="auto_extracted",
    )
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


def _provenance_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if isinstance(item.get("provenance"), dict))


def _candidate_review_count(items: list[dict[str, Any]]) -> int:
    return sum(
        1
        for item in items
        if any(
            provenance.get("review_state") == "candidate_requires_review"
            for provenance in _item_provenance_entries(item)
        )
    )


def _item_provenance_entries(item: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    provenance = item.get("provenance")
    if isinstance(provenance, dict):
        entries.append(provenance)
    additional = item.get("additional_provenance")
    if isinstance(additional, list):
        entries.extend(entry for entry in additional if isinstance(entry, dict))
    return entries
