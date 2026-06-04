"""Sanitized runtime configuration routes."""

from __future__ import annotations

from typing import Any
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends

from ojtflow.config import Settings
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.interfaces.api.deps import (
    get_api_settings,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok

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
            "retrieval": {
                "corpus_dir_count": len(settings.retrieval_corpus_dirs),
                "chunk_max_chars": settings.retrieval_chunk_max_chars,
                "chunk_overlap_chars": settings.retrieval_chunk_overlap_chars,
            },
            "upload": {
                "max_upload_bytes": settings.max_upload_bytes,
                "max_inline_data_bytes": settings.max_inline_data_bytes,
                "read_chunk_bytes": settings.upload_read_chunk_bytes,
                "allowed_extensions": list(settings.allowed_upload_extensions),
            },
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
