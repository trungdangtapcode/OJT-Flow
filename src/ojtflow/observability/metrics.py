"""Prometheus metrics helpers."""

from __future__ import annotations

import time

try:
    from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest
except ImportError:  # pragma: no cover - dependency is present in production images
    Counter = None  # type: ignore[assignment]
    Histogram = None  # type: ignore[assignment]
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


if Counter is not None and Histogram is not None:
    API_REQUESTS = Counter(
        "ojtflow_api_requests_total",
        "Total API requests.",
        ("method", "path", "status"),
    )
    API_REQUEST_LATENCY = Histogram(
        "ojtflow_api_request_duration_seconds",
        "API request latency in seconds.",
        ("method", "path"),
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
    )
else:
    API_REQUESTS = None
    API_REQUEST_LATENCY = None


def monotonic_seconds() -> float:
    return time.monotonic()


def observe_api_request(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    if API_REQUESTS is None or API_REQUEST_LATENCY is None:
        return
    route_path = _bounded_path(path)
    API_REQUESTS.labels(method=method, path=route_path, status=str(status_code)).inc()
    API_REQUEST_LATENCY.labels(method=method, path=route_path).observe(duration_seconds)


def metrics_payload() -> tuple[bytes, str]:
    if Counter is None:
        return b"ojtflow_metrics_available 0\n", CONTENT_TYPE_LATEST
    return generate_latest(), CONTENT_TYPE_LATEST


def _bounded_path(path: str) -> str:
    if path.startswith("/api/v1/jobs/"):
        return "/api/v1/jobs/{job_id}"
    if path.startswith("/api/v1/parse/artifacts/"):
        return "/api/v1/parse/artifacts/{artifact_id}"
    if path.startswith("/api/v1/workflows/"):
        return "/api/v1/workflows/{workflow_id}"
    return path[:160]

