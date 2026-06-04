import json
import re
from pathlib import Path

from fastapi.routing import APIRoute

from ojtflow.interfaces.api.app import create_app


REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_DIR = REPO_ROOT / "frontend" / "src" / "features"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
FRONTEND_E2E = REPO_ROOT / "frontend" / "e2e"
IMPORT_RE = re.compile(r"""from\s+["']([^"']+)["']""")
FETCH_RE = re.compile(r"\bfetch\s*\(")
BROWSER_STORAGE_RE = re.compile(r"\b(localStorage|sessionStorage|document\.cookie)\b")
FULL_PAGE_RELOAD_RE = re.compile(r"\b(?:window\.)?location\.reload\s*\(")
PLAYWRIGHT_CONTEXT_POST_RE = re.compile(r"context\.request\.post\s*\(")
CLEANUP_SCRIPT = REPO_ROOT / "frontend" / "scripts" / "cleanup-e2e-artifacts.mjs"
LOCAL_CLEANUP_SCRIPT = (
    REPO_ROOT / "frontend" / "scripts" / "cleanup-e2e-local-artifacts.mjs"
)
PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"
RELEASE_CHECK = REPO_ROOT / "scripts" / "release-check.sh"
AUTH_PROVIDER = REPO_ROOT / "frontend" / "src" / "app" / "auth.tsx"
APP_PROVIDERS = REPO_ROOT / "frontend" / "src" / "app" / "providers.tsx"
ERROR_BOUNDARY = REPO_ROOT / "frontend" / "src" / "app" / "error-boundary.tsx"
API_MODULE = REPO_ROOT / "frontend" / "src" / "api.ts"
APP_SHELL = REPO_ROOT / "frontend" / "src" / "components" / "layout" / "app-shell.tsx"
FRONTEND_TYPES = REPO_ROOT / "frontend" / "src" / "types.ts"
WORKFLOW_DETAIL = (
    REPO_ROOT / "frontend" / "src" / "features" / "workflows" / "workflow-detail.tsx"
)
WORKFLOW_DETAIL_SPLIT_FILES = [
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "workflows"
    / "workflow-detail-chrome.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "workflows"
    / "workflow-detail-review.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "workflows"
    / "workflow-detail-sections.tsx",
]
WORKBENCH_PAGE = (
    REPO_ROOT / "frontend" / "src" / "features" / "workbench" / "workbench-page.tsx"
)
RETRIEVAL_PAGE = (
    REPO_ROOT / "frontend" / "src" / "features" / "retrieval" / "retrieval-page.tsx"
)
SETTINGS_PAGE = (
    REPO_ROOT / "frontend" / "src" / "features" / "settings" / "settings-page.tsx"
)
WORKBENCH_SPLIT_FILES = [
    REPO_ROOT / "frontend" / "src" / "features" / "workbench" / "workbench-controls.tsx",
    REPO_ROOT / "frontend" / "src" / "features" / "workbench" / "workbench-examples.ts",
    REPO_ROOT / "frontend" / "src" / "features" / "workbench" / "workbench-utils.ts",
]
FRONTEND_API_CALL_RE = re.compile(
    r"\b(?P<fn>request|fetchApi)(?:<[^>]+>)?\(\s*(?P<quote>[`\"])(?P<path>[^`\"]*/[^`\"]*)(?P=quote)"
)


def _frontend_source_files() -> list[Path]:
    return sorted(path for path in FRONTEND_SRC.rglob("*") if path.suffix in {".ts", ".tsx"})


def test_frontend_features_do_not_import_other_features() -> None:
    violations: list[str] = []

    for source_file in sorted(
        path for path in FEATURES_DIR.rglob("*") if path.suffix in {".ts", ".tsx"}
    ):
        current_feature = source_file.relative_to(FEATURES_DIR).parts[0]
        text = source_file.read_text(encoding="utf-8")
        for specifier in IMPORT_RE.findall(text):
            if not specifier.startswith("."):
                continue

            imported_path = (source_file.parent / specifier).resolve()
            try:
                relative_import = imported_path.relative_to(FEATURES_DIR)
            except ValueError:
                continue

            imported_feature = relative_import.parts[0]
            if imported_feature != current_feature:
                violations.append(
                    f"{source_file.relative_to(REPO_ROOT)} imports {specifier!r} from feature {imported_feature!r}",
                )

    assert violations == []


def test_frontend_network_calls_stay_behind_api_boundary() -> None:
    violations: list[str] = []
    allowed_fetch_file = FRONTEND_SRC / "api.ts"

    for source_file in _frontend_source_files():
        if source_file == allowed_fetch_file:
            continue

        text = source_file.read_text(encoding="utf-8")
        if FETCH_RE.search(text):
            violations.append(
                f"{source_file.relative_to(REPO_ROOT)} calls fetch outside src/api.ts",
            )

    assert violations == []


def test_frontend_features_use_server_state_boundary() -> None:
    violations: list[str] = []

    for source_file in sorted(
        path for path in FEATURES_DIR.rglob("*") if path.suffix in {".ts", ".tsx"}
    ):
        text = source_file.read_text(encoding="utf-8")
        for specifier in IMPORT_RE.findall(text):
            if specifier.endswith("/api") or specifier in {"../../api", "../api"}:
                violations.append(
                    f"{source_file.relative_to(REPO_ROOT)} imports API module directly",
                )

    assert violations == []


def test_workflow_detail_shell_stays_split_by_responsibility() -> None:
    workflow_detail = WORKFLOW_DETAIL.read_text(encoding="utf-8")

    assert len(workflow_detail.splitlines()) <= 240
    assert "useWorkflowQuery" in workflow_detail
    assert "useWorkflowEventsQuery" in workflow_detail
    assert "useReviewDecisionMutation" in workflow_detail
    assert "useWorkflowOutputQuery" not in workflow_detail
    assert "navigator.clipboard" not in workflow_detail
    assert "toast." not in workflow_detail
    assert "<Table" not in workflow_detail
    for split_file in WORKFLOW_DETAIL_SPLIT_FILES:
        assert split_file.exists()

    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )
    for split_file in [WORKFLOW_DETAIL, *WORKFLOW_DETAIL_SPLIT_FILES]:
        assert split_file.name in frontend_architecture


def test_workbench_shell_stays_split_by_responsibility() -> None:
    workbench_page = WORKBENCH_PAGE.read_text(encoding="utf-8")

    assert len(workbench_page.splitlines()) <= 430
    assert "useCreateWorkflowMutation" in workbench_page
    assert "useUploadWorkflowMutation" in workbench_page
    assert "inputExamples" in workbench_page
    assert "const sampleCsv" not in workbench_page
    assert "function validateUploadFile" not in workbench_page
    assert "function WorkbenchControlPlane" not in workbench_page
    for split_file in WORKBENCH_SPLIT_FILES:
        assert split_file.exists()

    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )
    for split_file in [WORKBENCH_PAGE, *WORKBENCH_SPLIT_FILES]:
        assert split_file.name in frontend_architecture


def test_retrieval_page_surfaces_runtime_ranking_stack() -> None:
    retrieval_page = RETRIEVAL_PAGE.read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )

    assert "rankingStackFromPackage" in retrieval_page
    assert "diversityFromPackage" in retrieval_page
    assert "RerankBadge" in retrieval_page
    assert "DiversityBadge" in retrieval_page
    assert "packageData.handoff_context.reranker" in retrieval_page
    assert "packageData.handoff_context.diversity" in retrieval_page
    assert "runtime?.rerank?.enabled" in retrieval_page
    assert "applyFilterSuggestion" in retrieval_page
    assert "supportedSuggestionFilterFields" in retrieval_page
    assert "onApplyFilterSuggestion" in retrieval_page
    assert "Embedding and rerank provider state" in frontend_architecture
    assert "source coverage" in frontend_architecture
    assert "explicit operator apply" in frontend_architecture


def test_settings_page_exposes_reloadable_assistant_runtime() -> None:
    settings_page = SETTINGS_PAGE.read_text(encoding="utf-8")
    server_state = (FRONTEND_SRC / "lib" / "server-state.ts").read_text(encoding="utf-8")
    api_module = API_MODULE.read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )

    assert "AssistantSettingsForm" in settings_page
    assert "useRuntimeAssistantSettingsMutation" in settings_page
    assert "runtimeAssistantPayloadFromForm" in settings_page
    assert "OpenAI key configured" in settings_page
    assert "updateRuntimeAssistantSettings" in server_state
    assert '"/runtime/assistant-settings"' in api_module
    assert "Assistant runtime" in frontend_architecture


def test_frontend_browser_storage_is_not_used_for_auth_or_state() -> None:
    violations: list[str] = []

    for source_file in _frontend_source_files():
        text = source_file.read_text(encoding="utf-8")
        if BROWSER_STORAGE_RE.search(text):
            violations.append(
                f"{source_file.relative_to(REPO_ROOT)} uses browser storage/cookie APIs directly",
            )

    assert violations == []


def test_frontend_does_not_use_full_page_reload_for_server_state_refresh() -> None:
    violations: list[str] = []

    for source_file in _frontend_source_files():
        text = source_file.read_text(encoding="utf-8")
        if FULL_PAGE_RELOAD_RE.search(text):
            violations.append(
                f"{source_file.relative_to(REPO_ROOT)} uses full-page reload",
            )

    assert violations == []


def test_auth_provider_clears_server_state_cache_on_session_loss() -> None:
    auth_provider = AUTH_PROVIDER.read_text(encoding="utf-8")

    assert "useQueryClient" in auth_provider
    assert "AUTH_SESSION_EXPIRED_EVENT" in auth_provider
    assert "window.addEventListener(AUTH_SESSION_EXPIRED_EVENT" in auth_provider
    assert "queryClient.clear()" in auth_provider
    assert "err.status === 401" in auth_provider
    assert auth_provider.count("expireSession()") >= 2
    assert "logoutCurrentSession()" in auth_provider


def test_server_state_retries_do_not_repeat_unauthorized_requests() -> None:
    providers = APP_PROVIDERS.read_text(encoding="utf-8")

    assert "ApiRequestError" in providers
    assert "error.status === 401" in providers
    assert "return false" in providers
    assert "failureCount < 1" in providers


def test_frontend_has_app_level_error_boundary_without_page_reload() -> None:
    providers = APP_PROVIDERS.read_text(encoding="utf-8")
    error_boundary = ERROR_BOUNDARY.read_text(encoding="utf-8")

    assert "AppErrorBoundary" in providers
    assert "<AppErrorBoundary>" in providers
    assert "static getDerivedStateFromError" in error_boundary
    assert "Application error" in error_boundary
    assert "Reset view" in error_boundary
    assert "location.reload" not in error_boundary
    assert "window.location" not in error_boundary


def test_frontend_auth_callback_contract_does_not_model_bearer_token() -> None:
    frontend_types = FRONTEND_TYPES.read_text(encoding="utf-8")
    api_module = API_MODULE.read_text(encoding="utf-8")

    auth_login_start = frontend_types.index("export type AuthLoginResponse")
    auth_session_start = frontend_types.index("export type AuthSessionResponse")
    auth_login_type = frontend_types[auth_login_start:auth_session_start]

    assert "access_token" not in auth_login_type
    assert "token_type" not in auth_login_type
    assert "include_token" not in api_module


def test_frontend_api_wraps_malformed_json_as_structured_errors() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")

    assert "response.json()" not in api_module
    assert "await response.text()" in api_module
    assert "JSON.parse(body)" in api_module
    assert "normalizeEnvelope(JSON.parse(body)" in api_module
    assert "isApiEnvelope" in api_module
    assert "API response envelope is invalid." in api_module
    assert "API returned malformed JSON." in api_module
    assert "parse_error" in api_module


def test_frontend_api_wraps_network_failures_as_structured_errors() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")

    assert "async function fetchApi" in api_module
    assert "return await fetch(input, init)" in api_module
    assert 'code: "network_error"' in api_module
    assert "status: 0" in api_module
    assert "API request could not reach the server." in api_module
    assert "fetchApi(`${API_BASE_URL}${path}`" in api_module
    assert "fetchApi(`${rootPrefix}/health`" in api_module
    assert "fetchApi(`${API_BASE_URL}/parse/upload/workflow`" in api_module


def test_frontend_api_sets_json_content_type_only_for_body_requests() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")

    assert "headers: requestHeaders(init)" in api_module
    assert "function requestHeaders(init?: RequestInit): Headers" in api_module
    assert "new Headers(init?.headers)" in api_module
    assert "init?.body !== undefined" in api_module
    assert "!(init.body instanceof FormData)" in api_module
    assert 'headers.set("Content-Type", "application/json")' in api_module
    assert '"Content-Type": "application/json"' not in api_module


def test_frontend_api_calls_match_backend_route_surface() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")
    frontend_calls = _frontend_api_calls(api_module)

    backend_calls = {
        (method, route.path)
        for route in create_app().routes
        if isinstance(route, APIRoute)
        for method in route.methods or set()
        if method not in {"HEAD", "OPTIONS"}
    }

    assert frontend_calls
    assert frontend_calls - backend_calls == set()


def test_frontend_api_encodes_dynamic_path_segments() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")
    raw_dynamic_segments = [
        r"/\$\{workflowId\}",
        r"/\$\{reviewId\}",
    ]

    assert "function pathSegment(value: string): string" in api_module
    assert "encodeURIComponent(value)" in api_module
    for pattern in raw_dynamic_segments:
        assert re.search(pattern, api_module) is None
    assert "${pathSegment(workflowId)}" in api_module
    assert "${pathSegment(reviewId)}" in api_module


def test_app_shell_storage_badge_uses_runtime_config_contract() -> None:
    app_shell = APP_SHELL.read_text(encoding="utf-8")

    assert "useRuntimeConfigQuery" in app_shell
    assert "runtimeConfig.storage_backend" in app_shell
    assert "runtimeConfig.persistent_storage" in app_shell
    assert "Persistent storage" not in app_shell


def _normalize_frontend_api_path(raw_path: str) -> str | None:
    path = raw_path
    if path.startswith("${API_BASE_URL}"):
        path = path.removeprefix("${API_BASE_URL}")
        if path.startswith("/"):
            path = f"/api/v1{path}"
    elif path.startswith("${rootPrefix}"):
        path = path.removeprefix("${rootPrefix}")
    elif path.startswith("/api/v1"):
        return path
    elif path.startswith("/"):
        path = f"/api/v1{path}"
    else:
        return None

    path = path.split("${query", 1)[0]
    path = path.replace("${workflowId}", "{workflow_id}")
    path = path.replace("${pathSegment(workflowId)}", "{workflow_id}")
    path = path.replace("${reviewId}", "{review_id}")
    path = path.replace("${pathSegment(reviewId)}", "{review_id}")
    if path == "/api/v1/health":
        return "/health"
    return path


def _frontend_api_calls(api_module: str) -> set[tuple[str, str]]:
    calls: set[tuple[str, str]] = set()
    for match in FRONTEND_API_CALL_RE.finditer(api_module):
        path = _normalize_frontend_api_path(match.group("path"))
        if path is None or path == "/api/v1":
            continue
        call_source = _balanced_call_source(api_module, match.start())
        method_match = re.search(r"method:\s*[\"']([A-Z]+)[\"']", call_source)
        method = method_match.group(1) if method_match else "GET"
        calls.add((method, path))
    return calls


def _balanced_call_source(source: str, start: int) -> str:
    opening = source.find("(", start)
    if opening == -1:
        return source[start:]

    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(opening, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {"'", '"', "`"}:
            quote = char
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]

    return source[start:]


def test_e2e_cleanup_script_emits_parseable_json_summary() -> None:
    script = CLEANUP_SCRIPT.read_text(encoding="utf-8")

    assert "import json" in script
    assert "json.dumps(" in script
    assert "sort_keys=True" in script
    assert "deleted_workflows" in script
    assert "deleted_datasets" in script
    assert "deleted_events" in script
    assert "deleted_reviews" in script
    assert "deleted_evidence" in script
    assert "deleted_dataset_files" in script
    assert "deleted_auth_sessions" in script
    assert "deleted_auth_users" in script
    assert 'PLAYWRIGHT_GOOGLE_SUB_LIKE = "playwright-%"' in script
    assert 'PLAYWRIGHT_INSTRUCTION_LIKE = "Playwright E2E:%"' in script
    assert "left join ojtflow.users" in script
    assert "state_json->>'user_instruction'" in script
    assert "state_json->>'instruction'" in script
    assert "collect_file_refs" in script
    assert "input_refs, output_refs, event_json" in script
    assert "path.resolve().relative_to(data_root)" in script
    assert "ojtflow.workflow_events" in script
    assert "ojtflow.reviews" in script
    assert "ojtflow.evidence" in script
    assert "delete from ojtflow.sessions" in script
    assert "print({" not in script


def test_release_residue_assertion_matches_cleanup_workflow_markers() -> None:
    cleanup_script = CLEANUP_SCRIPT.read_text(encoding="utf-8")
    release_check = RELEASE_CHECK.read_text(encoding="utf-8")
    required_markers = [
        "u.google_sub like",
        "state_json->>'user_instruction'",
        "state_json->>'instruction'",
        "Playwright E2E:%",
    ]

    for marker in required_markers:
        assert marker in cleanup_script
        assert marker in release_check


def test_e2e_local_cleanup_is_success_only_and_limited_to_reports() -> None:
    package_json = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    local_cleanup = LOCAL_CLEANUP_SCRIPT.read_text(encoding="utf-8")
    release_check = RELEASE_CHECK.read_text(encoding="utf-8")

    assert package_json["scripts"]["e2e:cleanup:local"] == (
        "node scripts/cleanup-e2e-local-artifacts.mjs"
    )
    assert 'const artifactDirs = ["test-results", "playwright-report"];' in local_cleanup
    assert "rmSync(artifactPath, { force: true, recursive: true })" in local_cleanup
    assert "repoRoot" not in local_cleanup
    assert "docker" not in local_cleanup

    failure_exit_index = release_check.index('exit "${e2e_status}"')
    local_cleanup_index = release_check.index('npm run e2e:cleanup:local')
    residue_assertion_index = release_check.index('run_step "E2E residue assertion"')

    assert residue_assertion_index < failure_exit_index < local_cleanup_index


def test_playwright_cookie_authenticated_posts_send_origin_header() -> None:
    violations: list[str] = []

    for source_file in sorted(path for path in FRONTEND_E2E.rglob("*.ts") if path.is_file()):
        source = source_file.read_text(encoding="utf-8")
        for match in PLAYWRIGHT_CONTEXT_POST_RE.finditer(source):
            call_source = _balanced_call_source(source, match.start())
            if "headers:" not in call_source or "Origin:" not in call_source:
                violations.append(str(source_file.relative_to(REPO_ROOT)))

    assert violations == []
