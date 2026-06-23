"""Queue-backed OCR worker regression and live smoke tests.

These tests are deliberately not accuracy claims.  The local tests cover
deployment/configuration contracts.  The live smoke test requires the real
RabbitMQ/Celery/Postgres/API stack and verifies that a queued OCR job persists
the actual extracted text from a noisy scanned PDF.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx
import pytest

from ojtflow.application.background_job_service import BackgroundJobService
from ojtflow.application.document_intake_service import DocumentIntakeService
from ojtflow.config import clear_settings_cache, get_settings
from ojtflow.data_tools.extract import Extractor
from ojtflow.infrastructure.extraction.document import LocalDocumentExtractor
from ojtflow.infrastructure.storage.in_memory import (
    InMemoryBackgroundJobRepository,
    InMemoryDatasetStore,
    InMemoryUploadedArtifactRepository,
)

from test_real_gpu_api_smoke import (
    _add_scan_noise,
    _assert_exact_diabetes_visit_facts,
    _diabetes_visit_png_bytes,
    _draw_text_rgb,
    _json,
    _load_dotenv_defaults,
    _normalized_upper_text,
    _pdf_from_rgb_image,
    _render_diabetes_visit_summary_rgb,
    _rotate_rgb,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
API_BASE_URL = os.getenv("OJT_REAL_SMOKE_API_BASE_URL", "http://127.0.0.1:18000").rstrip(
    "/"
)
FLOWER_BASE_URL = os.getenv("OJT_REAL_SMOKE_FLOWER_BASE_URL", "http://127.0.0.1:15555").rstrip(
    "/"
)
PROMETHEUS_BASE_URL = os.getenv(
    "OJT_REAL_SMOKE_PROMETHEUS_BASE_URL",
    "http://127.0.0.1:19090",
).rstrip("/")
HTTP_TIMEOUT_SECONDS = float(os.getenv("OJT_REAL_SMOKE_TIMEOUT_SECONDS", "90"))
QUEUE_TIMEOUT_SECONDS = float(os.getenv("OJT_REAL_QUEUE_SMOKE_TIMEOUT_SECONDS", "240"))
POLL_INTERVAL_SECONDS = float(os.getenv("OJT_REAL_QUEUE_SMOKE_POLL_INTERVAL_SECONDS", "2"))


def _load_smoke_env_defaults() -> None:
    _load_dotenv_defaults()
    smoke_env = REPO_ROOT / ".env.smoke.local"
    if smoke_env.exists():
        for raw_line in smoke_env.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_admin_auth_token()}"}


def _admin_auth_token() -> str:
    token = os.getenv("OJT_QUEUE_SMOKE_ADMIN_AUTH_TOKEN", "").strip()
    if token:
        return token
    _load_smoke_env_defaults()

    from ojtflow.core.contracts.auth import GoogleIdentityProfile
    from ojtflow.interfaces.api.deps import (
        _build_auth_service,
        _build_governance_service,
    )

    auth = _build_auth_service()
    governance = _build_governance_service()
    owner = auth.repository.upsert_google_user(
        GoogleIdentityProfile(
            google_sub="local-queue-smoke-owner",
            email="local-queue-smoke-owner@ojtflow.local",
            email_verified=True,
            display_name="Local Queue Smoke Owner",
        )
    )
    workspace = governance.get_or_create_current_workspace(owner)
    role_key = "admin"
    slug = "queue-smoke-admin"
    account = next(
        (
            candidate
            for candidate in auth.list_service_accounts(
                organization_id=workspace.organization.organization_id
            )
            if candidate.slug == slug
        ),
        None,
    )
    if account is None:
        account = auth.create_service_account_identity(
            organization_id=workspace.organization.organization_id,
            slug=slug,
            display_name="Queue Smoke Admin Service Account",
            role_key=role_key,
            created_by_user_id=owner.user_id,
        )
    try:
        governance.add_organization_member(
            user=owner,
            organization_id=workspace.organization.organization_id,
            member_user_id=account.user_id,
            role_key=role_key,
        )
    except Exception as exc:
        message = str(exc).lower()
        if (
            "unique" not in message
            and "duplicate" not in message
            and "already exists" not in message
        ):
            raise
    issued = auth.issue_service_account_token(service_account=account)
    access_token = str(issued["access_token"])
    assert access_token.startswith("ojt_sa_")
    return access_token


def _queue_smoke_pdf_bytes() -> bytes:
    """Build a noisy rotated scanned PDF with a queue-specific visible marker."""

    width, height, pixels = _render_diabetes_visit_summary_rgb()
    mutable = bytearray(pixels)
    _draw_text_rgb(mutable, width, height, 1180, 690, "FHIR OBS", scale=5)
    rotated_width, rotated_height, rotated_pixels = _rotate_rgb(
        width,
        height,
        bytes(mutable),
        degrees=-3.5,
    )
    noisy_pixels = _add_scan_noise(rotated_width, rotated_height, rotated_pixels)
    return _pdf_from_rgb_image(rotated_width, rotated_height, noisy_pixels)


def _assert_queue_ocr_truth(text: str) -> None:
    _assert_exact_diabetes_visit_facts(text)
    normalized = _normalized_upper_text(text)
    assert "FHIR OBS" in normalized, text
    assert "HBA1C" in normalized and "7 4" in normalized and "%" in normalized, text
    assert "NO OCR TEXT WAS FOUND" not in normalized, text


def _poll_job(client: httpx.Client, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + QUEUE_TIMEOUT_SECONDS
    last_payload: dict[str, Any] | None = None
    last_transport_error: str | None = None
    while time.monotonic() < deadline:
        try:
            response = client.get(f"/api/v1/jobs/{job_id}", headers=_admin_headers())
        except httpx.TransportError as exc:
            last_transport_error = repr(exc)
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        assert response.status_code == 200, response.text
        payload = _json(response)["data"]
        last_payload = payload
        if payload["status"] in {"succeeded", "failed", "cancelled"}:
            return payload
        time.sleep(POLL_INTERVAL_SECONDS)
    pytest.fail(
        f"job {job_id} did not reach a terminal status: "
        f"last_payload={last_payload} last_transport_error={last_transport_error}"
    )


def _read_text_storage_ref(storage_ref: str) -> str:
    parsed = urlparse(storage_ref)
    assert parsed.scheme == "file", storage_ref
    path = Path(unquote(parsed.path))
    if path.exists():
        return path.read_text(encoding="utf-8")

    container_read = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "api",
            "python",
            "-c",
            (
                "from pathlib import Path; import sys; "
                "sys.stdout.write(Path(sys.argv[1]).read_text(encoding='utf-8'))"
            ),
            str(path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert container_read.returncode == 0, (
        f"could not read OCR text storage ref {storage_ref}; "
        f"stdout={container_read.stdout!r} stderr={container_read.stderr!r}"
    )
    return container_read.stdout


def _readiness_job_check(payload: dict[str, Any]) -> dict[str, Any]:
    checks = payload["data"]["checks"]
    return next(check for check in checks if check["name"] == "job_repository")


def _prometheus_target_health() -> dict[str, str]:
    with httpx.Client(base_url=PROMETHEUS_BASE_URL, timeout=HTTP_TIMEOUT_SECONDS) as client:
        response = client.get("/api/v1/targets")
    assert response.status_code == 200, response.text
    payload = response.json()
    active_targets = payload["data"]["activeTargets"]
    return {target["labels"]["job"]: target["health"] for target in active_targets}


def _rabbitmq_ocr_queue_state() -> dict[str, str]:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "rabbitmq",
            "rabbitmqctl",
            "list_queues",
            "name",
            "messages_ready",
            "messages_unacknowledged",
            "consumers",
            "durable",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    lines = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
        and not line.startswith("Timeout:")
        and not line.startswith("Listing queues")
    ]
    assert lines, result.stdout
    header = lines[0].split("\t")
    for row in lines[1:]:
        values = row.split("\t")
        state = dict(zip(header, values, strict=True))
        if state.get("name") == "ocr":
            return state
    pytest.fail(f"RabbitMQ durable OCR queue was not found: {result.stdout}")


def test_pilot_and_production_settings_reject_missing_rabbitmq_queue_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for mode in ("pilot", "production"):
        monkeypatch.setenv("OJT_PRODUCT_MODE", mode)
        monkeypatch.setenv("OJT_STORAGE_BACKEND", "postgres")
        monkeypatch.setenv("OJT_EMBEDDING_PROVIDER", "openai")
        monkeypatch.setenv("OJT_EMBEDDING_MODEL", "text-embedding-3-small")
        monkeypatch.setenv("OJT_OPENAI_API_KEY", "sk-test-config-only")
        monkeypatch.setenv("OJT_LLM_PROVIDER", "openai")
        monkeypatch.setenv("OJT_LLM_MODEL", "gpt-5-mini")
        monkeypatch.delenv("OJT_QUEUE_BACKEND", raising=False)
        clear_settings_cache()

        with pytest.raises(ValueError, match="OJT_QUEUE_BACKEND=rabbitmq"):
            get_settings()

    clear_settings_cache()


def test_docker_compose_config_is_valid_with_queue_and_monitoring_stack() -> None:
    result = subprocess.run(
        ["docker", "compose", "config", "--quiet"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_openai_vision_parse_failure_records_structured_job_error_without_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _load_smoke_env_defaults()
    monkeypatch.setenv("OJT_OPENAI_API_KEY", "sk-invalid-queue-ocr-failure-test")
    monkeypatch.setenv("OJT_LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("OJT_LLM_VISION_MODEL", "gpt-4.1-mini")
    clear_settings_cache()

    intake = DocumentIntakeService(
        artifacts=InMemoryUploadedArtifactRepository(),
        datasets=InMemoryDatasetStore(),
        jobs=BackgroundJobService(InMemoryBackgroundJobRepository()),
        extractor=LocalDocumentExtractor(),
    )
    artifact = intake.register_upload(
        owner_user_id="usr_queue_failure",
        filename="openai-vision-failure.png",
        mime_type="image/png",
        data=_diabetes_visit_png_bytes(),
    )
    job = intake.create_parse_job(
        owner_user_id="usr_queue_failure",
        artifact_id=artifact.artifact_id,
        prefer_extractor=Extractor.OPENAI_VISION,
        execute_now=False,
    )
    failed = intake.jobs.run_sync(
        owner_user_id="usr_queue_failure",
        job_id=job.job_id,
        handler=intake._run_parse_job,
    )

    assert failed.status == "failed"
    assert failed.error is not None
    assert failed.error.code == "job_execution_failed"
    assert failed.error.details["error_type"] in {
        "ToolExecutionError",
        "DependencyUnavailableError",
    }
    assert failed.output == {}
    assert intake.list_traces(
        owner_user_id="usr_queue_failure",
        artifact_id=artifact.artifact_id,
    ) == []
    clear_settings_cache()


def test_live_runtime_readiness_reports_queue_backed_when_rabbitmq_configured() -> None:
    _load_smoke_env_defaults()
    with httpx.Client(base_url=API_BASE_URL, timeout=HTTP_TIMEOUT_SECONDS) as client:
        health = client.get("/health")
        assert health.status_code == 200, health.text

        readiness = client.get("/api/v1/runtime/readiness", headers=_admin_headers())
        assert readiness.status_code == 200, readiness.text
        readiness_payload = _json(readiness)
        job_check = _readiness_job_check(readiness_payload)
        assert job_check["details"]["queue_backed"] is True, job_check
        assert job_check["details"]["runner_mode"] == "rabbitmq_celery", job_check


def test_live_rabbitmq_ocr_queue_has_a_real_worker_consumer() -> None:
    queue_state = _rabbitmq_ocr_queue_state()
    assert queue_state["durable"] == "true", queue_state
    assert int(queue_state["consumers"]) >= 1, queue_state


def _run_queue_ocr_job() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], str]:
    pdf_bytes = _queue_smoke_pdf_bytes()
    with httpx.Client(base_url=API_BASE_URL, timeout=HTTP_TIMEOUT_SECONDS) as client:
        health = client.get("/health")
        assert health.status_code == 200, health.text

        response = client.post(
            "/api/v1/parse/extract",
            headers=_admin_headers(),
            data={"extractor": "auto"},
            files={
                "file": (
                    "queue-smoke-scanned-diabetes-followup-fhir-obs.pdf",
                    pdf_bytes,
                    "application/pdf",
                )
            },
        )
        assert response.status_code == 202, response.text
        queued_payload = _json(response)
        queued = queued_payload["data"]
        job = queued["job"]
        artifact = queued["artifact"]

        assert queued_payload["meta"]["status"] == "queued"
        assert queued_payload["meta"]["poll"] == f"/api/v1/jobs/{job['job_id']}"
        assert job["job_type"] == "file_parse"
        assert job["status"] == "queued"
        assert job["job_id"].startswith("job_")
        assert artifact["filename"] == "queue-smoke-scanned-diabetes-followup-fhir-obs.pdf"

        initial_poll = client.get(
            f"/api/v1/jobs/{job['job_id']}",
            headers=_admin_headers(),
        )
        assert initial_poll.status_code == 200, initial_poll.text
        initial_job = _json(initial_poll)["data"]
        assert initial_job["job_id"] == job["job_id"]
        assert initial_job["status"] in {"queued", "running", "succeeded"}

        terminal = _poll_job(client, job["job_id"])

        metrics = client.get("/metrics")
        assert metrics.status_code == 200, metrics.text
        assert "text/plain" in metrics.headers["content-type"]
        assert "ojtflow_api_requests_total" in metrics.text
        assert 'path="/api/v1/jobs/{job_id}"' in metrics.text

        traces_response = client.get(
            f"/api/v1/parse/artifacts/{artifact['artifact_id']}/traces",
            headers=_admin_headers(),
        )
        assert traces_response.status_code == 200, traces_response.text
        persisted_traces = _json(traces_response)["data"]

    return terminal, artifact, persisted_traces, job["job_id"]


def test_live_parse_extract_pdf_returns_202_and_worker_persists_openai_vision_text() -> None:
    _load_smoke_env_defaults()
    terminal, artifact, persisted_traces, job_id = _run_queue_ocr_job()

    assert terminal["status"] == "succeeded", terminal
    assert terminal["error"] is None
    assert terminal["attempts"] >= 1
    assert terminal["completed_at"]
    assert terminal["progress"]["message"] == "Completed."

    output = terminal["output"]
    trace = output["trace"]
    assert output["artifact"]["artifact_id"] == artifact["artifact_id"]
    assert trace["job_id"] == job_id
    assert trace["artifact_id"] == artifact["artifact_id"]
    assert trace["source_format"] == "pdf"
    assert trace["extractor_chosen"] == "openai_vision"
    assert trace["char_count"] > 100
    assert trace["text_storage_ref"]
    assert trace["steps"][0]["status"] == "succeeded"
    assert trace["steps"][0]["extractor"] == "openai_vision"
    assert trace["steps"][0]["metadata"]["extraction"]["provider"] == "openai"
    assert trace["metadata"]["extraction"]["provider"] == "openai"
    assert trace["metadata"]["extraction"]["source_format_original"] == "pdf"
    assert persisted_traces and persisted_traces[0]["trace_id"] == trace["trace_id"]

    extracted_text = _read_text_storage_ref(trace["text_storage_ref"])
    _assert_queue_ocr_truth(extracted_text)

    with httpx.Client(base_url=FLOWER_BASE_URL, timeout=HTTP_TIMEOUT_SECONDS) as client:
        tasks_response = client.get("/api/tasks")
    assert tasks_response.status_code == 200, tasks_response.text
    assert job_id in tasks_response.text


def test_live_prometheus_scrapes_api_rabbitmq_and_celery_targets() -> None:
    target_health = _prometheus_target_health()
    assert target_health.get("ojtflow-api") == "up", target_health
    assert target_health.get("rabbitmq") == "up", target_health
    assert target_health.get("celery") == "up", target_health
