from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_CREDENTIAL_IGNORE_PATTERNS = {
    "credentials/",
    "secrets/",
    ".gcloud/",
    ".config/gcloud/",
    "credentials.json",
    "token.json",
    "oauth-token.json",
    "application_default_credentials.json",
    "adc.json",
    "gcloud_adc.json",
    "google-oauth-client.json",
    "client_secret*.json",
    "service-account*.json",
    "*service-account*.json",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
}


def _git_lines(*args: str) -> list[str]:
    output = subprocess.check_output(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
    )
    return [line for line in output.splitlines() if line.strip()]


def test_local_secret_and_runtime_paths_are_ignored() -> None:
    paths = [
        ".env",
        ".env.local",
        ".config/gcloud/application_default_credentials.json",
        ".gcloud/application_default_credentials.json",
        "adc.json",
        "application_default_credentials.json",
        "client_secret_123.apps.googleusercontent.com.json",
        "credentials/google-oauth-client.json",
        "credentials.json",
        "gcloud_adc.json",
        "google-oauth-client.json",
        "image.png",
        "oauth-token.json",
        "var/ojtflow.db",
        "var/ui-audit/workflows-load-desktop.png",
        "plan/generated.md",
        "plan/retrieval_healthcare_blueprint/index.md",
        "secrets/service-account.json",
        "service-account-prod.json",
        "service-account.key",
        "service-account.pem",
        "token.json",
        "src/ojtflow.egg-info/PKG-INFO",
        "frontend/node_modules/.package-lock.json",
        "frontend/var/final-detail-evidence-mobile.png",
        "frontend/test-results/report.json",
        "frontend/playwright-report/index.html",
        "frontend/.auth/user.json",
        "frontend/tsconfig.tsbuildinfo",
        "frontend/vite.config.js",
        "latex/main.aux",
        "submit/OJTFlow_short_proposal.log",
        "texput.log",
        "src/ojtflow/__pycache__/config.cpython-312.pyc",
    ]

    ignored = set(_git_lines("check-ignore", *paths))

    assert set(paths) <= ignored


def test_plan_directory_is_not_tracked() -> None:
    assert _git_lines("ls-files", "plan") == []


def test_generated_artifacts_are_not_visible_to_git() -> None:
    files = _git_lines("ls-files", "--cached", "--others", "--exclude-standard")
    generated_patterns = [
        re.compile(r"^plan/"),
        re.compile(r"^var/"),
        re.compile(r"^image\.png$"),
        re.compile(r"(^|/)__pycache__/"),
        re.compile(r"\.py[co]$"),
        re.compile(r"^\.pytest_cache/"),
        re.compile(r"^src/ojtflow\.egg-info/"),
        re.compile(r"^frontend/node_modules/"),
        re.compile(r"^frontend/dist/"),
        re.compile(r"^frontend/var/"),
        re.compile(r"^frontend/playwright-report/"),
        re.compile(r"^frontend/test-results/"),
        re.compile(r"^frontend/\.auth/"),
        re.compile(r"^frontend/.*\.tsbuildinfo$"),
        re.compile(r"^frontend/vite\.config\.(js|d\.ts)$"),
        re.compile(r"^(latex|submit)/.*\.(aux|log|out|toc)$"),
        re.compile(r"^texput\.log$"),
    ]
    findings = [
        relative_path
        for relative_path in files
        if any(pattern.search(relative_path) for pattern in generated_patterns)
    ]

    assert findings == []


def test_docker_build_contexts_exclude_cloud_credentials() -> None:
    for ignore_file in [REPO_ROOT / ".dockerignore", REPO_ROOT / "frontend/.dockerignore"]:
        patterns = {
            line.strip()
            for line in ignore_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        assert SENSITIVE_CREDENTIAL_IGNORE_PATTERNS <= patterns


def test_local_visual_audit_outputs_are_not_visible_to_git() -> None:
    files = _git_lines("ls-files", "--cached", "--others", "--exclude-standard")
    visual_artifact_patterns = [
        re.compile(r"^var/(screenshots|ui-[^/]+)/"),
        re.compile(r"^frontend/var/"),
        re.compile(r"^frontend/playwright-report/"),
        re.compile(r"^frontend/test-results/"),
    ]
    findings = [
        relative_path
        for relative_path in files
        if any(pattern.search(relative_path) for pattern in visual_artifact_patterns)
    ]

    assert findings == []


def test_source_tree_does_not_contain_committable_google_oauth_secrets() -> None:
    files = _git_lines("ls-files", "--cached", "--others", "--exclude-standard")
    google_secret_prefix = "GOC" + "SPX-"
    secret_patterns = [
        re.compile(rf"{google_secret_prefix}[A-Za-z0-9_-]{{20,}}"),
        re.compile(r'"client_secret"\s*:\s*"[^"$][^"]{8,}"'),
        re.compile(r"(?m)^OJT_GOOGLE_CLIENT_SECRET[ \t]*=[ \t]*[^$\s.][^\r\n\s]{8,}"),
        re.compile(r"(?m)^OJT_GOOGLE_CLIENT_ID[ \t]*=[ \t]*\d+[-][^\r\n\s]+\.apps\.googleusercontent\.com"),
    ]
    findings: list[str] = []

    for relative_path in files:
        path = REPO_ROOT / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in secret_patterns:
            if pattern.search(content):
                findings.append(relative_path)
                break

    assert findings == []


def test_source_tree_does_not_contain_committable_private_keys_or_api_tokens() -> None:
    files = _git_lines("ls-files", "--cached", "--others", "--exclude-standard")
    secret_patterns = [
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"AIza[0-9A-Za-z_-]{35}"),
        re.compile(r"ya29\.[0-9A-Za-z_-]{20,}"),
        re.compile(r"xox[baprs]-[0-9A-Za-z-]{20,}"),
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
    ]
    findings: list[str] = []

    for relative_path in files:
        path = REPO_ROOT / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in secret_patterns:
            if pattern.search(content):
                findings.append(relative_path)
                break

    assert findings == []


def test_docs_and_source_do_not_contain_local_machine_paths() -> None:
    files = _git_lines("ls-files", "--cached", "--others", "--exclude-standard")
    local_home = "/home/" + "tcuong1000"
    local_venv_marker = "." + "ostwin"
    forbidden_patterns = [
        re.compile(rf"{re.escape(local_home)}\b"),
        re.compile(rf"{re.escape(local_venv_marker)}\b"),
    ]
    checked_roots = (
        "docs/",
        "frontend/",
        "src/",
        "tests/",
        "README.md",
        "RELEASE_CANDIDATE.md",
        "pyproject.toml",
        "docker-compose.yml",
    )
    ignored_roots = (
        "frontend/node_modules/",
        "frontend/dist/",
        "frontend/playwright-report/",
        "frontend/test-results/",
    )
    findings: list[str] = []

    for relative_path in files:
        if not relative_path.startswith(checked_roots):
            continue
        if relative_path.startswith(ignored_roots):
            continue
        path = REPO_ROOT / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden_patterns:
            if pattern.search(content):
                findings.append(relative_path)
                break

    assert findings == []


def test_readme_architecture_tree_matches_repo_boundaries() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "src/ojtflow/" in readme
    assert "  medical/          OCR/DICOM/visual evidence extension contracts" in readme
    assert "  mcp_servers/      planned MCP wrapper boundary" in readme
    assert "frontend/\n  src/              React product UI and API client" in readme
    assert "frontend/\n  src/              React product UI and API client\n  medical/" not in readme
    assert "frontend/\n  src/              React product UI and API client\n  mcp_servers/" not in readme


def test_readme_documents_release_gate_and_evidence_docs() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    required_phrases = [
        "docs/testing_strategy.md",
        "RELEASE_CANDIDATE.md",
        "docs/release_verification_matrix.md",
        "PYTHON_BIN=python scripts/release-check.sh",
        "Docker stack rebuild",
        "runtime",
        "browser E2E",
        "Postgres residue assertion",
        "git whitespace hygiene",
        "OJT_RELEASE_CHECK_SKIP_DOCKER_BUILD=1",
        "OJT_RELEASE_CHECK_SKIP_E2E=1",
    ]

    for phrase in required_phrases:
        assert phrase in readme


def test_release_candidate_checklist_matches_current_release_gate() -> None:
    checklist = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")

    required_phrases = [
        "PYTHON_BIN=python scripts/release-check.sh",
        "docs/release_verification_matrix.md",
        "Browser Playwright E2E suite",
        "Runtime frontend asset freshness check",
        "Postgres residue assertion",
        "All protected API routes require an authenticated backend session",
        "Workflow, review, event, summary, stats, retrieval-with-workflow, and output",
        "FHIR-like profiling",
        "OCR evidence endpoint",
        "Graph-NER/RAG remains a handoff contract in v0",
        "Google OAuth, ADC, service-account, key, and certificate filenames",
        "`plan/` is ignored and not tracked as source",
    ]

    for phrase in required_phrases:
        assert phrase in checklist


def test_release_gate_checks_staged_and_unstaged_diff_hygiene() -> None:
    script = (REPO_ROOT / "scripts/release-check.sh").read_text(encoding="utf-8")
    matrix = (REPO_ROOT / "docs/release_verification_matrix.md").read_text(
        encoding="utf-8",
    )
    testing = (REPO_ROOT / "docs/testing_strategy.md").read_text(encoding="utf-8")

    assert "assert_git_diff_hygiene" in script
    assert "git diff --check" in script
    assert "git diff --cached --check" in script
    assert "git diff --cached --check" in matrix
    assert "git diff --cached --check" in testing


def test_passed_release_candidate_checklist_has_no_unchecked_items() -> None:
    checklist = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
    unchecked_items = re.findall(r"(?m)^- \[ \] .+$", checklist)

    assert "Last full local gate: passed" in checklist
    assert unchecked_items == []


def test_release_verification_matrix_maps_checklist_to_evidence() -> None:
    matrix = (REPO_ROOT / "docs/release_verification_matrix.md").read_text(
        encoding="utf-8",
    )
    required_phrases = [
        "scripts/release-check.sh",
        "tests/test_api.py::test_private_api_routes_have_auth_dependency",
        "tests/test_postgres_storage_optional.py::test_postgres_workflow_restart_resume",
        "tests/test_workflow_service.py::test_fhir_like_workflow_adds_profile_evidence_and_handoff_context",
        "tests/test_retrieval.py::test_retrieval_trace_flags_untrusted_query_context",
        "tests/test_frontend_architecture.py::test_frontend_network_calls_stay_behind_api_boundary",
        "frontend/e2e/layout.spec.ts",
        "frontend/e2e/oauth.spec.ts",
        "tests/test_repo_hygiene.py::test_source_tree_does_not_contain_committable_google_oauth_secrets",
        "human consent remains manual",
    ]

    for phrase in required_phrases:
        assert phrase in matrix


def test_release_verification_matrix_mentions_release_script_step_labels() -> None:
    script = (REPO_ROOT / "scripts/release-check.sh").read_text(encoding="utf-8")
    matrix = (REPO_ROOT / "docs/release_verification_matrix.md").read_text(
        encoding="utf-8",
    )
    labels = set(re.findall(r"(?:run_step|run_frontend_step) \"([^\"]+)\"", script))
    labels.add("Browser E2E suite")

    missing = sorted(label for label in labels if label not in matrix)

    assert missing == []


def test_release_verification_matrix_references_existing_tests_and_files() -> None:
    matrix = (REPO_ROOT / "docs/release_verification_matrix.md").read_text(
        encoding="utf-8",
    )
    python_refs = sorted(
        set(
            re.findall(
                r"tests/test_[A-Za-z0-9_]+\.py(?:::test_[A-Za-z0-9_]+)?",
                matrix,
            )
        )
    )
    e2e_refs = sorted(
        set(re.findall(r"frontend/e2e/[A-Za-z0-9_.-]+\.spec\.ts", matrix))
    )
    script_refs = sorted(
        set(
            re.findall(
                r"(?:scripts|frontend/scripts)/[A-Za-z0-9_.-]+\.(?:sh|mjs|js|ts)",
                matrix,
            )
        )
    )
    missing: list[str] = []

    for reference in python_refs:
        file_ref, _, function_name = reference.partition("::")
        path = REPO_ROOT / file_ref
        if not path.is_file():
            missing.append(reference)
            continue
        if function_name:
            source = path.read_text(encoding="utf-8")
            pattern = rf"(?:async\s+)?def\s+{re.escape(function_name)}\s*\("
            if not re.search(pattern, source):
                missing.append(reference)

    for reference in [*e2e_refs, *script_refs]:
        if not (REPO_ROOT / reference).is_file():
            missing.append(reference)

    assert missing == []


def test_release_docs_cover_demo_flow_and_testing_strategy() -> None:
    demo = (REPO_ROOT / "docs/demo_backend_flow.md").read_text(encoding="utf-8")
    testing = (REPO_ROOT / "docs/testing_strategy.md").read_text(encoding="utf-8")

    demo_required = [
        "data/fixtures/structured/lab_results_messy.csv",
        "Clean this CSV, convert it to JSON, and explain anomalies.",
        "require_human_review",
        "Review approval resumes the workflow even after service restart.",
        "GET /api/v1/workflows/{workflow_id}/output",
        "retrieved_context",
        "handoff_context.retrieval_trace",
    ]
    testing_required = [
        "Unit tests",
        "Integration tests",
        "Real-stack smoke tests",
        "Browser E2E tests",
        "scripts/release-check.sh",
        "runtime:assert-current",
        "E2E cleanup",
        "Google OAuth handoff",
    ]

    for phrase in demo_required:
        assert phrase in demo
    for phrase in testing_required:
        assert phrase in testing


def test_playwright_specs_do_not_use_fixed_network_sleeps() -> None:
    files = _git_lines("ls-files", "--cached", "--others", "--exclude-standard", "frontend/e2e")
    forbidden_patterns = [
        re.compile(r"setTimeout\s*\(\s*resolve\s*,\s*\d{3,}"),
        re.compile(r"waitForTimeout\s*\(\s*\d{3,}"),
    ]
    findings: list[str] = []

    for relative_path in files:
        path = REPO_ROOT / relative_path
        if path.suffix not in {".ts", ".tsx"} or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden_patterns:
            if pattern.search(content):
                findings.append(relative_path)
                break

    assert findings == []


def test_application_source_has_no_debug_leftovers() -> None:
    files = _git_lines("ls-files", "--cached", "--others", "--exclude-standard")
    checked_roots = ("src/", "frontend/src/", "frontend/e2e/", "tests/")
    checked_suffixes = {".py", ".ts", ".tsx", ".js", ".mjs"}
    forbidden_patterns = [
        re.compile(r"\bTODO\b"),
        re.compile(r"\bFIXME\b"),
        re.compile(r"\bXXX\b"),
        re.compile(r"\bHACK\b"),
        re.compile(r"\bdebugger\s*;"),
        re.compile(r"\bconsole\.log\s*\("),
        re.compile(r"\bpdb\.set_trace\s*\("),
        re.compile(r"\bbreakpoint\s*\("),
        re.compile(r"raise\s+NotImplementedError\b"),
    ]
    findings: list[str] = []

    for relative_path in files:
        if relative_path == "tests/test_repo_hygiene.py":
            continue
        if not relative_path.startswith(checked_roots):
            continue
        path = REPO_ROOT / relative_path
        if path.suffix not in checked_suffixes or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden_patterns:
            if pattern.search(content):
                findings.append(relative_path)
                break

    assert findings == []
