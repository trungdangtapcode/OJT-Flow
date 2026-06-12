"""External medical-search transparency records for retrieval packages."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ojtflow.core.contracts.analytics import ExternalSourceConnector
from ojtflow.core.contracts.retrieval import (
    RetrievalExternalQueryTransparency,
    RetrievalQuery,
    RetrievalQueryAnalysis,
    RetrievalRouteBudget,
    RetrievalSearchHint,
)
from ojtflow.data_tools.hashing import sha256_text
from ojtflow.interoperability.analytics import (
    build_external_api_cache_metadata,
    load_external_api_cache_policy,
    load_external_source_connectors,
)

EXTERNAL_TRANSPARENCY_SOURCE_RELEASE_VERSION = "external_query_preview:not_fetched"
EXTERNAL_MEDICAL_TARGET_CONNECTORS = {
    "pubmed": "pubmed",
    "clinicaltrials_gov": "clinicaltrials_gov",
    "openfda_drug_label": "openfda",
    "openfda_drug_event": "openfda",
}


def build_external_query_transparency_records(
    *,
    query: RetrievalQuery,
    query_analysis: RetrievalQueryAnalysis,
    route_budget: RetrievalRouteBudget | None,
    knowledge_root: Path | str | None,
) -> list[RetrievalExternalQueryTransparency]:
    """Build auditable records for external-search hints without executing them."""

    if not query_analysis.search_hints:
        return []

    root = Path(knowledge_root) if knowledge_root is not None else _default_knowledge_root()
    try:
        connector_catalog = load_external_source_connectors(root)
        cache_policy = load_external_api_cache_policy(root)
    except FileNotFoundError:
        return []
    connectors = {
        connector.connector_id: connector
        for connector in connector_catalog.connectors
    }
    hint_by_target = {hint.target: hint for hint in query_analysis.search_hints}
    external_network_allowed = (
        bool(route_budget.external_network_allowed) if route_budget is not None else False
    )

    records: list[RetrievalExternalQueryTransparency] = []
    seen: set[tuple[str, str, str]] = set()
    for task in query_analysis.retrieval_tasks:
        if task.target != "external_medical_index":
            continue
        target = task.search_hint_target or str(task.metadata.get("target") or "")
        connector_id = EXTERNAL_MEDICAL_TARGET_CONNECTORS.get(target)
        if connector_id is None:
            continue
        connector = connectors.get(connector_id)
        if connector is None:
            continue
        hint = hint_by_target.get(target)
        exact_query = _exact_query(task.query, hint)
        dedupe_key = (connector_id, target, exact_query)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        endpoint_url = _endpoint_url(exact_query, hint, connector)
        cache_metadata = build_external_api_cache_metadata(
            policy=cache_policy,
            connector_id=connector.connector_id,
            endpoint_url=endpoint_url or connector.source_url,
            query=exact_query,
            source_release_version=EXTERNAL_TRANSPARENCY_SOURCE_RELEASE_VERSION,
            metadata={
                "retrieval_query_hash": sha256_text(query.query),
                "search_hint_target": target,
                "task_id": task.task_id,
                "execution_status": _execution_status(external_network_allowed),
                "cache_state": "not_executed",
            },
        )
        records.append(
            RetrievalExternalQueryTransparency(
                record_id=_record_id(connector_id, target, exact_query),
                connector_id=connector.connector_id,
                target=target,
                display_name=connector.display_name,
                exact_query=exact_query,
                endpoint_url=endpoint_url,
                endpoint_url_hash=(
                    sha256_text(endpoint_url) if endpoint_url is not None else None
                ),
                query_hash=sha256_text(_normalize_query(exact_query)),
                request_parameters=_request_parameters(exact_query, endpoint_url),
                filters_applied={
                    **query.filters,
                    **task.suggested_filters,
                },
                result_ids=_result_ids(hint),
                cache_state="not_executed",
                cache_key=cache_metadata.cache_key,
                cache_policy_id=cache_metadata.invalidation_policy_id,
                source_release_version=cache_metadata.source_release_version,
                rate_limit_metadata=_rate_limit_metadata(connector),
                external_network_allowed=external_network_allowed,
                execution_status=_execution_status(external_network_allowed),
                warnings=_warnings(
                    connector=connector,
                    task_warnings=task.warnings,
                    hint_warnings=hint.warnings if hint else [],
                    external_network_allowed=external_network_allowed,
                ),
                metadata={
                    "auth_requirement": connector.auth_requirement,
                    "license_notes": connector.license_notes,
                    "cache_metadata": cache_metadata.model_dump(mode="json"),
                    "query_transparency_required": connector.query_transparency_required,
                    "ingestion_approval_required": connector.ingestion_approval_required,
                    "source_url": connector.source_url,
                    "docs_url": connector.docs_url,
                },
            )
        )
    return records


def _default_knowledge_root() -> Path:
    return Path(__file__).resolve().parents[4] / "knowledge"


def _exact_query(task_query: str, hint: RetrievalSearchHint | None) -> str:
    return (hint.query if hint else task_query).strip()


def _endpoint_url(
    exact_query: str,
    hint: RetrievalSearchHint | None,
    connector: ExternalSourceConnector,
) -> str | None:
    if hint and hint.url:
        return hint.url
    parsed = urlparse(exact_query)
    if parsed.scheme and parsed.netloc:
        return exact_query
    return connector.source_url


def _request_parameters(
    exact_query: str,
    endpoint_url: str | None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for source in (endpoint_url, exact_query):
        if not source:
            continue
        parsed = urlparse(source)
        if not parsed.query:
            continue
        for key, values in parse_qs(parsed.query, keep_blank_values=True).items():
            params[key] = values[0] if len(values) == 1 else values
    if exact_query.startswith("GET "):
        params["http_template"] = exact_query
    return params


def _result_ids(hint: RetrievalSearchHint | None) -> list[str]:
    if hint is None:
        return []
    raw = hint.metadata.get("result_ids")
    if not isinstance(raw, list):
        return []
    return [str(value) for value in raw if str(value).strip()]


def _rate_limit_metadata(connector: ExternalSourceConnector) -> dict[str, Any]:
    return {
        "policy": connector.rate_limit_policy,
        "auth_requirement": connector.auth_requirement,
        "source": "external_connector_registry",
    }


def _execution_status(external_network_allowed: bool) -> str:
    return "not_executed" if external_network_allowed else "blocked_by_route_budget"


def _warnings(
    *,
    connector: ExternalSourceConnector,
    task_warnings: list[str],
    hint_warnings: list[str],
    external_network_allowed: bool,
) -> list[str]:
    warnings = [
        *task_warnings,
        *hint_warnings,
    ]
    if not external_network_allowed:
        warnings.append(
            "External query was not executed because the selected retrieval route "
            "does not allow external network calls."
        )
    if connector.ingestion_approval_required:
        warnings.append(
            "External results are candidate evidence until ingestion approval marks "
            "them searchable."
        )
    return _unique_nonblank(warnings)


def _record_id(connector_id: str, target: str, exact_query: str) -> str:
    return f"extq_{sha256_text(f'{connector_id}:{target}:{exact_query}')[:20]}"


def _normalize_query(value: str) -> str:
    return " ".join(value.strip().split())


def _unique_nonblank(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result
