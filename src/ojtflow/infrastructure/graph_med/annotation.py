"""Direct graph-med patient annotation adapter.

This mirrors graph-med's patient annotation flow without importing its package at runtime:

1. Read ICD chapters from the graph-med Neo4j ontology.
2. Run LLM patient NER with the graph-med prompt shape using the app LLM provider by default.
3. Embed each mention through the app embedding provider by default.
4. Query the ``icd_disease_embedding`` vector index for ICD candidates.
5. Run LLM NED to select or abstain from an ICD code.

No local deterministic NER fallback is used here. Missing graph-med ontology, vector index,
required GPU runtime, or annotation providers are treated as dependency failures.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from ojtflow.core.contracts.knowledge_graph import (
    GraphMedLinkedEntity,
    GraphMedPatientEntity,
    GraphMedStatus,
)
from ojtflow.core.errors import DependencyUnavailableError

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

_PATIENT_NER_SYSTEM = """
You are an expert clinical NER annotator.

GOAL:
Extract ALL disorder/problem mentions (diagnoses, disorders, and symptoms/signs) from BOTH the
concatenated encounter summary and the clinical narrative.

SOURCES:
- CONCAT_TEXT: concatenation of Encounter.reasonCode + ChiefComplaint + Condition.
- NARRATIVE_TEXT: the encounter narrative.

ALLOWED LABELS:
Exactly the strings given in ICD_CHAPTERS.

OUTPUT FORMAT (STRICT JSON):
{
  "patient_id": "str",
  "encounter_id": "str",
  "entities": [
    {
      "source": "concat" | "narrative",
      "start": 0,
      "end": 0,
      "text": "str",
      "label": "ICD Chapter EXACTLY as given in ICD_CHAPTERS",
      "assertion": "present" | "negated" | "uncertain",
      "temporality": "acute" | "chronic" | "recurrent" | "history" | "unspecified",
      "rationale": "str"
    }
  ]
}

Rules:
- Return all valid entities from both sources.
- Use verbatim contiguous spans with 0-based [start, end) indices.
- Split coordinated mentions into separate spans.
- Detect negated and uncertain mentions.
- Skip medications, tests, vitals, and procedures.
- Return JSON only.
""".strip()

_PATIENT_NED_SYSTEM = """
You are an expert clinical entity linker for ICD codes.

Given a single extracted mention, ranked ICD candidate codes, and other mentions from the same
note, choose the single best ICD code or abstain.

OUTPUT:
Return STRICT JSON preserving all original mention fields and appending:
- "icd_id": string | null
- "icd_label": string | null
- "confidence": number from 0 to 1
- "linking_rationale": string

Rules:
- Match meaning, not just wording.
- Respect assertion: for negated mentions, abstain by default.
- Do not invent codes outside the candidate list.
- Prefer the most specific candidate that fits the exact span and context.
- If no candidate fits, return icd_id=null and explain briefly.
- Return JSON only.
""".strip()


@dataclass(frozen=True)
class GraphMedAnnotationConfig:
    enabled: bool
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str
    embedding_base_url: str
    llm_base_url: str
    llm_model: str
    embedding_model: str = ""
    embedding_api_key: str = ""
    embedding_dimensions: int | None = None
    embedding_fallback_base_url: str = ""
    embedding_fallback_model: str = ""
    embedding_fallback_api_key: str = ""
    embedding_fallback_dimensions: int | None = None
    llm_api_key: str = ""
    llm_fallback_base_url: str = ""
    llm_fallback_model: str = ""
    llm_fallback_api_key: str = ""
    gnn_base_url: str = ""
    device: str = "cuda"
    require_gpu: bool = False
    icd_vector_index: str = "icd_disease_embedding"
    candidate_k: int = 10
    timeout_seconds: float = 90.0


class GraphMedAnnotationClient:
    """Run graph-med patient NER/NED against annotation providers and Neo4j ontology."""

    def __init__(self, config: GraphMedAnnotationConfig) -> None:
        self._config = config
        self._driver: Any | None = None
        self._graph_med_llm: Any | None = None
        self._patient_ner_chain: Any | None = None
        self._patient_ned_chain: Any | None = None

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def status(self) -> GraphMedStatus:
        if not self._config.enabled:
            return self._status(
                available=False,
                ontology_loaded=False,
                counts={},
                message="graph-med annotation is disabled.",
            )
        counts: dict[str, int] = {}
        try:
            rows = self._rows(
                """
                MATCH (n)
                UNWIND labels(n) AS label
                WITH label, n
                WHERE label IN ['IcdDisease', 'HpoPhenotype', 'Umls']
                RETURN label, count(DISTINCT n) AS count
                """
            )
            counts = {str(row["label"]): int(row["count"]) for row in rows}
            index_ready = self._vector_index_exists()
            embedding_reachable = any(
                self._endpoint_reachable(
                    target["base_url"],
                    paths=("/healthz", "/health", "/models", "/v1/models"),
                    api_key=target["api_key"],
                )
                for target in self._embedding_targets()
            )
            llm_reachable = any(
                self._endpoint_reachable(
                    target["base_url"],
                    paths=("/models", "/health"),
                    strip_v1_for_health=True,
                    api_key=target["api_key"],
                )
                for target in self._llm_targets()
            )
            gnn_reachable = self._gnn_endpoint_reachable()
            gpu_available = self._gpu_available()
        except Exception as exc:
            return self._status(
                available=False,
                ontology_loaded=False,
                counts=counts,
                gpu_available=False,
                gnn_endpoint_reachable=False,
                embedding_endpoint_reachable=False,
                llm_endpoint_reachable=False,
                message=f"graph-med Neo4j unavailable: {exc}",
            )

        ontology_loaded = bool(counts.get("IcdDisease", 0))
        endpoints = self._endpoints_configured
        endpoints_reachable = embedding_reachable and llm_reachable
        gpu_ready = not self._config.require_gpu or gpu_available
        available = (
            ontology_loaded
            and index_ready
            and endpoints
            and endpoints_reachable
            and gpu_ready
        )
        if available:
            message = "graph-med ontology, vector index, and annotation providers are reachable."
        elif not ontology_loaded:
            message = "graph-med ontology is not loaded in Neo4j."
        elif not index_ready:
            message = (
                f"graph-med ICD vector index '{self._config.icd_vector_index}' is missing."
            )
        elif not endpoints:
            message = "graph-med annotation providers are not configured."
        else:
            if self._config.require_gpu and not gpu_available:
                message = "graph-med GPU runtime is required but CUDA is not available."
            else:
                message = "graph-med annotation providers are configured but not reachable."
        return self._status(
            available=available,
            ontology_loaded=ontology_loaded,
            counts=counts,
            gpu_available=gpu_available,
            gnn_endpoint_reachable=gnn_reachable,
            embedding_endpoint_reachable=embedding_reachable,
            llm_endpoint_reachable=llm_reachable,
            message=message,
        )

    def annotate_text(
        self,
        *,
        patient_id: str,
        encounter_id: str,
        concat_text: str,
        narrative_text: str,
    ) -> list[GraphMedLinkedEntity]:
        status = self.status()
        if not status.available:
            raise DependencyUnavailableError(
                status.message,
                details={"graph_med_status": status.model_dump()},
            )

        chapters = self._icd_chapters()
        ner_payload = {
            "icd_chapters": chapters,
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "concat_text": concat_text,
            "narrative_text": narrative_text,
        }
        ner_response = self._graph_med_ner(ner_payload)
        entities = [GraphMedPatientEntity.model_validate(entity.model_dump()) for entity in ner_response.entities]

        linked: list[GraphMedLinkedEntity] = []
        for index, entity in enumerate(entities):
            candidates = self._select_candidates(entity.text)
            ned_response = self._graph_med_ned(
                mention=ner_response.entities[index],
                candidates=candidates,
                other_mentions=[
                    {"text": other.text, "label": other.label}
                    for other in entities
                    if other is not entity
                ],
            )
            linked.append(GraphMedLinkedEntity.model_validate(ned_response.model_dump()))
        return linked

    @property
    def _endpoints_configured(self) -> bool:
        return bool(self._embedding_targets() and self._llm_targets())

    def _status(
        self,
        *,
        available: bool,
        ontology_loaded: bool,
        counts: dict[str, int],
        gpu_available: bool = False,
        gnn_endpoint_reachable: bool = False,
        embedding_endpoint_reachable: bool = False,
        llm_endpoint_reachable: bool = False,
        message: str,
    ) -> GraphMedStatus:
        return GraphMedStatus(
            enabled=self._config.enabled,
            available=available,
            ontology_loaded=ontology_loaded,
            gpu_required=self._config.require_gpu,
            gpu_available=gpu_available,
            gnn_endpoint_configured=bool(self._config.gnn_base_url),
            gnn_endpoint_reachable=gnn_endpoint_reachable,
            embedding_endpoint_configured=bool(self._embedding_targets()),
            llm_endpoint_configured=bool(self._llm_targets()),
            embedding_endpoint_reachable=embedding_endpoint_reachable,
            llm_endpoint_reachable=llm_endpoint_reachable,
            icd_vector_index=self._config.icd_vector_index,
            icd_disease_count=counts.get("IcdDisease", 0),
            hpo_phenotype_count=counts.get("HpoPhenotype", 0),
            umls_count=counts.get("Umls", 0),
            message=message,
        )

    def _driver_or_create(self) -> Any:
        if self._driver is None:
            try:
                from neo4j import GraphDatabase  # noqa: PLC0415
            except ImportError as exc:  # pragma: no cover
                raise DependencyUnavailableError(
                    "Neo4j driver is unavailable; install the graph extra."
                ) from exc
            self._driver = GraphDatabase.driver(
                self._config.neo4j_uri,
                auth=(self._config.neo4j_user, self._config.neo4j_password),
            )
        return self._driver

    def _rows(self, query: str, **params: Any) -> list[dict[str, Any]]:
        with self._driver_or_create().session(database=self._config.neo4j_database) as session:
            return [record.data() for record in session.run(query, **params)]

    def _vector_index_exists(self) -> bool:
        rows = self._rows(
            """
            SHOW INDEXES
            YIELD name, type, entityType, labelsOrTypes, properties
            WHERE name = $name AND type = 'VECTOR'
            RETURN count(*) AS count
            """,
            name=self._config.icd_vector_index,
        )
        return bool(rows and int(rows[0]["count"]) > 0)

    def _icd_chapters(self) -> list[str]:
        rows = self._rows(
            """
            MATCH (c:IcdChapter)
            RETURN c.chapterName AS chapterName
            ORDER BY c.chapterName ASC
            """
        )
        chapters = [str(row["chapterName"]) for row in rows if row.get("chapterName")]
        if not chapters:
            raise DependencyUnavailableError("graph-med ICD chapters are not loaded.")
        return chapters

    def _select_candidates(self, text: str) -> list[dict[str, Any]]:
        embedding = self._embed(text)
        try:
            rows = self._rows(
                """
                CALL db.index.vector.queryNodes($index, $k, $qe) YIELD node, score
                RETURN node.id AS id, node.label AS label, score
                ORDER BY score DESC
                LIMIT $k
                """,
                index=self._config.icd_vector_index,
                k=self._config.candidate_k,
                qe=embedding,
            )
        except Exception as exc:
            raise DependencyUnavailableError(
                f"graph-med ICD vector lookup failed: {exc}"
            ) from exc
        return [
            {"id": row["id"], "label": row["label"], "score": float(row["score"])}
            for row in rows
            if row.get("id") and row.get("label")
        ]

    def _embed(self, text: str) -> list[float]:
        targets = self._embedding_targets()
        if not targets:
            raise DependencyUnavailableError("graph-med embedding endpoint is not configured.")
        errors: list[str] = []
        for target in targets:
            for url in _embedding_urls(target["base_url"]):
                try:
                    payload: dict[str, Any] = {"input": [text]}
                    if url.rstrip("/").endswith("/v1/embeddings"):
                        if target["model"]:
                            payload["model"] = target["model"]
                        if target["dimensions"]:
                            payload["dimensions"] = target["dimensions"]
                    response = httpx.post(
                        url,
                        json=payload,
                        headers=_auth_headers(target["api_key"]),
                        timeout=self._config.timeout_seconds,
                    )
                    response.raise_for_status()
                    vector = _extract_embedding_vector(response.json())
                    if vector:
                        return vector
                    errors.append(f"{url}: no vector")
                except Exception as exc:
                    errors.append(f"{url}: {exc}")
        raise DependencyUnavailableError(
            "graph-med embedding endpoint failed: " + "; ".join(errors)
        )

    def _llm_json(self, *, system: str, user: str) -> dict[str, Any]:
        targets = self._llm_targets()
        if not targets:
            raise DependencyUnavailableError("graph-med LLM endpoint is not configured.")

        errors: list[str] = []
        for target in targets:
            url = f"{target['base_url'].rstrip('/')}/chat/completions"
            try:
                response = httpx.post(
                    url,
                    json=_chat_completion_payload(target, system=system, user=user),
                    headers=_auth_headers(target["api_key"]),
                    timeout=self._config.timeout_seconds,
                )
                response.raise_for_status()
                body = response.json()
                content = body["choices"][0]["message"]["content"]
                break
            except Exception as exc:
                errors.append(f"{url}: {exc}")
        else:
            raise DependencyUnavailableError(
                "graph-med LLM endpoint failed: " + "; ".join(errors)
            )
        try:
            return json.loads(_clean_json_text(str(content)))
        except json.JSONDecodeError as exc:
            raise DependencyUnavailableError(
                "graph-med LLM endpoint returned non-JSON annotation output."
            ) from exc

    def _endpoint_reachable(
        self,
        base_url: str,
        *,
        paths: tuple[str, ...],
        strip_v1_for_health: bool = False,
        api_key: str = "",
    ) -> bool:
        if not base_url:
            return False
        base = base_url.rstrip("/")
        roots = [base]
        if strip_v1_for_health and base.endswith("/v1"):
            roots.append(base[: -len("/v1")])
        for root in roots:
            for path in paths:
                if path == "/health" and root.endswith("/v1"):
                    continue
                reachable_path = path
                if root.endswith("/v1") and path.startswith("/v1/"):
                    reachable_path = path[len("/v1") :]
                try:
                    response = httpx.get(
                        f"{root}{reachable_path}",
                        headers=_auth_headers(api_key),
                        timeout=min(self._config.timeout_seconds, 3.0),
                    )
                except Exception:
                    continue
                if 200 <= response.status_code < 300:
                    return True
        return False

    def _embedding_targets(self) -> list[dict[str, Any]]:
        targets: list[dict[str, Any]] = []
        if self._config.embedding_base_url:
            targets.append(
                {
                    "base_url": self._config.embedding_base_url,
                    "model": self._config.embedding_model,
                    "api_key": self._config.embedding_api_key,
                    "dimensions": self._config.embedding_dimensions,
                }
            )
        if self._config.embedding_fallback_base_url:
            fallback = {
                "base_url": self._config.embedding_fallback_base_url,
                "model": self._config.embedding_fallback_model,
                "api_key": self._config.embedding_fallback_api_key,
                "dimensions": self._config.embedding_fallback_dimensions,
            }
            if not any(
                target["base_url"].rstrip("/") == fallback["base_url"].rstrip("/")
                and target["model"] == fallback["model"]
                and target["dimensions"] == fallback["dimensions"]
                for target in targets
            ):
                targets.append(fallback)
        return targets

    def _llm_targets(self) -> list[dict[str, str]]:
        targets: list[dict[str, str]] = []
        if self._config.llm_base_url and self._config.llm_model:
            targets.append(
                {
                    "base_url": self._config.llm_base_url,
                    "model": self._config.llm_model,
                    "api_key": self._config.llm_api_key,
                }
            )
        if self._config.llm_fallback_base_url and self._config.llm_fallback_model:
            fallback = {
                "base_url": self._config.llm_fallback_base_url,
                "model": self._config.llm_fallback_model,
                "api_key": self._config.llm_fallback_api_key,
            }
            if not any(
                target["base_url"].rstrip("/") == fallback["base_url"].rstrip("/")
                and target["model"] == fallback["model"]
                for target in targets
            ):
                targets.append(fallback)
        return targets

    def _graph_med_ner(self, payload: dict[str, Any]) -> Any:
        try:
            from ojtflow.infrastructure.graph_med.vendor.llm.pydantic_model import (  # noqa: PLC0415
                PatientNERInput,
                PatientNERResponse,
            )
        except ImportError as exc:
            raise DependencyUnavailableError(
                "graph-med vendored NER dependencies are unavailable; install the graph-med-service extra."
            ) from exc

        chain = self._graph_med_patient_ner_chain()
        input_data = PatientNERInput.model_validate(payload)
        result = chain.invoke(input_data.model_dump())
        return PatientNERResponse.model_validate(
            result.model_dump() if hasattr(result, "model_dump") else result
        )

    def _graph_med_ned(
        self,
        *,
        mention: Any,
        candidates: list[dict[str, Any]],
        other_mentions: list[dict[str, str]],
    ) -> Any:
        try:
            from ojtflow.infrastructure.graph_med.vendor.llm.pydantic_model import (  # noqa: PLC0415
                PatientNEDCandidate,
                PatientNEDInput,
                PatientNEDOtherMention,
                PatientNEDResponse,
            )
        except ImportError as exc:
            raise DependencyUnavailableError(
                "graph-med vendored NED dependencies are unavailable; install the graph-med-service extra."
            ) from exc

        input_data = PatientNEDInput(
            mention=mention,
            candidates=[PatientNEDCandidate.model_validate(candidate) for candidate in candidates],
            other_mentions=[
                PatientNEDOtherMention.model_validate(other) for other in other_mentions
            ],
        )
        result = self._graph_med_patient_ned_chain().invoke(input_data.model_dump())
        return PatientNEDResponse.model_validate(
            result.model_dump() if hasattr(result, "model_dump") else result
        )

    def _graph_med_patient_ner_chain(self) -> Any:
        if self._patient_ner_chain is None:
            try:
                from ojtflow.infrastructure.graph_med.vendor.llm.chain import (  # noqa: PLC0415
                    patient_ner_chain,
                )
            except ImportError as exc:
                raise DependencyUnavailableError(
                    "graph-med vendored NER chain is unavailable; install the graph-med-service extra."
                ) from exc
            self._patient_ner_chain = patient_ner_chain(self._graph_med_chat_model())
        return self._patient_ner_chain

    def _graph_med_patient_ned_chain(self) -> Any:
        if self._patient_ned_chain is None:
            try:
                from ojtflow.infrastructure.graph_med.vendor.llm.chain import (  # noqa: PLC0415
                    patient_ned_chain,
                )
            except ImportError as exc:
                raise DependencyUnavailableError(
                    "graph-med vendored NED chain is unavailable; install the graph-med-service extra."
                ) from exc
            self._patient_ned_chain = patient_ned_chain(self._graph_med_chat_model())
        return self._patient_ned_chain

    def _graph_med_chat_model(self) -> Any:
        if self._graph_med_llm is not None:
            return self._graph_med_llm
        targets = self._llm_targets()
        if not targets:
            raise DependencyUnavailableError("graph-med LLM provider is not configured.")
        target = targets[0]
        try:
            from langchain_openai import ChatOpenAI  # noqa: PLC0415
        except ImportError as exc:
            raise DependencyUnavailableError(
                "graph-med LangChain OpenAI dependency is unavailable; install the graph-med-service extra."
            ) from exc
        kwargs: dict[str, Any] = {
            "api_key": target["api_key"] or "EMPTY",
            "base_url": target["base_url"].rstrip("/"),
            "model": target["model"],
            "timeout": self._config.timeout_seconds,
        }
        if not target["model"].startswith("gpt-5"):
            kwargs["temperature"] = 0
        self._graph_med_llm = ChatOpenAI(**kwargs)
        return self._graph_med_llm

    def _gnn_endpoint_reachable(self) -> bool:
        if not self._config.gnn_base_url:
            return False
        return self._endpoint_reachable(
            self._config.gnn_base_url,
            paths=("/healthz", "/health"),
        )

    def _gpu_available(self) -> bool:
        if self._config.device.strip().lower() == "cpu":
            return False
        if Path("/dev/nvidiactl").exists() or any(Path("/dev").glob("nvidia[0-9]*")):
            return True
        try:
            import torch  # noqa: PLC0415
        except ImportError:
            return False
        return bool(torch.cuda.is_available())


def _render_patient_ner_user(payload: dict[str, Any]) -> str:
    return (
        "ICD_CHAPTERS:\n"
        f"{json.dumps(payload['icd_chapters'], ensure_ascii=False)}\n\n"
        f"patient_id: {payload['patient_id']}\n"
        f"encounter_id: {payload['encounter_id']}\n\n"
        "CONCAT_TEXT:\n"
        f"{payload['concat_text']}\n\n"
        "NARRATIVE_TEXT:\n"
        f"{payload['narrative_text']}"
    )


def _render_patient_ned_user(
    *,
    mention: GraphMedPatientEntity,
    candidates: list[dict[str, Any]],
    other_mentions: list[dict[str, str]],
) -> str:
    return (
        "MENTION:\n"
        f"{mention.model_dump_json()}\n\n"
        "CANDIDATES:\n"
        f"{json.dumps(candidates, ensure_ascii=False)}\n\n"
        "OTHER_MENTIONS:\n"
        f"{json.dumps(other_mentions, ensure_ascii=False)}"
    )


def _clean_json_text(value: str) -> str:
    cleaned = _JSON_FENCE_RE.sub("", value.strip()).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= start:
        return cleaned[start : end + 1]
    return cleaned


def _extract_embedding_vector(body: Any) -> list[float]:
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            vector = first.get("embedding") or first.get("data")
        else:
            vector = first
        if isinstance(vector, list):
            return [float(value) for value in vector]
    if isinstance(body, list) and body and isinstance(body[0], dict):
        nested = body[0].get("data")
        if isinstance(nested, list) and nested:
            return [float(value) for value in nested[0]]
    return []


def _embedding_urls(base_url: str) -> tuple[str, ...]:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return (f"{base}/embeddings", f"{base[:-len('/v1')]}/embed")
    return (f"{base}/embed", f"{base}/v1/embeddings")


def _auth_headers(api_key: str) -> dict[str, str]:
    if not api_key:
        return {}
    return {"Authorization": f"Bearer {api_key}"}


def _chat_completion_payload(
    target: dict[str, str],
    *,
    system: str,
    user: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": target["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    if target["model"].startswith("gpt-5"):
        payload["max_completion_tokens"] = 4096
    else:
        payload["temperature"] = 0
        payload["max_tokens"] = 4096
    return payload
