"""Kùzu-backed persistent knowledge-graph repository.

Implements :class:`ojtflow.application.ports.KnowledgeGraphRepository` against an embedded
Kùzu (``kuzudb``) property graph. ``kuzu`` is imported lazily so the package imports without
the optional ``graph`` extra installed.

.. warning::
   The exact Kùzu DDL/Cypher here is written to the design doc and **must be confirmed
   against the installed ``kuzu`` version** (list-property semantics and ``MERGE`` behaviour
   vary across releases). The :class:`InMemoryKnowledgeGraphRepository` is the unit-tested
   reference for Phase 1; this adapter is validated by the ``graph``-extra integration suite
   (skipped when ``kuzu`` is absent).

Scope handling: Kùzu node tables take a single-column primary key, so the composite
``(scope, organization_id, node_id)`` identity (§4) is encoded into a synthetic ``pk``
column. ``node_id``/``scope``/``organization_id`` remain queryable properties.
"""

from __future__ import annotations

from pathlib import Path
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


def _pk(scope: str, organization_id: str, node_id: str) -> str:
    return f"{scope}{_PK_SEP}{organization_id}{_PK_SEP}{node_id}"


class KuzuKnowledgeGraphRepository:
    """Translates port calls to Kùzu Cypher. Owns one ``Database`` + ``Connection``."""

    def __init__(self, db_path: str | Path) -> None:
        try:
            import kuzu  # noqa: PLC0415 — lazy: optional `graph` extra
        except ImportError as exc:  # pragma: no cover - exercised only without extra
            raise RuntimeError(
                "Kùzu backend requires the 'graph' extra: pip install '.[graph]'"
            ) from exc
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = kuzu.Database(str(db_path))
        self._conn = kuzu.Connection(self._db)

    # -- helpers -----------------------------------------------------------------
    def _rows(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        result = self._conn.execute(query, parameters=params or {})
        columns = result.get_column_names()
        rows: list[dict[str, Any]] = []
        while result.has_next():
            rows.append(dict(zip(columns, result.get_next())))
        return rows

    def bootstrap(self) -> None:
        self._conn.execute(
            """
            CREATE NODE TABLE IF NOT EXISTS Concept(
                pk STRING, node_id STRING, scope STRING, organization_id STRING,
                node_type STRING, label STRING, normalized_code STRING, code_system STRING,
                aliases STRING[], confidence DOUBLE, review_state STRING,
                created_at STRING, updated_at STRING, source_chunk_ids STRING[],
                PRIMARY KEY (pk))
            """
        )
        self._conn.execute(
            """
            CREATE NODE TABLE IF NOT EXISTS Chunk(
                chunk_id STRING, scope STRING, organization_id STRING, document_id STRING,
                source_id STRING, snippet STRING, created_at STRING, PRIMARY KEY (chunk_id))
            """
        )
        self._conn.execute(
            "CREATE REL TABLE IF NOT EXISTS MENTIONS(FROM Chunk TO Concept, confidence DOUBLE)"
        )
        self._conn.execute(
            """
            CREATE REL TABLE IF NOT EXISTS RELATED(
                FROM Concept TO Concept, relation STRING, confidence DOUBLE,
                review_state STRING, created_at STRING, source_chunk_ids STRING[])
            """
        )

    # -- writes ------------------------------------------------------------------
    def upsert_concepts(self, concepts: list[KnowledgeGraphNode]) -> None:
        for c in concepts:
            pk = _pk(c.scope, c.organization_id, c.node_id)
            existing = self._rows(
                "MATCH (c:Concept {pk: $pk}) RETURN c.source_chunk_ids AS ids",
                {"pk": pk},
            )
            merged_ids = _union(
                existing[0]["ids"] if existing else [], c.source_chunk_ids
            )
            self._conn.execute(
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
                {
                    "pk": pk,
                    "node_id": c.node_id,
                    "scope": c.scope,
                    "organization_id": c.organization_id,
                    "node_type": c.node_type,
                    "label": c.label,
                    "normalized_code": c.normalized_code or "",
                    "code_system": c.code_system or "",
                    "aliases": list(c.aliases),
                    "confidence": c.confidence,
                    "review_state": c.review_state,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at or utc_now().isoformat(),
                    "source_chunk_ids": merged_ids,
                },
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
                {"src": r.source_node_id, "tgt": r.target_node_id, "rel": r.relation},
            )
            merged_ids = _union(existing[0]["ids"] if existing else [], incoming)
            self._conn.execute(
                """
                MATCH (s:Concept {node_id: $src}), (t:Concept {node_id: $tgt})
                MERGE (s)-[e:RELATED {relation: $rel}]->(t)
                SET e.confidence = $confidence, e.review_state = $review_state,
                    e.created_at = coalesce(e.created_at, $created_at),
                    e.source_chunk_ids = $source_chunk_ids
                """,
                {
                    "src": r.source_node_id,
                    "tgt": r.target_node_id,
                    "rel": r.relation,
                    "confidence": r.confidence,
                    "review_state": r.review_state,
                    "created_at": r.created_at,
                    "source_chunk_ids": merged_ids,
                },
            )

    def append_provenance(
        self,
        chunk: KnowledgeGraphChunk,
        mentions: list[KnowledgeGraphMention],
    ) -> None:
        self._conn.execute(
            """
            MERGE (ch:Chunk {chunk_id: $chunk_id})
            SET ch.scope = $scope, ch.organization_id = $organization_id,
                ch.document_id = $document_id, ch.source_id = $source_id,
                ch.snippet = $snippet, ch.created_at = $created_at
            """,
            {
                "chunk_id": chunk.chunk_id,
                "scope": chunk.scope,
                "organization_id": chunk.organization_id,
                "document_id": chunk.document_id or "",
                "source_id": chunk.source_id or "",
                "snippet": chunk.snippet,
                "created_at": chunk.created_at,
            },
        )
        for mention in mentions:
            self._conn.execute(
                """
                MATCH (ch:Chunk {chunk_id: $chunk_id}), (c:Concept {node_id: $node_id})
                MERGE (ch)-[m:MENTIONS]->(c)
                SET m.confidence = $confidence,
                    c.source_chunk_ids = list_distinct(
                        list_concat(coalesce(c.source_chunk_ids, []), [$chunk_id]))
                """,
                {
                    "chunk_id": chunk.chunk_id,
                    "node_id": mention.node_id,
                    "confidence": mention.confidence,
                },
            )

    # -- reads -------------------------------------------------------------------
    def get_concept(
        self,
        *,
        node_id: str,
        organization_id: str | None,
    ) -> KnowledgeGraphNode | None:
        rows = self._rows(
            f"""
            MATCH (c:Concept {{node_id: $node_id}})
            WHERE {self._scope_clause('c')}
            RETURN c ORDER BY c.scope DESC LIMIT 1
            """,
            {"node_id": node_id, "org": organization_id or ""},
        )
        return _node_from_row(rows[0]["c"]) if rows else None

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
        # Assembled with explicit bounded follow-up queries (see _collect_edges) rather
        # than a single variable-length path projection, to keep provenance resolution
        # robust across kuzu versions.
        node_map: dict[str, KnowledgeGraphNode] = {}
        for nid in seeds:
            node = self.get_concept(node_id=nid, organization_id=organization_id)
            if node is not None:
                node_map[nid] = node
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
            rows = self._rows(
                f"""
                MATCH (s:Concept)-[e:RELATED]-(t:Concept)
                WHERE s.node_id IN $frontier
                  AND {self._scope_clause('s')} AND {self._scope_clause('t')}
                RETURN s.node_id AS src, t.node_id AS tgt, e.relation AS relation,
                       e.confidence AS confidence, e.review_state AS review_state,
                       e.created_at AS created_at, e.source_chunk_ids AS source_chunk_ids
                """,
                {"frontier": current, "org": org},
            )
            next_nodes: list[str] = []
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
            current = next_nodes
        return list(edges.values())

    def _snippets(self, chunk_ids: list[str]) -> list[str]:
        if not chunk_ids:
            return []
        rows = self._rows(
            "MATCH (ch:Chunk) WHERE ch.chunk_id IN $ids AND ch.snippet <> '' "
            "RETURN ch.snippet AS snippet",
            {"ids": list(chunk_ids)},
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
              AND (lower(c.label) CONTAINS $needle OR lower(c.normalized_code) CONTAINS $needle)
            RETURN c ORDER BY c.label LIMIT {limit}
            """,
            {"needle": q.strip().lower(), "org": organization_id or ""},
        )
        return [_node_from_row(row["c"]) for row in rows]

    def stats(self, *, organization_id: str | None) -> KnowledgeGraphStats:
        org = organization_id or ""
        nodes = self._rows(
            f"MATCH (c:Concept) WHERE {self._scope_clause('c')} "
            "RETURN c.node_type AS t, c.scope AS s",
            {"org": org},
        )
        by_type: dict[str, int] = {}
        by_scope: dict[str, int] = {}
        for row in nodes:
            by_type[row["t"]] = by_type.get(row["t"], 0) + 1
            by_scope[row["s"]] = by_scope.get(row["s"], 0) + 1
        edge_rows = self._rows(
            f"MATCH (s:Concept)-[e:RELATED]->(t:Concept) "
            f"WHERE {self._scope_clause('s')} AND {self._scope_clause('t')} "
            "RETURN count(e) AS c",
            {"org": org},
        )
        chunk_rows = self._rows(
            "MATCH (ch:Chunk) WHERE ch.scope = 'global' OR ch.organization_id = $org "
            "RETURN count(ch) AS c",
            {"org": org},
        )
        return KnowledgeGraphStats(
            node_count=len(nodes),
            edge_count=int(edge_rows[0]["c"]) if edge_rows else 0,
            chunk_count=int(chunk_rows[0]["c"]) if chunk_rows else 0,
            nodes_by_type=by_type,
            nodes_by_scope=by_scope,
            generated_at=utc_now().isoformat(),
        )

    @staticmethod
    def _scope_clause(var: str) -> str:
        return f"({var}.scope = 'global' OR {var}.organization_id = $org)"


def _union(existing: list[str] | None, incoming: list[str]) -> list[str]:
    out = list(existing or [])
    for value in incoming:
        if value and value not in out:
            out.append(value)
    return out


def _node_from_row(row: dict[str, Any]) -> KnowledgeGraphNode:
    return KnowledgeGraphNode(
        node_id=row["node_id"],
        scope=row["scope"],
        organization_id=row.get("organization_id", ""),
        node_type=row["node_type"],
        label=row["label"],
        normalized_code=row.get("normalized_code") or None,
        code_system=row.get("code_system") or None,
        aliases=list(row.get("aliases") or []),
        confidence=row.get("confidence") or 1.0,
        review_state=row.get("review_state") or "accepted",
        created_at=row["created_at"],
        updated_at=row.get("updated_at") or row["created_at"],
        source_chunk_ids=list(row.get("source_chunk_ids") or []),
    )
