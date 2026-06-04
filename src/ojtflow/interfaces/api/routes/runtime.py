"""Sanitized runtime configuration routes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends

from ojtflow.application.workflow_service import WorkflowService
from ojtflow.config import (
    Settings,
    clear_settings_cache,
    get_settings,
    runtime_assistant_settings,
    runtime_retrieval_settings,
    save_runtime_assistant_settings,
    save_runtime_retrieval_settings,
)
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.core.errors import ToolExecutionError
from ojtflow.interfaces.api.deps import (
    clear_workflow_service_cache,
    get_api_settings,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import (
    RuntimeAssistantSettingsRequest,
    RuntimeRetrievalSettingsRequest,
)

try:
    import redis as redis_client
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover - dependency is installed in supported runtime.
    redis_client = None

    class RedisError(Exception):
        pass

router = APIRouter(tags=["runtime"])


@router.get("/runtime/config")
async def runtime_config(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return non-secret runtime facts for operations UI."""

    del authenticated
    return ok(
        {
            "status": "ok",
            "storage_backend": settings.storage_backend,
            "persistent_storage": settings.storage_backend in {"postgres", "sqlite"},
            "postgres_configured": bool(settings.postgres_dsn),
            "redis_configured": bool(settings.redis_url),
            "data_dir_configured": bool(settings.data_dir),
            "knowledge_dir_configured": bool(settings.knowledge_dir),
            "migrations_dir_configured": bool(settings.migrations_dir),
            "auth": {
                "google_oauth_configured": bool(
                    settings.google_client_id and settings.google_client_secret
                ),
                "hosted_domain_restricted": bool(settings.allowed_google_hosted_domains),
                "cookie_secure": settings.auth_cookie_secure,
                "cookie_effective_secure": settings.effective_auth_cookie_secure,
                "cookie_samesite": settings.auth_cookie_samesite,
                "session_ttl_seconds": settings.auth_session_ttl_seconds,
                "state_ttl_seconds": settings.auth_state_ttl_seconds,
            },
            "embedding": {
                "provider": settings.embedding_provider,
                "model": settings.embedding_model,
                "dimensions": settings.embedding_dimensions,
                "openai_configured": bool(settings.openai_api_key),
                "openai_base_url_configured": bool(settings.openai_embedding_base_url),
                "hf_device": settings.hf_embedding_device,
                "hf_batch_size": settings.hf_embedding_batch_size,
                "hf_cache_dir_configured": bool(settings.hf_embedding_cache_dir),
            },
            "llm": {
                "provider": settings.llm_provider,
                "model": settings.llm_model,
                "openai_configured": bool(settings.openai_api_key),
                "base_url_configured": bool(settings.llm_base_url),
                "timeout_seconds": settings.llm_timeout_seconds,
                "max_tool_calls": settings.llm_max_tool_calls,
                "runtime_settings_configured": bool(settings.runtime_settings_path),
                "runtime_settings": runtime_assistant_settings(settings),
            },
            "rerank": {
                "provider": settings.rerank_provider,
                "enabled": settings.rerank_provider != "none",
                "model": settings.rerank_model,
                "device": settings.rerank_device,
                "batch_size": settings.rerank_batch_size,
                "candidate_limit": settings.rerank_candidate_limit,
                "score_weight": settings.rerank_score_weight,
            },
            "retrieval": {
                "framework": settings.retrieval_framework,
                "corpus_dir_count": len(settings.retrieval_corpus_dirs),
                "chunk_max_chars": settings.retrieval_chunk_max_chars,
                "chunk_overlap_chars": settings.retrieval_chunk_overlap_chars,
                "candidate_multiplier": settings.retrieval_candidate_multiplier,
                "min_candidates": settings.retrieval_min_candidates,
                "vector_weight": settings.retrieval_vector_weight,
                "bm25_weight": settings.retrieval_bm25_weight,
                "diversity_enabled": settings.retrieval_diversity_enabled,
                "diversity_lambda": settings.retrieval_diversity_lambda,
                "hnsw_ef_search": settings.retrieval_hnsw_ef_search,
                "runtime_settings_configured": bool(settings.runtime_settings_path),
                "runtime_settings": runtime_retrieval_settings(settings),
                "rule_packs": _retrieval_rule_packs(settings),
            },
            "upload": {
                "max_upload_bytes": settings.max_upload_bytes,
                "max_inline_data_bytes": settings.max_inline_data_bytes,
                "read_chunk_bytes": settings.upload_read_chunk_bytes,
                "allowed_extensions": list(settings.allowed_upload_extensions),
            },
        }
    )


@router.put("/runtime/retrieval-settings")
async def update_runtime_retrieval_settings(
    request: RuntimeRetrievalSettingsRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Persist operator-tuned retrieval settings and reload cached services."""

    del authenticated
    updates = request.model_dump(exclude_none=True)
    try:
        save_runtime_retrieval_settings(settings, updates)
    except (TypeError, ValueError) as exc:
        raise ToolExecutionError(
            "Invalid runtime retrieval settings.",
            details={"reason": str(exc)},
        ) from exc

    clear_settings_cache()
    clear_workflow_service_cache()
    fresh_settings = get_settings()
    return ok(
        {
            "settings": runtime_retrieval_settings(fresh_settings),
            "reloaded": True,
        }
    )


@router.put("/runtime/assistant-settings")
async def update_runtime_assistant_settings(
    request: RuntimeAssistantSettingsRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Persist operator-tuned Assistant/LLM settings and reload cached services."""

    del authenticated
    updates = request.model_dump(exclude_none=True)
    try:
        save_runtime_assistant_settings(settings, updates)
    except (TypeError, ValueError) as exc:
        raise ToolExecutionError(
            "Invalid runtime assistant settings.",
            details={"reason": str(exc)},
        ) from exc

    clear_settings_cache()
    clear_workflow_service_cache()
    fresh_settings = get_settings()
    return ok(
        {
            "settings": runtime_assistant_settings(fresh_settings),
            "reloaded": True,
        }
    )


@router.get("/runtime/readiness")
async def runtime_readiness(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return sanitized readiness diagnostics for authenticated operators."""

    checks: list[dict[str, Any]] = [
        _check(
            "settings",
            "ok",
            "Runtime settings loaded.",
            {
                "storage_backend": settings.storage_backend,
                "persistent_storage": settings.storage_backend in {"postgres", "sqlite"},
            },
        )
    ]

    checks.append(_artifact_directory_check(settings))
    checks.append(_session_cache_check(settings.storage_backend, settings.redis_url))
    checks.append(_retrieval_rule_pack_readiness_check(settings))

    try:
        stats = service.workflows.stats(owner_user_id=authenticated.user.user_id)
        checks.append(
            _check(
                "workflow_repository",
                "ok",
                "Workflow repository is reachable.",
                {"visible_workflows": stats.total},
            )
        )
    except Exception as exc:  # pragma: no cover - failure path covered by API behavior.
        checks.append(_failure_check("workflow_repository", exc))

    try:
        schema_count = len(service.list_schemas())
        schemas_loaded = schema_count > 0
        checks.append(
            _check(
                "schema_inventory",
                "ok" if schemas_loaded else "error",
                "Trusted schema inventory is available."
                if schemas_loaded
                else "No trusted schema profiles were loaded; schema-backed workflows cannot run.",
                {"schema_count": schema_count},
            )
        )
    except Exception as exc:  # pragma: no cover
        checks.append(_failure_check("schema_inventory", exc))

    try:
        checks.append(_retrieval_readiness_check(service))
    except Exception as exc:  # pragma: no cover
        checks.append(_failure_check("retrieval_inventory", exc))

    return ok(
        {
            "status": _readiness_status(checks),
            "checks": checks,
        }
    )


def _check(
    name: str,
    status: str,
    summary: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "summary": summary,
        "details": details or {},
    }


def _artifact_directory_check(settings: Settings) -> dict[str, Any]:
    if settings.storage_backend == "memory":
        return _check(
            "artifact_directory",
            "ok",
            "Artifact directory is not required for memory storage.",
            {"required": False},
        )

    data_dir = settings.resolved_data_dir
    probes = {
        "data_dir": _directory_write_probe(data_dir),
        "datasets_dir": _directory_write_probe(data_dir / "datasets"),
        "outputs_dir": _directory_write_probe(data_dir / "outputs"),
    }
    writable = all(probe["writable"] for probe in probes.values())
    return _check(
        "artifact_directory",
        "ok" if writable else "error",
        "Artifact directories are writable."
        if writable
        else "One or more artifact directories are missing or not writable.",
        {
            "required": True,
            **probes,
        },
    )


def _retrieval_rule_packs(settings: Settings) -> list[dict[str, Any]]:
    root = settings.resolved_knowledge_dir
    return [
        _retrieval_rule_pack(
            root,
            name="query_expansion",
            relative_path=Path("retrieval/query_expansion_rules.json"),
            env_var="OJT_QUERY_EXPANSION_RULES_PATH",
        ),
        _retrieval_rule_pack(
            root,
            name="filter_suggestions",
            relative_path=Path("retrieval/filter_suggestion_rules.json"),
            env_var="OJT_FILTER_SUGGESTION_RULES_PATH",
        ),
        _retrieval_rule_pack(
            root,
            name="query_diagnostics",
            relative_path=Path("retrieval/query_diagnostic_rules.json"),
            env_var="OJT_QUERY_DIAGNOSTIC_RULES_PATH",
        ),
        _retrieval_rule_pack(
            root,
            name="ranking_boosts",
            relative_path=Path("retrieval/ranking_boost_rules.json"),
            env_var="OJT_RANKING_BOOST_RULES_PATH",
        ),
        _retrieval_rule_pack(
            root,
            name="evaluation_policy",
            relative_path=Path("retrieval/evaluation_policy.json"),
            env_var="OJT_RETRIEVAL_EVALUATION_POLICY_PATH",
        ),
        _retrieval_rule_pack(
            root,
            name="search_hint_targets",
            relative_path=Path("retrieval/search_hint_targets.json"),
            env_var="OJT_SEARCH_HINT_TARGETS_PATH",
        ),
    ]


def _retrieval_rule_pack(
    knowledge_root: Path,
    *,
    name: str,
    relative_path: Path,
    env_var: str,
) -> dict[str, Any]:
    override = os.environ.get(env_var)
    path = Path(override) if override else knowledge_root / relative_path
    source = "override" if override else "knowledge"
    details: dict[str, Any] = {
        "name": name,
        "status": "missing",
        "source": source,
        "env_var": env_var,
        "configured": bool(override),
        "rule_count": 0,
    }
    if not path.exists():
        return details
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            **details,
            "status": "error",
            "error": type(exc).__name__,
        }
    rules = raw.get("rules") if isinstance(raw, dict) else None
    targets = raw.get("targets") if isinstance(raw, dict) else None
    items = rules if isinstance(rules, list) else targets if isinstance(targets, list) else []
    return {
        **details,
        "status": "ok",
        "rule_count": len(items),
    }


def _retrieval_rule_pack_readiness_check(settings: Settings) -> dict[str, Any]:
    packs = _retrieval_rule_packs(settings)
    issues = [pack for pack in packs if pack["status"] != "ok"]
    return _check(
        "retrieval_rule_packs",
        "ok" if not issues else "error",
        "Retrieval rule packs are loadable."
        if not issues
        else "One or more retrieval rule packs are missing or malformed.",
        {
            "pack_count": len(packs),
            "issue_count": len(issues),
            "packs": packs,
        },
    )


def _directory_write_probe(path: Path) -> dict[str, Any]:
    exists = path.exists()
    is_dir = path.is_dir()
    if not exists or not is_dir:
        return {"exists": exists, "is_dir": is_dir, "writable": False}

    probe_path = path / f".ojtflow-readiness-{uuid4().hex}.tmp"
    try:
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink()
        return {"exists": True, "is_dir": True, "writable": True}
    except OSError as exc:
        try:
            if probe_path.exists():
                probe_path.unlink()
        except OSError:
            pass
        return {
            "exists": True,
            "is_dir": True,
            "writable": False,
            "error_type": type(exc).__name__,
        }


def _session_cache_check(storage_backend: str, redis_url: str) -> dict[str, Any]:
    if storage_backend != "postgres":
        return _check(
            "session_cache",
            "ok",
            "Session cache uses the process-local adapter for this storage backend.",
            {"mode": "process_local"},
        )
    if not redis_url:
        return _check(
            "session_cache",
            "error",
            "Redis session cache is not configured; Postgres auth is not multi-instance ready.",
            {"mode": "fallback"},
        )
    if redis_client is None:
        return _check(
            "session_cache",
            "error",
            "Redis dependency is unavailable; Postgres auth is not multi-instance ready.",
            {"mode": "fallback", "error_type": "ImportError"},
        )
    try:
        client = redis_client.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        client.ping()
    except (RedisError, ValueError) as exc:
        return _check(
            "session_cache",
            "error",
            "Redis session cache is configured but not reachable; Postgres auth is not multi-instance ready.",
            {"mode": "fallback", "error_type": type(exc).__name__},
        )
    return _check(
        "session_cache",
        "ok",
        "Redis session cache is reachable.",
        {"mode": "redis", "reachable": True},
    )


def _retrieval_readiness_check(service: WorkflowService) -> dict[str, Any]:
    sources = service.list_retrieval_sources()
    package = service.search_retrieval(
        RetrievalQuery(
            query="lab result schema unit date patient identifier",
            top_k=3,
            filters={"trust_level": "approved"},
        )
    )
    source_count = len(sources)
    hit_count = len(package.hits)
    warning_count = len(package.trace.warnings)
    if source_count == 0:
        status = "error"
        summary = "No trusted retrieval sources were loaded; evidence-backed workflows cannot run."
    elif hit_count == 0:
        status = "warning"
        summary = "Retrieval inventory loaded, but the search probe returned no evidence."
    else:
        status = "ok"
        summary = "Retrieval source inventory and search probe are available."
    return _check(
        "retrieval_inventory",
        status,
        summary,
        {
            "source_count": source_count,
            "probe_hit_count": hit_count,
            "probe_strategy": package.trace.strategy,
            "probe_candidates_seen": package.trace.candidates_seen,
            "probe_warning_count": warning_count,
        },
    )


def _failure_check(name: str, exc: Exception) -> dict[str, Any]:
    return _check(
        name,
        "error",
        f"{name.replace('_', ' ').title()} check failed.",
        {"error_type": type(exc).__name__},
    )


def _readiness_status(checks: list[dict[str, Any]]) -> str:
    statuses = {str(check["status"]) for check in checks}
    if "error" in statuses:
        return "not_ready"
    if "warning" in statuses:
        return "degraded"
    return "ready"
