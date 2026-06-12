#!/usr/bin/env python3
"""Run bounded OJTFlow performance smoke scenarios."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ojtflow.config import clear_settings_cache  # noqa: E402
from ojtflow.core.contracts.auth import (  # noqa: E402
    AuthenticatedSession,
    SessionRecord,
    UserRecord,
)
from ojtflow.core.contracts.operations import (  # noqa: E402
    LoadSmokeReport,
    LoadSmokeScenario,
    LoadSmokeScenarioResult,
)
from ojtflow.infrastructure.operations import load_load_smoke_plan  # noqa: E402
from ojtflow.interfaces.api.app import create_app  # noqa: E402
from ojtflow.interfaces.api.deps import (  # noqa: E402
    clear_workflow_service_cache,
    get_governance_service,
    require_authentication,
)


class AllowAllGovernance:
    def require_permission(self, *, user, permission_scope: str) -> None:
        del user, permission_scope


async def authenticated_dependency() -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    user = UserRecord(
        user_id="usr_perf_smoke",
        google_sub="performance-smoke",
        email="performance-smoke@example.com",
        email_verified=True,
        display_name="Performance Smoke",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_perf_smoke",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


async def main_async() -> int:
    parser = argparse.ArgumentParser(description="Run OJTFlow performance smoke checks.")
    parser.add_argument("--mode", choices=["asgi", "http"], default="asgi")
    parser.add_argument("--base-url", default=os.environ.get("OJT_API_URL", "http://localhost:8000"))
    parser.add_argument("--knowledge-dir", default="knowledge")
    parser.add_argument("--scenario", action="append", help="Run only selected scenario ID.")
    parser.add_argument("--bearer-token", default=os.environ.get("OJT_SMOKE_BEARER_TOKEN"))
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    knowledge_root = _resolve_path(args.knowledge_dir)
    plan = load_load_smoke_plan(knowledge_root)
    selected = set(args.scenario or [])
    scenarios = [
        scenario for scenario in plan.scenarios
        if not selected or scenario.scenario_id in selected
    ]
    if selected and len(scenarios) != len(selected):
        found = {scenario.scenario_id for scenario in scenarios}
        missing = ", ".join(sorted(selected - found))
        raise SystemExit(f"Unknown scenario(s): {missing}")

    if args.mode == "asgi":
        os.environ.setdefault("OJT_STORAGE_BACKEND", "memory")
        os.environ.setdefault("OJT_PRODUCT_MODE", "local_dev")
        os.environ.setdefault("OJT_LLM_PROVIDER", "disabled")
        clear_settings_cache()
        clear_workflow_service_cache()
        app = create_app()
        app.dependency_overrides[require_authentication] = authenticated_dependency
        app.dependency_overrides[get_governance_service] = lambda: AllowAllGovernance()
        transport = httpx.ASGITransport(app=app)
        client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    else:
        headers = {}
        if args.bearer_token:
            headers["Authorization"] = f"Bearer {args.bearer_token}"
        client = httpx.AsyncClient(base_url=args.base_url, headers=headers, timeout=30.0)

    started_at = datetime.now(timezone.utc)
    async with client:
        results = [await _run_scenario(client, scenario) for scenario in scenarios]
    completed_at = datetime.now(timezone.utc)
    report = LoadSmokeReport(
        report_id=f"load_smoke_{int(started_at.timestamp())}",
        started_at=started_at.isoformat(),
        completed_at=completed_at.isoformat(),
        base_url=args.base_url if args.mode == "http" else "asgi://testserver",
        mode=args.mode,
        scenario_results=results,
        passed=all(result.passed for result in results),
        warnings=list(plan.warnings),
    )

    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(_format_report(report))
    return 0 if report.passed else 1


async def _run_scenario(
    client: httpx.AsyncClient,
    scenario: LoadSmokeScenario,
) -> LoadSmokeScenarioResult:
    timings: list[float] = []
    error_count = 0
    warnings: list[str] = []
    total = scenario.warmup_requests + scenario.repetitions
    for index in range(total):
        is_warmup = index < scenario.warmup_requests
        started = time.perf_counter()
        status = 0
        try:
            status = await _execute_request(client, scenario)
        except Exception as exc:  # pragma: no cover - failure path is report behavior.
            error_count += 0 if is_warmup else 1
            warnings.append(f"request exception: {type(exc).__name__}")
            continue
        elapsed_ms = (time.perf_counter() - started) * 1000
        if is_warmup:
            continue
        timings.append(elapsed_ms)
        if status != scenario.expected_status:
            error_count += 1
            warnings.append(f"expected status {scenario.expected_status}, got {status}")

    request_count = len(timings)
    error_ratio = error_count / request_count if request_count else 1.0
    p95 = _percentile(timings, 95)
    passed = (
        request_count == scenario.repetitions
        and error_ratio <= scenario.max_error_ratio
        and p95 <= scenario.max_p95_ms
    )
    if p95 > scenario.max_p95_ms:
        warnings.append(
            f"p95 {p95:.1f} ms exceeded budget {scenario.max_p95_ms:.1f} ms"
        )
    return LoadSmokeScenarioResult(
        scenario_id=scenario.scenario_id,
        surface=scenario.surface,
        request_count=request_count,
        error_count=error_count,
        error_ratio=round(error_ratio, 4),
        min_ms=round(min(timings) if timings else 0.0, 2),
        mean_ms=round(statistics.fmean(timings) if timings else 0.0, 2),
        p50_ms=round(_percentile(timings, 50), 2),
        p95_ms=round(p95, 2),
        max_ms=round(max(timings) if timings else 0.0, 2),
        passed=passed,
        warnings=_dedupe(warnings),
    )


async def _execute_request(client: httpx.AsyncClient, scenario: LoadSmokeScenario) -> int:
    if scenario.scenario_id == "workflow_create":
        response = await client.post(scenario.path, json=_workflow_payload())
        return response.status_code
    if scenario.scenario_id == "retrieval_search":
        response = await client.post(scenario.path, json=_retrieval_payload())
        return response.status_code
    if scenario.scenario_id == "assistant_stream":
        async with client.stream("POST", scenario.path, json=_assistant_payload()) as response:
            async for chunk in response.aiter_text():
                if chunk:
                    break
            return response.status_code
    if scenario.scenario_id == "upload_parse":
        response = await client.post(
            scenario.path,
            data={"extractor": "auto", "execute_now": "true"},
            files={"file": ("smoke.csv", _csv_bytes(), "text/csv")},
        )
        return response.status_code
    if scenario.scenario_id == "reindex":
        response = await client.post(
            scenario.path,
            json={"include_seeded": True, "include_corpus": False, "execute_now": True},
        )
        return response.status_code
    if scenario.method.upper() == "GET":
        response = await client.get(scenario.path)
        return response.status_code
    response = await client.request(scenario.method.upper(), scenario.path)
    return response.status_code


def _workflow_payload() -> dict[str, Any]:
    return {
        "instruction": "Performance smoke: validate lab CSV and build output.",
        "data": _csv_text(),
        "input_format": "csv",
        "target_format": "json",
        "schema_id": "lab_result_v1",
        "require_human_review": False,
    }


def _retrieval_payload() -> dict[str, Any]:
    return {
        "query": "HbA1c lab result unit FHIR Observation UCUM",
        "top_k": 5,
        "schema_id": "lab_result_v1",
        "fields": ["lab_name", "value", "unit"],
        "clinical_domain": "laboratory",
        "trust_level": "approved",
    }


def _assistant_payload() -> dict[str, Any]:
    return {
        "message": "Validate this lab CSV and explain issues with trusted evidence.",
        "context": {
            "data": _csv_text(),
            "input_format": "csv",
            "schema_id": "lab_result_v1",
            "clinical_domain": "laboratory",
        },
        "execute_write_actions": False,
    }


def _csv_text() -> str:
    return "date,patient_id,lab_name,value,unit\n2026-01-01,P001,HbA1c,7.4,%\n"


def _csv_bytes() -> bytes:
    return _csv_text().encode("utf-8")


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (percentile / 100)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _format_report(report: LoadSmokeReport) -> str:
    lines = [
        "OJTFlow performance smoke",
        f"  mode: {report.mode}",
        f"  base_url: {report.base_url}",
        f"  passed: {report.passed}",
        "",
        "Scenarios",
    ]
    for result in report.scenario_results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(
            "  "
            f"{status} {result.scenario_id}: "
            f"requests={result.request_count}, errors={result.error_count}, "
            f"p50={result.p50_ms:.1f}ms, p95={result.p95_ms:.1f}ms, "
            f"max={result.max_ms:.1f}ms"
        )
        for warning in result.warnings:
            lines.append(f"    warning: {warning}")
    if report.warnings:
        lines.append("")
        lines.append("Plan warnings")
        for warning in report.warnings:
            lines.append(f"  - {warning}")
    return "\n".join(lines)


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
