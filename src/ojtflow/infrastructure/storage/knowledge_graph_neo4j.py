"""Neo4j-backed persistent knowledge-graph repository.

Implements :class:`ojtflow.application.ports.KnowledgeGraphRepository` against Neo4j (the
same engine the ``graph-med`` reference project uses). The official ``neo4j`` driver is
imported lazily so the package imports without the optional ``graph`` extra installed.

Scope identity (§4): a Concept's canonical key is ``(scope, organization_id, node_id)``.
Neo4j Community supports single-property uniqueness constraints, so the composite key is
encoded into a synthetic ``pk`` property (``scope|org|node_id``); ``node_id``/``scope``/
``organization_id`` remain queryable properties. Reads return ``global ∪ caller org``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ojtflow.core.contracts.knowledge_graph import (
    KnowledgeGraphChunk,
    KnowledgeGraphEdge,
    KnowledgeGraphMention,
    KnowledgeGraphNode,
    KnowledgeGraphStats,
    KnowledgeGraphView,
)
from ojtflow.core.time import utc_now

_PK_SEP = "\x1f"
_GRAPH_MED_PREFIX = "graph-med"


@dataclass(frozen=True)
class _GraphMedNodeSpec:
    cypher_label: str
    node_type: str
    code_system: str


_GRAPH_MED_NODE_SPECS: tuple[_GraphMedNodeSpec, ...] = (
    _GraphMedNodeSpec("IcdDisease", "icd_disease", "ICD-10"),
    _GraphMedNodeSpec("IcdChapter", "icd_chapter", "ICD-10"),
    _GraphMedNodeSpec("IcdGroup", "icd_group", "ICD-10"),
    _GraphMedNodeSpec("HpoPhenotype", "hpo_phenotype", "HPO"),
    _GraphMedNodeSpec("HpoDisease", "hpo_disease", "HPO"),
    _GraphMedNodeSpec("Umls", "umls", "UMLS"),
)
_GRAPH_MED_LABELS = tuple(spec.cypher_label for spec in _GRAPH_MED_NODE_SPECS)
_GRAPH_MED_NODE_TYPES = {spec.node_type: spec for spec in _GRAPH_MED_NODE_SPECS}


def _pk(scope: str, organization_id: str, node_id: str) -> str:
    return f"{scope}{_PK_SEP}{organization_id}{_PK_SEP}{node_id}"


def _graph_med_node_id(spec: _GraphMedNodeSpec, source_id: str) -> str:
    return f"{_GRAPH_MED_PREFIX}:{spec.node_type}:{source_id}"


def _parse_graph_med_node_id(node_id: str) -> tuple[_GraphMedNodeSpec, str] | None:
    prefix, separator, remainder = node_id.partition(":")
    if prefix != _GRAPH_MED_PREFIX or not separator:
        return None
    node_type, separator, source_id = remainder.partition(":")
    if not separator or not source_id:
        return None
    spec = _GRAPH_MED_NODE_TYPES.get(node_type)
    if spec is None:
        return None
    return spec, source_id


def _graph_med_label_expression(var: str) -> str:
    return (
        f"coalesce(toString({var}.label), toString({var}.chapterName), "
        f"toString({var}.groupName), toString({var}.id), toString({var}.uri), '')"
    )


def _union(existing: list[str] | None, incoming: list[str]) -> list[str]:
    out = list(existing or [])
    for value in incoming:
        if value and value not in out:
            out.append(value)
    return out


class Neo4jKnowledgeGraphRepository:
    """Translates port calls to Cypher against a Neo4j database."""

    def __init__(
        self,
        uri: str,
        *,
        user: str,
        password: str,
        database: str = "neo4j",
    ) -> None:
        try:
            from neo4j import GraphDatabase  # noqa: PLC0415 — lazy: optional `graph` extra
        except ImportError as exc:  # pragma: no cover - exercised only without extra
            raise RuntimeError(
                "Neo4j backend requires the 'graph' extra: pip install '.[graph]'"
            ) from exc
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def close(self) -> None:
        self._driver.close()

    # -- helpers -----------------------------------------------------------------
    def _rows(self, query: str, **params: Any) -> list[dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            return [record.data() for record in session.run(query, **params)]

    def bootstrap(self) -> None:
        self._rows(
            "CREATE CONSTRAINT concept_pk IF NOT EXISTS "
            "FOR (c:Concept) REQUIRE c.pk IS UNIQUE"
        )
        self._rows(
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS "
            "FOR (ch:Chunk) REQUIRE ch.chunk_id IS UNIQUE"
        )

    # -- writes ------------------------------------------------------------------
    def upsert_concepts(self, concepts: list[KnowledgeGraphNode]) -> None:
        for c in concepts:
            pk = _pk(c.scope, c.organization_id, c.node_id)
            existing = self._rows(
                "MATCH (c:Concept {pk: $pk}) RETURN c.source_chunk_ids AS ids", pk=pk
            )
            merged_ids = _union(existing[0]["ids"] if existing else [], c.source_chunk_ids)
            self._rows(
                """
                MERGE (c:Concept {pk: $pk})
                SET c.node_id = $node_id, c.scope = $scope,
                    c.organization_id = $organization_id, c.node_type = $node_type,
                    c.label = $label, c.normalized_code = $normalized_code,
                    c.code_system = $code_system, c.aliases = $aliases,
                    c.confidence = $confidence, c.review_state = $review_state,
                    c.created_at = coalesce(c.created_at, $created_at),
                    c.updated_at = $updated_at, c.source_chunk_ids = $source_chunk_ids
                """,
                pk=pk,
                node_id=c.node_id,
                scope=c.scope,
                organization_id=c.organization_id,
                node_type=c.node_type,
                label=c.label,
                normalized_code=c.normalized_code or "",
                code_system=c.code_system or "",
                aliases=list(c.aliases),
                confidence=c.confidence,
                review_state=c.review_state,
                created_at=c.created_at,
                updated_at=c.updated_at or utc_now().isoformat(),
                source_chunk_ids=merged_ids,
            )

    def upsert_relations(
        self,
        relations: list[KnowledgeGraphEdge],
        *,
        source_chunk_id: str | None = None,
    ) -> None:
        for r in relations:
            incoming = list(r.source_chunk_ids) + ([source_chunk_id] if source_chunk_id else [])
            existing = self._rows(
                """
                MATCH (s:Concept {node_id: $src})-[e:RELATED {relation: $rel}]->
                      (t:Concept {node_id: $tgt})
                RETURN e.source_chunk_ids AS ids
                """,
                src=r.source_node_id,
                tgt=r.target_node_id,
                rel=r.relation,
            )
            merged_ids = _union(existing[0]["ids"] if existing else [], incoming)
            self._rows(
                """
                MATCH (s:Concept {node_id: $src}), (t:Concept {node_id: $tgt})
                MERGE (s)-[e:RELATED {relation: $rel}]->(t)
                SET e.confidence = $confidence, e.review_state = $review_state,
                    e.created_at = coalesce(e.created_at, $created_at),
                    e.source_chunk_ids = $source_chunk_ids
                """,
                src=r.source_node_id,
                tgt=r.target_node_id,
                rel=r.relation,
                confidence=r.confidence,
                review_state=r.review_state,
                created_at=r.created_at,
                source_chunk_ids=merged_ids,
            )

    def append_provenance(
        self,
        chunk: KnowledgeGraphChunk,
        mentions: list[KnowledgeGraphMention],
    ) -> None:
        self._rows(
            """
            MERGE (ch:Chunk {chunk_id: $chunk_id})
            SET ch.scope = $scope, ch.organization_id = $organization_id,
                ch.document_id = $document_id, ch.source_id = $source_id,
                ch.snippet = $snippet, ch.created_at = $created_at
            """,
            chunk_id=chunk.chunk_id,
            scope=chunk.scope,
            organization_id=chunk.organization_id,
            document_id=chunk.document_id or "",
            source_id=chunk.source_id or "",
            snippet=chunk.snippet,
            created_at=chunk.created_at,
        )
        for mention in mentions:
            self._rows(
                """
                MATCH (ch:Chunk {chunk_id: $chunk_id}), (c:Concept {node_id: $node_id})
                MERGE (ch)-[m:MENTIONS]->(c)
                SET m.confidence = $confidence,
                    c.source_chunk_ids =
                        CASE WHEN $chunk_id IN coalesce(c.source_chunk_ids, [])
                             THEN c.source_chunk_ids
                             ELSE coalesce(c.source_chunk_ids, []) + $chunk_id END
                """,
                chunk_id=chunk.chunk_id,
                node_id=mention.node_id,
                confidence=mention.confidence,
            )

    # -- reads -------------------------------------------------------------------
    def get_concept(
        self,
        *,
        node_id: str,
        organization_id: str | None,
    ) -> KnowledgeGraphNode | None:
        graph_med = self._get_graph_med_concept(node_id)
        if graph_med is not None:
            return graph_med
        rows = self._rows(
            f"""
            MATCH (c:Concept {{node_id: $node_id}})
            WHERE {self._scope_clause('c')}
            RETURN c ORDER BY c.scope DESC LIMIT 1
            """,
            node_id=node_id,
            org=organization_id or "",
        )
        return _node_from_props(rows[0]["c"]) if rows else None

    def neighborhood(
        self,
        *,
        seeds: list[str],
        depth: int = 1,
        limit: int = 100,
        organization_id: str | None,
    ) -> KnowledgeGraphView:
        depth = max(0, min(depth, 2))
        limit = max(1, min(limit, 1000))
        org = organization_id or ""
        node_map: dict[str, KnowledgeGraphNode] = {}
        for nid in seeds:
            node = self.get_concept(node_id=nid, organization_id=organization_id)
            if node is not None:
                node_map[node.node_id] = node
        edges = self._collect_edges(list(node_map), org, depth, node_map, limit)
        nodes = list(node_map.values())[:limit]
        node_ids = {n.node_id for n in nodes}
        edges = [e for e in edges if e.source_node_id in node_ids and e.target_node_id in node_ids]
        return KnowledgeGraphView(
            nodes=nodes,
            edges=edges,
            seed_node_ids=[nid for nid in seeds if nid in node_map],
            node_count=len(nodes),
            edge_count=len(edges),
            depth=depth,
            generated_at=utc_now().isoformat(),
        )

    def _collect_edges(
        self,
        frontier: list[str],
        org: str,
        depth: int,
        node_map: dict[str, KnowledgeGraphNode],
        limit: int,
    ) -> list[KnowledgeGraphEdge]:
        edges: dict[tuple[str, str, str], KnowledgeGraphEdge] = {}
        current = list(frontier)
        for _ in range(depth):
            if not current:
                break
            next_nodes: list[str] = []
            rows = self._rows(
                f"""
                MATCH (seed:Concept)-[e:RELATED]-(neighbor:Concept)
                WHERE seed.node_id IN $frontier
                  AND {self._scope_clause('seed')} AND {self._scope_clause('neighbor')}
                WITH startNode(e) AS src, endNode(e) AS tgt, e
                RETURN src.node_id AS src, tgt.node_id AS tgt, e.relation AS relation,
                       e.confidence AS confidence, e.review_state AS review_state,
                       e.created_at AS created_at, e.source_chunk_ids AS source_chunk_ids
                """,
                frontier=current,
                org=org,
            )
            for row in rows:
                key = (row["src"], row["tgt"], row["relation"])
                if key in edges:
                    continue
                edges[key] = KnowledgeGraphEdge(
                    source_node_id=row["src"],
                    target_node_id=row["tgt"],
                    relation=row["relation"],
                    confidence=row.get("confidence") or 1.0,
                    review_state=row.get("review_state") or "accepted",
                    created_at=row.get("created_at") or utc_now().isoformat(),
                    source_chunk_ids=list(row.get("source_chunk_ids") or []),
                    source_snippets=self._snippets(row.get("source_chunk_ids") or []),
                )
                for endpoint in (row["src"], row["tgt"]):
                    if endpoint not in node_map and len(node_map) < limit:
                        node = self.get_concept(node_id=endpoint, organization_id=org or None)
                        if node is not None:
                            node_map[endpoint] = node
                            next_nodes.append(endpoint)
            graph_med_rows = self._graph_med_edge_rows(current, limit=limit)
            for row in graph_med_rows:
                src = _graph_med_row_node_id(row["src_labels"], row["src_id"])
                tgt = _graph_med_row_node_id(row["tgt_labels"], row["tgt_id"])
                if src is None or tgt is None:
                    continue
                relation = str(row["relation"])
                key = (src, tgt, relation)
                if key not in edges:
                    edges[key] = KnowledgeGraphEdge(
                        source_node_id=src,
                        target_node_id=tgt,
                        relation=relation,
                        confidence=1.0,
                        review_state="accepted",
                        created_at=utc_now().isoformat(),
                        source_snippets=_graph_med_edge_snippets(row.get("props") or {}),
                    )
                for endpoint in (src, tgt):
                    if endpoint not in node_map and len(node_map) < limit:
                        node = self.get_concept(node_id=endpoint, organization_id=org or None)
                        if node is not None:
                            node_map[endpoint] = node
                            next_nodes.append(endpoint)
            current = next_nodes
        return list(edges.values())

    def _snippets(self, chunk_ids: list[str]) -> list[str]:
        if not chunk_ids:
            return []
        rows = self._rows(
            "MATCH (ch:Chunk) WHERE ch.chunk_id IN $ids AND ch.snippet <> '' "
            "RETURN ch.snippet AS snippet",
            ids=list(chunk_ids),
        )
        return [row["snippet"] for row in rows]

    def search_concepts(
        self,
        *,
        q: str,
        organization_id: str | None,
        limit: int = 50,
    ) -> list[KnowledgeGraphNode]:
        limit = max(1, min(limit, 1000))
        rows = self._rows(
            f"""
            MATCH (c:Concept)
            WHERE {self._scope_clause('c')}
              AND (toLower(c.label) CONTAINS $needle
                   OR toLower(c.normalized_code) CONTAINS $needle)
            RETURN c ORDER BY c.label LIMIT $limit
            """,
            needle=q.strip().lower(),
            org=organization_id or "",
            limit=limit,
        )
        nodes = [_node_from_props(row["c"]) for row in rows]
        remaining = max(0, limit - len(nodes))
        if remaining:
            nodes.extend(self._search_graph_med_concepts(q=q, limit=remaining))
        nodes.sort(key=lambda node: node.label.lower())
        return nodes[:limit]

    def stats(self, *, organization_id: str | None) -> KnowledgeGraphStats:
        org = organization_id or ""
        nodes = self._rows(
            f"MATCH (c:Concept) WHERE {self._scope_clause('c')} "
            "RETURN c.node_type AS t, c.scope AS s",
            org=org,
        )
        by_type: dict[str, int] = {}
        by_scope: dict[str, int] = {}
        for row in nodes:
            by_type[row["t"]] = by_type.get(row["t"], 0) + 1
            by_scope[row["s"]] = by_scope.get(row["s"], 0) + 1
        graph_med_stats = self._graph_med_stats()
        for node_type, count in graph_med_stats["nodes_by_type"].items():
            by_type[node_type] = by_type.get(node_type, 0) + count
        if graph_med_stats["node_count"]:
            by_scope["global"] = by_scope.get("global", 0) + graph_med_stats["node_count"]
        edge_rows = self._rows(
            f"MATCH (s:Concept)-[e:RELATED]->(t:Concept) "
            f"WHERE {self._scope_clause('s')} AND {self._scope_clause('t')} "
            "RETURN count(e) AS c",
            org=org,
        )
        ojt_edge_count = int(edge_rows[0]["c"]) if edge_rows else 0
        chunk_rows = self._rows(
            "MATCH (ch:Chunk) WHERE ch.scope = 'global' OR ch.organization_id = $org "
            "RETURN count(ch) AS c",
            org=org,
        )
        return KnowledgeGraphStats(
            node_count=len(nodes) + graph_med_stats["node_count"],
            edge_count=ojt_edge_count + graph_med_stats["edge_count"],
            chunk_count=int(chunk_rows[0]["c"]) if chunk_rows else 0,
            nodes_by_type=by_type,
            nodes_by_scope=by_scope,
            generated_at=utc_now().isoformat(),
        )

    def _get_graph_med_concept(self, node_id: str) -> KnowledgeGraphNode | None:
        parsed = _parse_graph_med_node_id(node_id)
        if parsed is None:
            return None
        spec, source_id = parsed
        rows = self._rows(
            f"""
            MATCH (n:{spec.cypher_label})
            WITH labels(n) AS labels, properties(n) AS props
            WITH labels, props, coalesce(toString(props.id), toString(props.uri), '') AS source_id
            WHERE source_id = $id
            RETURN labels, props
            LIMIT 1
            """,
            id=source_id,
        )
        if not rows:
            return None
        return _graph_med_node_from_row(rows[0]["labels"], rows[0]["props"])

    def _search_graph_med_concepts(self, *, q: str, limit: int) -> list[KnowledgeGraphNode]:
        needle = q.strip().lower()
        rows = self._rows(
            f"""
            MATCH (n)
            WHERE any(label IN labels(n) WHERE label IN $graph_med_labels)
            WITH labels(n) AS labels, properties(n) AS props
            WITH labels, props,
                 {_graph_med_label_expression('props')} AS sort_label,
                 coalesce(toString(props.id), toString(props.uri), '') AS source_id
            WHERE
              $needle = ''
              OR toLower(sort_label) CONTAINS $needle
              OR toLower(source_id) CONTAINS $needle
            RETURN labels, props, sort_label
            ORDER BY sort_label
            LIMIT $limit
            """,
            graph_med_labels=list(_GRAPH_MED_LABELS),
            needle=needle,
            limit=limit,
        )
        return [
            node
            for row in rows
            if (node := _graph_med_node_from_row(row["labels"], row["props"])) is not None
        ]

    def _graph_med_edge_rows(
        self,
        frontier: list[str],
        *,
        limit: int,
    ) -> list[dict[str, Any]]:
        source_ids = [
            source_id
            for node_id in frontier
            if (parsed := _parse_graph_med_node_id(node_id)) is not None
            for _spec, source_id in [parsed]
        ]
        if not source_ids:
            return []
        return self._rows(
            """
            MATCH (s)-[e]-(t)
            WHERE any(label IN labels(s) WHERE label IN $graph_med_labels)
              AND any(label IN labels(t) WHERE label IN $graph_med_labels)
            WITH s, t, e, properties(s) AS s_props
            WHERE coalesce(toString(s_props.id), toString(s_props.uri), '') IN $source_ids
            WITH startNode(e) AS src, endNode(e) AS tgt, e
            WHERE any(label IN labels(src) WHERE label IN $graph_med_labels)
              AND any(label IN labels(tgt) WHERE label IN $graph_med_labels)
            WITH src, tgt, e, properties(src) AS src_props, properties(tgt) AS tgt_props
            RETURN labels(src) AS src_labels,
                   coalesce(toString(src_props.id), toString(src_props.uri), '') AS src_id,
                   labels(tgt) AS tgt_labels,
                   coalesce(toString(tgt_props.id), toString(tgt_props.uri), '') AS tgt_id,
                   type(e) AS relation,
                   properties(e) AS props
            LIMIT $limit
            """,
            graph_med_labels=list(_GRAPH_MED_LABELS),
            source_ids=source_ids,
            limit=limit,
        )

    def _graph_med_stats(self) -> dict[str, Any]:
        rows = self._rows(
            """
            MATCH (n)
            UNWIND labels(n) AS label
            WITH label, n
            WHERE label IN $graph_med_labels
            RETURN label, count(DISTINCT n) AS count
            """,
            graph_med_labels=list(_GRAPH_MED_LABELS),
        )
        nodes_by_type: dict[str, int] = {}
        node_count = 0
        for row in rows:
            spec = _graph_med_spec_for_labels([row["label"]])
            if spec is None:
                continue
            count = int(row["count"])
            nodes_by_type[spec.node_type] = nodes_by_type.get(spec.node_type, 0) + count
            node_count += count
        edge_rows = self._rows(
            """
            MATCH (s)-[e]->(t)
            WHERE any(label IN labels(s) WHERE label IN $graph_med_labels)
              AND any(label IN labels(t) WHERE label IN $graph_med_labels)
            RETURN count(e) AS count
            """,
            graph_med_labels=list(_GRAPH_MED_LABELS),
        )
        return {
            "node_count": node_count,
            "edge_count": int(edge_rows[0]["count"]) if edge_rows else 0,
            "nodes_by_type": nodes_by_type,
        }

    @staticmethod
    def _scope_clause(var: str) -> str:
        return f"({var}.scope = 'global' OR {var}.organization_id = $org)"


def _node_from_props(props: dict[str, Any]) -> KnowledgeGraphNode:
    return KnowledgeGraphNode(
        node_id=props["node_id"],
        scope=props["scope"],
        organization_id=props.get("organization_id", ""),
        node_type=props["node_type"],
        label=props["label"],
        normalized_code=props.get("normalized_code") or None,
        code_system=props.get("code_system") or None,
        aliases=list(props.get("aliases") or []),
        confidence=props.get("confidence") or 1.0,
        review_state=props.get("review_state") or "accepted",
        created_at=props["created_at"],
        updated_at=props.get("updated_at") or props["created_at"],
        source_chunk_ids=list(props.get("source_chunk_ids") or []),
    )


def _graph_med_spec_for_labels(labels: list[str]) -> _GraphMedNodeSpec | None:
    label_set = set(labels)
    for spec in _GRAPH_MED_NODE_SPECS:
        if spec.cypher_label in label_set:
            return spec
    return None


def _graph_med_row_node_id(labels: list[str], source_id: str) -> str | None:
    spec = _graph_med_spec_for_labels(labels)
    if spec is None or not source_id:
        return None
    return _graph_med_node_id(spec, source_id)


def _graph_med_node_from_row(
    labels: list[str],
    props: dict[str, Any],
) -> KnowledgeGraphNode | None:
    spec = _graph_med_spec_for_labels(labels)
    source_id = str(props.get("id") or props.get("uri") or "").strip()
    if spec is None or not source_id:
        return None
    label = str(
        props.get("label")
        or props.get("chapterName")
        or props.get("groupName")
        or props.get("id")
        or source_id
    )
    aliases = [
        str(value)
        for value in _as_list(props.get("hasExactSynonym"))
        if str(value).strip()
    ]
    return KnowledgeGraphNode(
        node_id=_graph_med_node_id(spec, source_id),
        scope="global",
        organization_id="",
        node_type=spec.node_type,
        label=label,
        normalized_code=source_id,
        code_system=spec.code_system,
        aliases=aliases,
        confidence=1.0,
        review_state="accepted",
        created_at=str(props.get("created_at") or props.get("createdAt") or utc_now().isoformat()),
        updated_at=str(props.get("updated_at") or props.get("updatedAt") or utc_now().isoformat()),
    )


def _graph_med_edge_snippets(props: dict[str, Any]) -> list[str]:
    parts = []
    for key in ("source", "evidence", "onset", "frequency", "sex", "modifier", "url"):
        value = props.get(key)
        if value:
            parts.append(f"{key}: {value}")
    return ["; ".join(parts)] if parts else []


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
