#!/usr/bin/env python3
"""Smoke-check deployed OJTFlow URLs and print a public URL summary."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ojtflow.infrastructure.operations import load_deployment_smoke_plan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deployed OJTFlow smoke checks.")
    parser.add_argument("--knowledge-dir", default="knowledge")
    parser.add_argument("--frontend-url", default=os.environ.get("OJT_FRONTEND_URL"))
    parser.add_argument("--api-url", default=os.environ.get("OJT_API_URL"))
    parser.add_argument("--public-url", default=os.environ.get("OJT_PUBLIC_URL"))
    parser.add_argument("--bearer-token", default=os.environ.get("OJT_SMOKE_BEARER_TOKEN"))
    parser.add_argument("--cookie", default=os.environ.get("OJT_SMOKE_COOKIE"))
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--allow-missing-auth", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    knowledge_root = _resolve_path(args.knowledge_dir)
    plan = load_deployment_smoke_plan(knowledge_root)
    frontend_url = args.frontend_url or _default_url(plan, "frontend")
    api_url = args.api_url or _default_url(plan, "api_public_health")
    public_url = args.public_url or frontend_url
    frontend_build_version = _frontend_package_version()
    headers = _auth_headers(args.bearer_token, args.cookie)

    results: list[dict] = []
    for target in plan.targets:
        base_url = frontend_url if target.target_id == "frontend" else api_url
        for path in target.required_paths:
            results.append(
                _check_url(
                    base_url=base_url,
                    path=path,
                    required=True,
                    expected_statuses=set(target.expected_statuses),
                    headers=headers,
                    timeout=args.timeout,
                    allow_missing_auth=args.allow_missing_auth,
                )
            )
        for path in target.optional_paths:
            results.append(
                _check_url(
                    base_url=base_url,
                    path=path,
                    required=False,
                    expected_statuses=set(target.expected_statuses),
                    headers=headers,
                    timeout=args.timeout,
                    allow_missing_auth=True,
                )
            )

    passed = all(item["passed"] for item in results if item["required"])
    report = {
        "public_url": public_url,
        "frontend_url": frontend_url,
        "frontend_build_version": frontend_build_version,
        "api_url": api_url,
        "passed": passed,
        "checked_at": int(time.time()),
        "results": results,
        "warnings": list(plan.warnings),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_report(report))
    return 0 if passed else 1


def _check_url(
    *,
    base_url: str,
    path: str,
    required: bool,
    expected_statuses: set[int],
    headers: dict[str, str],
    timeout: float,
    allow_missing_auth: bool,
) -> dict:
    url = urljoin(_with_trailing_slash(base_url), path.lstrip("/"))
    auth_required = path.startswith("/api/v1/")
    if auth_required and not headers and allow_missing_auth:
        return {
            "url": url,
            "path": path,
            "required": required,
            "status": "skipped_missing_auth",
            "http_status": None,
            "passed": not required,
            "elapsed_ms": 0,
        }
    if auth_required and not headers:
        return {
            "url": url,
            "path": path,
            "required": required,
            "status": "missing_auth",
            "http_status": None,
            "passed": False,
            "elapsed_ms": 0,
        }
    started = time.perf_counter()
    try:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            response.read(512)
    except HTTPError as exc:
        status = int(exc.code)
    except URLError as exc:
        return {
            "url": url,
            "path": path,
            "required": required,
            "status": f"network_error:{type(exc.reason).__name__}",
            "http_status": None,
            "passed": False,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return {
        "url": url,
        "path": path,
        "required": required,
        "status": "ok" if status in expected_statuses else "unexpected_status",
        "http_status": status,
        "passed": status in expected_statuses,
        "elapsed_ms": elapsed_ms,
    }


def _auth_headers(bearer_token: str | None, cookie: str | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if cookie:
        headers["Cookie"] = cookie
    return headers


def _default_url(plan, target_id: str) -> str:
    target = next(target for target in plan.targets if target.target_id == target_id)
    return target.default_url


def _frontend_package_version() -> str:
    package_json = REPO_ROOT / "frontend" / "package.json"
    if not package_json.exists():
        return "unknown"
    try:
        raw = json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "unknown"
    version = raw.get("version")
    return str(version).strip() if version else "unknown"


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _with_trailing_slash(value: str) -> str:
    return value if value.endswith("/") else f"{value}/"


def _format_report(report: dict) -> str:
    lines = [
        "OJTFlow deployment smoke",
        f"  Public URL: {report['public_url']}",
        f"  Frontend URL: {report['frontend_url']}",
        f"  Frontend build version: {report['frontend_build_version']}",
        f"  API URL: {report['api_url']}",
        f"  Passed: {report['passed']}",
        "",
        "Checks",
    ]
    for item in report["results"]:
        required = "required" if item["required"] else "optional"
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(
            "  "
            f"{status} {required} {item['path']}: "
            f"{item['status']} "
            f"status={item['http_status']} "
            f"elapsed={item['elapsed_ms']}ms"
        )
    if report["warnings"]:
        lines.append("")
        lines.append("Warnings")
        for warning in report["warnings"]:
            lines.append(f"  - {warning}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
