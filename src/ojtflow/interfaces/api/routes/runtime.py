"""Sanitized runtime configuration routes."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from ojtflow.application.governance_service import GovernanceService
from ojtflow.application.workflow_service import WorkflowService
from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.medical_evidence_service import OCR_LOW_CONFIDENCE_THRESHOLD
from ojtflow.application.runtime_settings_history import (
    append_runtime_setting_history,
    list_runtime_setting_history,
    rollback_runtime_settings_change,
)
from ojtflow.config import (
    Settings,
    clear_settings_cache,
    load_runtime_settings_overrides,
    runtime_assistant_settings,
    runtime_retrieval_settings,
    save_runtime_assistant_settings,
    save_runtime_retrieval_settings,
)
from ojtflow.core.policy.abuse_cost_policy import load_abuse_cost_policy
from ojtflow.core.contracts.auth import AuthenticatedSession
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.core.contracts.runtime import MigrationDiagnostics
from ojtflow.core.contracts.storage_consistency import StorageRepairPlan
from ojtflow.core.errors import ToolExecutionError
from ojtflow.interfaces.api.deps import (
    clear_workflow_service_cache,
    get_api_settings,
    get_background_job_service,
    get_governance_service,
    get_workflow_service,
    require_authentication,
)
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import (
    RuntimeAssistantSettingsRequest,
    RuntimeRetrievalSettingsRequest,
    RuntimeSettingsRollbackRequest,
)
from ojtflow.infrastructure.storage import migrations as migrations_module
from ojtflow.infrastructure.storage.consistency import (
    build_storage_repair_plan,
    scan_workflow_artifacts,
    write_storage_repair_marker,
)
from ojtflow.infrastructure.storage.migrations import PostgresMigrator
from ojtflow.infrastructure.retrieval.rule_packs import retrieval_rule_packs
from ojtflow.application.tool_registry import tool_specs_json

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
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return non-secret runtime facts for operations UI."""

    governance.require_permission(user=authenticated.user, permission_scope="settings:read")
    tool_specs = tool_specs_json()
    abuse_cost_policy = load_abuse_cost_policy(settings.resolved_abuse_cost_policy_path)
    return ok(
        {
            "status": "ok",
            "product_mode": settings.product_mode,
            "storage_backend": settings.storage_backend,
            "persistent_storage": settings.storage_backend in {"postgres", "sqlite"},
            "postgres_configured": bool(settings.postgres_dsn),
            "redis_configured": bool(settings.redis_url),
            "data_dir_configured": bool(settings.data_dir),
            "knowledge_dir_configured": bool(settings.knowledge_dir),
            "migrations_dir_configured": bool(settings.migrations_dir),
            "audit": {
                "hash_chain_written": True,
                "hash_chain_required": settings.effective_audit_hash_chain_required,
                "hash_chain_required_configured": settings.audit_hash_chain_required,
            },
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
                "service_account_token_ttl_seconds": (
                    settings.service_account_token_ttl_seconds
                ),
                "service_account_default_role_key": (
                    settings.service_account_default_role_key
                ),
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
                "planning_model": settings.llm_planning_model,
                "synthesis_model": settings.llm_synthesis_model,
                "vision_model": settings.llm_vision_model,
                "openai_configured": bool(settings.openai_api_key),
                "base_url": settings.llm_base_url,
                "base_url_configured": bool(settings.llm_base_url),
                "timeout_seconds": settings.llm_timeout_seconds,
                "max_tool_calls": settings.llm_max_tool_calls,
                "planning_progress_interval_seconds": (
                    settings.llm_planning_progress_interval_seconds
                ),
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
                "rule_packs": retrieval_rule_packs(settings.resolved_knowledge_dir),
            },
            "upload": {
                "max_upload_bytes": settings.max_upload_bytes,
                "max_inline_data_bytes": settings.max_inline_data_bytes,
                "read_chunk_bytes": settings.upload_read_chunk_bytes,
                "allowed_extensions": list(settings.allowed_upload_extensions),
            },
            "retention": {
                "artifact_rule_count": len(settings.artifact_retention_rules),
                "artifact_policy_configured": bool(settings.artifact_retention_rules),
            },
            "tools": {
                "registered_count": len(tool_specs),
                "approval_required_count": sum(
                    1 for spec in tool_specs if bool(spec.get("requires_approval"))
                ),
                "write_gates_enabled": True,
            },
            "rate_limit": {
                "enabled": settings.rate_limit_enabled,
                "backend": settings.rate_limit_backend,
                "policy_configured": bool(settings.rate_limit_policy_path),
                "redis_prefix_configured": bool(settings.rate_limit_redis_prefix),
            },
            "cost_controls": {
                "policy_configured": bool(settings.abuse_cost_policy_path),
                "llm_max_request_chars": abuse_cost_policy.llm.max_request_chars,
                "ocr_max_openai_vision_bytes": (
                    abuse_cost_policy.ocr.max_openai_vision_bytes
                ),
                "embedding_max_request_inputs": (
                    abuse_cost_policy.embeddings.max_request_inputs
                ),
                "embedding_max_request_chars": (
                    abuse_cost_policy.embeddings.max_request_chars
                ),
                "batch_max_total_bytes": (
                    abuse_cost_policy.batch_ingestion.max_batch_total_bytes
                ),
            },
            "review_policy": {
                "default_human_review_required": True,
                "ocr_low_confidence_threshold": OCR_LOW_CONFIDENCE_THRESHOLD,
            },
            "policy": {
                "no_mock_data": settings.no_mock_data,
                "effective_no_mock_data": settings.effective_no_mock_data,
                "requires_real_llm": settings.product_mode in {"pilot", "production"},
                "requires_persistent_storage": settings.product_mode
                in {"pilot", "production"},
            },
        }
    )


@router.put("/runtime/retrieval-settings")
async def update_runtime_retrieval_settings(
    request: RuntimeRetrievalSettingsRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Persist operator-tuned retrieval settings and reload cached services."""

    governance.require_permission(user=authenticated.user, permission_scope="settings:write")
    payload = request.model_dump(exclude_none=True)
    reason = payload.pop("change_reason", None)
    updates = payload
    before = load_runtime_settings_overrides(settings)
    try:
        save_runtime_retrieval_settings(settings, updates)
    except (TypeError, ValueError) as exc:
        raise ToolExecutionError(
            "Invalid runtime retrieval settings.",
            details={"reason": str(exc)},
        ) from exc
    after = load_runtime_settings_overrides(settings)
    history_entry = append_runtime_setting_history(
        settings=settings,
        surface="retrieval",
        actor_id=authenticated.user.user_id,
        actor_email=authenticated.user.email,
        reason=reason,
        before=before,
        after=after,
        keys=set(updates),
    )

    clear_settings_cache()
    clear_workflow_service_cache()
    fresh_settings = await get_api_settings()
    return ok(
        {
            "settings": runtime_retrieval_settings(fresh_settings),
            "reloaded": True,
            "history_entry": history_entry,
        }
    )


@router.put("/runtime/assistant-settings")
async def update_runtime_assistant_settings(
    request: RuntimeAssistantSettingsRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Persist operator-tuned Assistant/LLM settings and reload cached services."""

    governance.require_permission(user=authenticated.user, permission_scope="settings:write")
    payload = request.model_dump(exclude_none=True)
    reason = payload.pop("change_reason", None)
    updates = payload
    before = load_runtime_settings_overrides(settings)
    try:
        save_runtime_assistant_settings(settings, updates)
    except (TypeError, ValueError) as exc:
        raise ToolExecutionError(
            "Invalid runtime assistant settings.",
            details={"reason": str(exc)},
        ) from exc
    after = load_runtime_settings_overrides(settings)
    history_entry = append_runtime_setting_history(
        settings=settings,
        surface="assistant",
        actor_id=authenticated.user.user_id,
        actor_email=authenticated.user.email,
        reason=reason,
        before=before,
        after=after,
        keys=set(updates),
    )

    clear_settings_cache()
    clear_workflow_service_cache()
    fresh_settings = await get_api_settings()
    return ok(
        {
            "settings": runtime_assistant_settings(fresh_settings),
            "reloaded": True,
            "history_entry": history_entry,
        }
    )


@router.get("/runtime/settings-history")
async def runtime_settings_history(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    """Return runtime setting history entries visible to settings readers."""

    governance.require_permission(user=authenticated.user, permission_scope="settings:read")
    return ok(list_runtime_setting_history(settings, limit=limit))


@router.get("/runtime/secrets/health")
async def runtime_secrets_health(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return sanitized secret/configuration readiness without secret values."""

    governance.require_permission(user=authenticated.user, permission_scope="admin:read")
    return ok(_secret_health(settings))


@router.post("/runtime/settings-history/rollback")
async def rollback_runtime_settings_history(
    request: RuntimeSettingsRollbackRequest,
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Rollback a previous runtime setting change and record the rollback."""

    governance.require_permission(user=authenticated.user, permission_scope="settings:write")
    history_entry = rollback_runtime_settings_change(
        settings=settings,
        change_id=request.change_id,
        actor_id=authenticated.user.user_id,
        actor_email=authenticated.user.email,
        reason=request.reason,
    )
    clear_settings_cache()
    clear_workflow_service_cache()
    fresh_settings = await get_api_settings()
    return ok(
        {
            "settings": {
                "assistant": runtime_assistant_settings(fresh_settings),
                "retrieval": runtime_retrieval_settings(fresh_settings),
            },
            "reloaded": True,
            "history_entry": history_entry,
        }
    )


def _secret_health(settings: Settings) -> dict[str, Any]:
    checks = [
        _secret_check(
            name="Google OAuth client ID",
            env_vars=["OJT_GOOGLE_CLIENT_ID"],
            configured=bool(settings.google_client_id),
            required=settings.product_mode in {"pilot", "production"},
            remediation="Create a Google OAuth web client and set OJT_GOOGLE_CLIENT_ID.",
        ),
        _secret_check(
            name="Google OAuth client secret",
            env_vars=["OJT_GOOGLE_CLIENT_SECRET"],
            configured=bool(settings.google_client_secret),
            required=settings.product_mode in {"pilot", "production"},
            remediation="Set OJT_GOOGLE_CLIENT_SECRET from the OAuth client secret value.",
        ),
        _secret_check(
            name="OpenAI API key",
            env_vars=["OJT_OPENAI_API_KEY", "OPENAI_API_KEY"],
            configured=bool(settings.openai_api_key),
            required=(
                settings.llm_provider == "openai"
                or settings.embedding_provider == "openai"
                or settings.product_mode in {"pilot", "production"}
            ),
            remediation="Set OJT_OPENAI_API_KEY or OPENAI_API_KEY for OpenAI-backed LLM/embedding features.",
        ),
        _secret_check(
            name="Postgres database URL",
            env_vars=["OJT_DATABASE_URL", "DATABASE_URL"],
            configured=bool(settings.postgres_dsn),
            required=settings.storage_backend == "postgres",
            remediation="Set OJT_DATABASE_URL for the Postgres-backed backend spine.",
        ),
        _secret_check(
            name="Redis URL",
            env_vars=["OJT_REDIS_URL"],
            configured=bool(settings.redis_url),
            required=settings.storage_backend == "postgres",
            remediation="Set OJT_REDIS_URL for Postgres session/cache deployment.",
        ),
    ]
    status = "ok"
    if any(check["status"] == "error" for check in checks):
        status = "error"
    elif any(check["status"] == "warning" for check in checks):
        status = "warning"
    return {
        "status": status,
        "product_mode": settings.product_mode,
        "storage_backend": settings.storage_backend,
        "secret_values_exposed": False,
        "checks": checks,
    }


def _secret_check(
    *,
    name: str,
    env_vars: list[str],
    configured: bool,
    required: bool,
    remediation: str,
) -> dict[str, Any]:
    if configured:
        status = "ok"
    elif required:
        status = "error"
    else:
        status = "warning"
    return {
        "name": name,
        "status": status,
        "configured": configured,
        "required": required,
        "env_vars": env_vars,
        "remediation": remediation,
    }


@router.get("/runtime/readiness")
async def runtime_readiness(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return sanitized readiness diagnostics for authenticated operators."""

    governance.require_permission(user=authenticated.user, permission_scope="admin:read")
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

    checks.append(_product_mode_policy_check(settings))
    checks.append(_migration_readiness_check(settings))
    checks.append(_artifact_directory_check(settings))
    checks.append(_auth_configuration_check(settings))
    checks.append(_session_cache_check(settings.storage_backend, settings.redis_url))
    checks.append(_embedding_configuration_check(settings))
    checks.append(_llm_configuration_check(settings))
    checks.append(_mcp_tool_registry_check())
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

    try:
        checks.append(_storage_consistency_check(service, settings, authenticated.user.user_id))
    except Exception as exc:  # pragma: no cover
        checks.append(_failure_check("storage_consistency", exc))

    try:
        checks.append(_job_repository_check(jobs, authenticated.user.user_id))
    except Exception as exc:  # pragma: no cover
        checks.append(_failure_check("job_repository", exc))

    return ok(
        {
            "status": _readiness_status(checks),
            "checks": checks,
        }
    )


@router.get("/runtime/migrations")
async def runtime_migrations(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    settings: Settings = Depends(get_api_settings),
) -> dict:
    """Return sanitized Postgres migration manifest/database diagnostics."""

    governance.require_permission(user=authenticated.user, permission_scope="admin:read")
    diagnostics = _migration_diagnostics(settings)
    return ok(diagnostics.model_dump(mode="json"))


@router.get("/runtime/storage-consistency")
async def runtime_storage_consistency(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
    limit: int = Query(default=100, ge=1, le=500),
    include_seeded: bool = Query(default=True),
    include_corpus: bool = Query(default=True),
) -> dict:
    """Return a sanitized workflow, artifact, and knowledge consistency report."""

    governance.require_permission(user=authenticated.user, permission_scope="admin:read")
    if settings.storage_backend == "memory":
        report = scan_workflow_artifacts(
            [],
            data_dir=settings.resolved_data_dir,
            required=False,
        )
    else:
        workflows = service.list_workflows(
            limit=limit,
            owner_user_id=authenticated.user.user_id,
        )
        dataset_records = service.datasets.list_records(limit=max(limit * 3, 100))
        retrieval_integrity = service.retrieval_integrity_report(
            include_seeded=include_seeded,
            include_corpus=include_corpus,
        )
        report = scan_workflow_artifacts(
            workflows,
            data_dir=settings.resolved_data_dir,
            required=True,
            dataset_records=dataset_records,
            retrieval_integrity=retrieval_integrity,
        )
    return ok(
        {
            "status": "consistent" if report.is_consistent else "inconsistent",
            "report": report.model_dump(mode="json"),
        }
    )


@router.get("/runtime/storage-repair-plan")
async def runtime_storage_repair_plan(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
    limit: int = Query(default=100, ge=1, le=500),
    max_candidates: int = Query(default=100, ge=1, le=500),
) -> dict:
    """Return a sanitized, non-destructive storage repair plan."""

    governance.require_permission(user=authenticated.user, permission_scope="admin:read")
    plan = _storage_repair_plan_for_user(
        service,
        settings,
        authenticated.user.user_id,
        limit=limit,
        max_candidates=max_candidates,
    )
    if not plan.required:
        status = "not_required"
    elif plan.total_candidate_count == 0:
        status = "no_action_needed"
    else:
        status = "review_required"
    return ok(
        {
            "status": status,
            "plan": plan.model_dump(mode="json"),
        }
    )


@router.post("/runtime/storage-repair-markers")
async def runtime_storage_repair_markers(
    authenticated: AuthenticatedSession = Depends(require_authentication),
    governance: GovernanceService = Depends(get_governance_service),
    service: WorkflowService = Depends(get_workflow_service),
    settings: Settings = Depends(get_api_settings),
    limit: int = Query(default=100, ge=1, le=500),
    max_candidates: int = Query(default=100, ge=1, le=500),
) -> dict:
    """Persist a sanitized marker for current storage repair candidates."""

    governance.require_permission(user=authenticated.user, permission_scope="admin:write")
    plan = _storage_repair_plan_for_user(
        service,
        settings,
        authenticated.user.user_id,
        limit=limit,
        max_candidates=max_candidates,
    )
    if not plan.required:
        return ok({"status": "not_required", "plan": plan.model_dump(mode="json")})
    if plan.returned_candidate_count == 0:
        return ok({"status": "no_action_needed", "plan": plan.model_dump(mode="json")})

    marker = write_storage_repair_marker(plan, data_dir=settings.resolved_data_dir)
    return ok(
        {
            "status": "marked",
            "marker": marker.model_dump(mode="json"),
            "plan": plan.model_dump(mode="json"),
        }
    )


def _storage_repair_plan_for_user(
    service: WorkflowService,
    settings: Settings,
    owner_user_id: str,
    *,
    limit: int,
    max_candidates: int,
) -> StorageRepairPlan:
    if settings.storage_backend == "memory":
        return build_storage_repair_plan(
            [],
            data_dir=settings.resolved_data_dir,
            required=False,
            max_candidates=max_candidates,
        )

    workflows = service.list_workflows(limit=limit, owner_user_id=owner_user_id)
    dataset_records = service.datasets.list_records(limit=max(limit * 3, 100))
    return build_storage_repair_plan(
        workflows,
        data_dir=settings.resolved_data_dir,
        required=True,
        dataset_records=dataset_records,
        max_candidates=max_candidates,
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


def _product_mode_policy_check(settings: Settings) -> dict[str, Any]:
    requires_real_llm = settings.product_mode in {"pilot", "production"}
    requires_persistent_storage = settings.product_mode in {"pilot", "production"}
    violations: list[str] = []
    if requires_persistent_storage and settings.storage_backend == "memory":
        violations.append("memory_storage")
    if requires_real_llm and settings.llm_provider == "disabled":
        violations.append("disabled_llm")
    return _check(
        "product_mode_policy",
        "ok" if not violations else "error",
        "Product mode policy is satisfied."
        if not violations
        else "Product mode policy blocks this runtime configuration.",
        {
            "product_mode": settings.product_mode,
            "no_mock_data": settings.no_mock_data,
            "effective_no_mock_data": settings.effective_no_mock_data,
            "requires_real_llm": requires_real_llm,
            "requires_persistent_storage": requires_persistent_storage,
            "violations": violations,
        },
    )


def _retrieval_rule_pack_readiness_check(settings: Settings) -> dict[str, Any]:
    packs = retrieval_rule_packs(settings.resolved_knowledge_dir)
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


def _migration_readiness_check(settings: Settings) -> dict[str, Any]:
    diagnostics = _migration_diagnostics(settings)
    details = diagnostics.model_dump(mode="json")
    if diagnostics.status == "not_required":
        return _check(
            "postgres_migrations",
            "ok",
            diagnostics.bootstrap_summary,
            details,
        )
    return _check(
        "postgres_migrations",
        "ok" if diagnostics.status == "ok" else "error",
        diagnostics.bootstrap_summary,
        details,
    )


def _migration_diagnostics(settings: Settings) -> MigrationDiagnostics:
    postgres_configured = bool(settings.postgres_dsn)
    if settings.storage_backend != "postgres":
        try:
            migrations = PostgresMigrator(
                settings.postgres_dsn,
                migrations_dir=settings.resolved_migrations_dir,
            ).load_migrations()
        except Exception as exc:
            return MigrationDiagnostics(
                status="error",
                storage_backend=settings.storage_backend,
                required=False,
                postgres_configured=postgres_configured,
                bootstrap_code=_classify_migration_bootstrap_error(exc),
                bootstrap_summary="Postgres migration manifest could not be loaded.",
            )
        return MigrationDiagnostics(
            status="not_required",
            storage_backend=settings.storage_backend,
            required=False,
            postgres_configured=postgres_configured,
            manifest_count=len(migrations),
            latest_available_version=migrations[-1].version if migrations else None,
            bootstrap_code="not_required",
            bootstrap_summary=(
                "Postgres migration manifest is loadable; database migration state is not required for this storage backend."
            ),
            migrations=[
                {
                    "version": migration.version,
                    "name": migration.name,
                    "checksum": migration.checksum,
                    "status": "pending",
                }
                for migration in migrations
            ],
        )

    if not postgres_configured:
        return MigrationDiagnostics(
            status="error",
            storage_backend=settings.storage_backend,
            required=True,
            postgres_configured=False,
            connection_ok=False,
            bootstrap_code="missing_dsn",
            bootstrap_summary="Postgres storage is selected but OJT_DATABASE_URL is not configured.",
        )

    if migrations_module.psycopg is None:
        return MigrationDiagnostics(
            status="error",
            storage_backend=settings.storage_backend,
            required=True,
            postgres_configured=True,
            dependency_available=False,
            connection_ok=False,
            bootstrap_code="dependency_unavailable",
            bootstrap_summary="Postgres diagnostics require psycopg to be installed.",
        )

    try:
        report = PostgresMigrator(
            settings.postgres_dsn,
            migrations_dir=settings.resolved_migrations_dir,
        ).inspect_database()
    except Exception as exc:
        return MigrationDiagnostics(
            status="error",
            storage_backend=settings.storage_backend,
            required=True,
            postgres_configured=True,
            dependency_available=True,
            connection_ok=False,
            bootstrap_code=_classify_migration_bootstrap_error(exc),
            bootstrap_summary=_migration_bootstrap_summary(exc),
        )

    pending_count = int(report["pending_count"])
    unknown_count = int(report["unknown_applied_count"])
    mismatch_count = int(report["checksum_mismatch_count"])
    if unknown_count or mismatch_count:
        status = "error"
        summary = "Postgres migration history has unknown or checksum-mismatched entries."
        code = "migration_history_conflict"
    elif pending_count:
        status = "error"
        summary = "Postgres has pending migrations; apply them before serving traffic."
        code = "pending_migrations"
    else:
        status = "ok"
        summary = "Postgres migration history matches the source manifest."
        code = "ok"

    return MigrationDiagnostics(
        status=status,
        storage_backend=settings.storage_backend,
        required=True,
        postgres_configured=True,
        dependency_available=True,
        connection_ok=True,
        table_exists=bool(report["table_exists"]),
        manifest_count=int(report["manifest_count"]),
        applied_count=int(report["applied_count"]),
        pending_count=pending_count,
        unknown_applied_count=unknown_count,
        checksum_mismatch_count=mismatch_count,
        latest_available_version=report["latest_available_version"],
        latest_applied_version=report["latest_applied_version"],
        bootstrap_code=code,
        bootstrap_summary=summary,
        migrations=report["migrations"],
    )


def _classify_migration_bootstrap_error(exc: Exception) -> str:
    text = str(exc).casefold()
    name = type(exc).__name__.casefold()
    if "duplicate migration version" in text:
        return "duplicate_migration"
    if "psycopg" in text and "install" in text:
        return "dependency_unavailable"
    if "invalid dsn" in text or "missing" in text and "database" in text:
        return "bad_dsn"
    if "password authentication failed" in text or "authentication failed" in text:
        return "auth_failed"
    if "could not translate host name" in text or "name or service not known" in text:
        return "dns_failed"
    if "connection refused" in text or "is the server running" in text:
        return "network_refused"
    if "timeout" in text or "timed out" in text:
        return "network_timeout"
    if "extension" in text and ("does not exist" in text or "unavailable" in text):
        return "missing_extension"
    if "operationalerror" in name:
        return "connection_failed"
    return "migration_inspection_failed"


def _migration_bootstrap_summary(exc: Exception) -> str:
    code = _classify_migration_bootstrap_error(exc)
    summaries = {
        "duplicate_migration": "Postgres migration manifest contains a duplicate version.",
        "dependency_unavailable": "Postgres diagnostics require psycopg to be installed.",
        "bad_dsn": "Postgres database URL is malformed or incomplete.",
        "auth_failed": "Postgres rejected the configured credentials.",
        "dns_failed": "Postgres host name could not be resolved.",
        "network_refused": "Postgres connection was refused by the target host.",
        "network_timeout": "Postgres connection timed out.",
        "missing_extension": "A required Postgres extension is unavailable.",
        "connection_failed": "Postgres connection failed before migration inspection could complete.",
    }
    return summaries.get(code, "Postgres migration diagnostics could not inspect the database.")


def _auth_configuration_check(settings: Settings) -> dict[str, Any]:
    has_client_id = bool(settings.google_client_id)
    has_client_secret = bool(settings.google_client_secret)
    configured = has_client_id and has_client_secret
    partial = has_client_id != has_client_secret
    if partial:
        status = "error"
        summary = "Google OAuth is partially configured; both client ID and client secret are required."
    elif configured:
        status = "ok"
        summary = "Google OAuth configuration is present."
    else:
        status = "ok"
        summary = "Google OAuth is not configured; local/dev auth overrides may still run."
    return _check(
        "auth_configuration",
        status,
        summary,
        {
            "google_oauth_configured": configured,
            "partial_configuration": partial,
            "hosted_domain_restricted": bool(settings.allowed_google_hosted_domains),
            "cookie_secure": settings.auth_cookie_secure,
            "cookie_effective_secure": settings.effective_auth_cookie_secure,
            "cookie_samesite": settings.auth_cookie_samesite,
            "session_ttl_seconds": settings.auth_session_ttl_seconds,
            "state_ttl_seconds": settings.auth_state_ttl_seconds,
        },
    )


def _embedding_configuration_check(settings: Settings) -> dict[str, Any]:
    if settings.embedding_provider == "openai" and not settings.openai_api_key:
        return _check(
            "embedding_configuration",
            "error",
            "OpenAI embeddings are selected but no API key is configured.",
            {
                "provider": settings.embedding_provider,
                "model": settings.embedding_model,
                "dimensions": settings.embedding_dimensions,
                "api_key_configured": False,
            },
        )
    return _check(
        "embedding_configuration",
        "ok",
        "Embedding provider configuration is internally consistent.",
        {
            "provider": settings.embedding_provider,
            "model": settings.embedding_model,
            "dimensions": settings.embedding_dimensions,
            "semantic_provider": settings.embedding_provider != "deterministic",
        },
    )


def _llm_configuration_check(settings: Settings) -> dict[str, Any]:
    if settings.llm_provider == "openai" and not settings.openai_api_key:
        return _check(
            "llm_configuration",
            "error",
            "OpenAI LLM mode is selected but no API key is configured.",
            {
                "provider": settings.llm_provider,
                "model": settings.llm_model,
                "planning_model": settings.llm_planning_model,
                "synthesis_model": settings.llm_synthesis_model,
                "vision_model": settings.llm_vision_model,
                "api_key_configured": False,
            },
        )
    return _check(
        "llm_configuration",
        "ok",
        "Assistant LLM configuration is internally consistent.",
        {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "planning_model": settings.llm_planning_model,
            "synthesis_model": settings.llm_synthesis_model,
            "vision_model": settings.llm_vision_model,
            "real_ai_enabled": settings.llm_provider != "disabled",
            "timeout_seconds": settings.llm_timeout_seconds,
            "max_tool_calls": settings.llm_max_tool_calls,
            "planning_progress_interval_seconds": (
                settings.llm_planning_progress_interval_seconds
            ),
        },
    )


def _mcp_tool_registry_check() -> dict[str, Any]:
    specs = tool_specs_json()
    names = [str(spec["name"]) for spec in specs]
    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    missing_agent_count = sum(1 for spec in specs if not spec.get("allowed_agents"))
    status = "error" if duplicate_names or missing_agent_count else "ok"
    return _check(
        "mcp_tool_registry",
        status,
        "Tool registry metadata is ready for MCP handoff."
        if status == "ok"
        else "Tool registry metadata has duplicate tools or missing agent scopes.",
        {
            "tool_count": len(specs),
            "approval_required_count": sum(
                1 for spec in specs if bool(spec.get("requires_approval"))
            ),
            "duplicate_names": duplicate_names,
            "missing_agent_scope_count": missing_agent_count,
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


def _storage_consistency_check(
    service: WorkflowService,
    settings: Settings,
    owner_user_id: str,
) -> dict[str, Any]:
    if settings.storage_backend == "memory":
        report = scan_workflow_artifacts(
            [],
            data_dir=settings.resolved_data_dir,
            required=False,
        )
        return _check(
            "storage_consistency",
            "ok",
            "Storage consistency scan is not required for memory storage.",
            report.model_dump(mode="json"),
        )

    workflows = service.list_workflows(limit=100, owner_user_id=owner_user_id)
    dataset_records = (
        service.datasets.list_records(limit=300)
        if hasattr(service, "datasets")
        else []
    )
    report = scan_workflow_artifacts(
        workflows,
        data_dir=settings.resolved_data_dir,
        required=True,
        dataset_records=dataset_records,
        retrieval_integrity=service.retrieval_integrity_report(
            include_seeded=True,
            include_corpus=False,
        ),
    )
    status = "ok" if report.is_consistent else "error"
    summary = (
        "Workflow artifacts, dataset records, and retrieval source index are consistent for the sampled scope."
        if report.is_consistent
        else "One or more sampled artifact refs, dataset rows, local files, or retrieval source indexes are missing, stale, or hash-mismatched."
    )

    return _check(
        "storage_consistency",
        status,
        summary,
        report.model_dump(mode="json"),
    )


def _job_repository_check(
    jobs: BackgroundJobService,
    owner_user_id: str,
) -> dict[str, Any]:
    visible_jobs = jobs.list_jobs(owner_user_id=owner_user_id, limit=1)
    return _check(
        "job_repository",
        "ok",
        "Background job repository is reachable.",
        {
            "probe_count": len(visible_jobs),
            "runner_mode": "sync_local",
            "queue_backed": False,
            "supported_job_types": [
                "retrieval_reindex",
                "file_parse",
                "ocr_extract",
                "embedding_reindex",
                "external_ingest",
                "export_package",
            ],
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
