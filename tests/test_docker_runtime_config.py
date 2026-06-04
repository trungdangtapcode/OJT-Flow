from pathlib import Path
import json


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_frontend_container_serves_built_assets_with_nginx() -> None:
    dockerfile = (REPO_ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    normalized = dockerfile.lower()

    assert "from node:22-alpine as build" in normalized
    assert "run npm run build" in normalized
    assert "from nginx:" in normalized
    assert "copy --from=build /app/dist" in normalized
    assert 'cmd ["nginx", "-g", "daemon off;"]' in normalized
    assert "npm run dev" not in normalized


def test_compose_uses_separate_api_and_frontend_build_contexts() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    api_section = compose.split("  api:", 1)[1].split("  frontend:", 1)[0]
    frontend_section = compose.split("  frontend:", 1)[1].split("volumes:", 1)[0]

    assert "build:" in api_section
    assert "\n      context: .\n" in api_section
    assert "\n      context: ./frontend\n" in frontend_section
    assert "\n      context: .\n" not in frontend_section


def test_api_container_includes_runtime_contracts_without_dev_server() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    constraints = (REPO_ROOT / "constraints.txt").read_text(encoding="utf-8")
    normalized = dockerfile.lower()

    assert "from python:3.12-slim" in normalized
    assert "pythondontwritebytecode=1" in normalized
    assert "pythonunbuffered=1" in normalized
    assert "pythonpath=/app/src" in normalized
    assert "arg pip_version=" in normalized
    assert "copy pyproject.toml readme.md constraints.txt" in normalized
    assert "copy src ./src" in normalized
    assert "copy knowledge ./knowledge" in normalized
    assert "copy sql ./sql" in normalized
    assert "pip==" in normalized
    assert "--constraint /app/constraints.txt" in normalized
    assert "--build-constraint /app/constraints.txt" in normalized
    assert '".[parsing]"' in normalized
    assert "python -m pip install --no-cache-dir" in normalized
    assert "markitdown==0.1.6" in constraints
    assert "pdfminer-six==20251230" in constraints
    assert "pdfplumber==0.11.9" in constraints
    assert "pip_constraint" not in normalized
    assert "--upgrade pip" not in normalized
    assert 'cmd ["python", "-m", "uvicorn"' in normalized
    assert "--reload" not in normalized


def test_api_dockerfile_copy_sources_are_allowlisted() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    copy_lines = [
        line.strip()
        for line in dockerfile.splitlines()
        if line.strip().lower().startswith("copy ")
    ]

    assert copy_lines == [
        "COPY pyproject.toml README.md constraints.txt ./",
        "COPY src ./src",
        "COPY knowledge ./knowledge",
        "COPY sql ./sql",
    ]
    assert all("COPY ." not in line for line in copy_lines)


def test_frontend_dockerfile_copy_sources_are_allowlisted() -> None:
    dockerfile = (REPO_ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    copy_lines = [
        line.strip()
        for line in dockerfile.splitlines()
        if line.strip().lower().startswith("copy ")
    ]

    assert copy_lines == [
        "COPY package.json package-lock.json ./",
        "COPY index.html tsconfig.json tsconfig.node.json vite.config.ts ./",
        "COPY src ./src",
        "COPY nginx.conf /etc/nginx/conf.d/default.conf",
        "COPY --from=build /app/dist /usr/share/nginx/html",
    ]
    assert all("COPY ." not in line for line in copy_lines)


def test_frontend_nginx_proxies_api_and_preserves_spa_routes() -> None:
    nginx_conf = (REPO_ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")

    assert "listen 5173;" in nginx_conf
    assert "server_tokens off;" in nginx_conf
    assert "location /api/" in nginx_conf
    assert "proxy_pass http://api:8000/api/;" in nginx_conf
    assert "location = /health" in nginx_conf
    assert "proxy_pass http://api:8000/health;" in nginx_conf
    assert "try_files $uri $uri/ /index.html;" in nginx_conf


def test_frontend_nginx_sets_cache_and_security_headers() -> None:
    nginx_conf = (REPO_ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")

    assert 'Cache-Control "no-store"' in nginx_conf
    assert 'Cache-Control "public, max-age=31536000, immutable"' in nginx_conf
    assert 'X-Content-Type-Options "nosniff"' in nginx_conf
    assert 'X-Frame-Options "DENY"' in nginx_conf
    assert 'Referrer-Policy "strict-origin-when-cross-origin"' in nginx_conf
    assert "Content-Security-Policy" in nginx_conf
    assert "frame-ancestors 'none'" in nginx_conf


def test_compose_frontend_healthcheck_does_not_depend_on_node_runtime() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    frontend_section = compose.split("  frontend:", 1)[1]

    assert "VITE_API_BASE_URL: ${VITE_API_BASE_URL:-/api/v1}" in frontend_section
    assert '"${OJT_FRONTEND_PORT:-5173}:5173"' in frontend_section
    assert "wget" in frontend_section
    assert "node" not in frontend_section
    assert "VITE_API_PROXY_TARGET" not in frontend_section


def test_compose_runtime_uses_postgres_redis_and_persistent_app_data() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    api_section = compose.split("  api:", 1)[1].split("  frontend:", 1)[0]

    assert "OJT_STORAGE_BACKEND: postgres" in api_section
    assert (
        "OJT_DATABASE_URL: "
        "postgresql://${OJT_POSTGRES_USER:-ojtflow}:"
        "${OJT_POSTGRES_PASSWORD:-ojtflow}@postgres:5432/"
        "${OJT_POSTGRES_DB:-ojtflow}"
    ) in api_section
    assert "OJT_REDIS_URL: redis://redis:6379/0" in api_section
    assert "OJT_DATA_DIR: /app/var" in api_section
    assert "OJT_KNOWLEDGE_DIR: /app/knowledge" in api_section
    assert "OJT_MIGRATIONS_DIR: /app/sql/postgres/migrations" in api_section
    assert "OJT_MAX_UPLOAD_BYTES: ${OJT_MAX_UPLOAD_BYTES:-26214400}" in api_section
    assert "OJT_MAX_INLINE_DATA_BYTES: ${OJT_MAX_INLINE_DATA_BYTES:-1048576}" in api_section
    assert "OJT_UPLOAD_READ_CHUNK_BYTES: ${OJT_UPLOAD_READ_CHUNK_BYTES:-1048576}" in api_section
    assert "OJT_ALLOWED_UPLOAD_EXTENSIONS: ${OJT_ALLOWED_UPLOAD_EXTENSIONS:-" in api_section
    assert '"${OJT_API_PORT:-8000}:8000"' in api_section
    assert "- app_data:/app/var" in api_section
    assert "postgres:" in api_section
    assert "redis:" in api_section
    assert "condition: service_healthy" in api_section
    assert "urllib.request.urlopen('http://127.0.0.1:8000/health'" in api_section


def test_compose_database_and_cache_defaults_are_overridable() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    postgres_section = compose.split("  postgres:", 1)[1].split("  redis:", 1)[0]
    redis_section = compose.split("  redis:", 1)[1].split("  api:", 1)[0]

    assert "POSTGRES_DB: ${OJT_POSTGRES_DB:-ojtflow}" in postgres_section
    assert "POSTGRES_USER: ${OJT_POSTGRES_USER:-ojtflow}" in postgres_section
    assert "POSTGRES_PASSWORD: ${OJT_POSTGRES_PASSWORD:-ojtflow}" in postgres_section
    assert '"${OJT_POSTGRES_PORT:-5432}:5432"' in postgres_section
    assert "pg_isready -U" in postgres_section
    assert "$${POSTGRES_USER}" in postgres_section
    assert "$${POSTGRES_DB}" in postgres_section
    assert '"${OJT_REDIS_PORT:-6379}:6379"' in redis_section


def test_env_example_exposes_compose_and_upload_runtime_knobs() -> None:
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    lines = set(env_example.splitlines())
    required_settings = {
        "OJT_POSTGRES_DB=ojtflow",
        "OJT_POSTGRES_USER=ojtflow",
        "OJT_POSTGRES_PASSWORD=ojtflow",
        "OJT_POSTGRES_PORT=5432",
        "OJT_REDIS_PORT=6379",
        "OJT_API_PORT=8000",
        "OJT_FRONTEND_PORT=5173",
        "VITE_API_BASE_URL=/api/v1",
        "OJT_KNOWLEDGE_DIR=knowledge",
        "OJT_MIGRATIONS_DIR=sql/postgres/migrations",
        "OJT_MAX_UPLOAD_BYTES=26214400",
        "OJT_MAX_INLINE_DATA_BYTES=1048576",
        "OJT_UPLOAD_READ_CHUNK_BYTES=1048576",
    }

    assert required_settings <= lines
    assert any(line.startswith("OJT_ALLOWED_UPLOAD_EXTENSIONS=") for line in lines)


def test_python_runtime_constraints_pin_direct_api_dependencies() -> None:
    constraints = (REPO_ROOT / "constraints.txt").read_text(encoding="utf-8").splitlines()
    pinned_packages = {
        line.split("==", 1)[0].lower().replace("_", "-")
        for line in constraints
        if line and not line.startswith("#")
    }
    required_direct_packages = {
        "fastapi",
        "google-auth",
        "httpx",
        "pydantic",
        "psycopg",
        "psycopg-binary",
        "python-multipart",
        "pyyaml",
        "redis",
        "uvicorn",
    }

    assert all(
        "==" in line
        for line in constraints
        if line and not line.startswith("#")
    )
    assert required_direct_packages <= pinned_packages
    assert "ojtflow" not in pinned_packages


def test_frontend_has_runtime_asset_freshness_check() -> None:
    package_json = json.loads((REPO_ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    script = (REPO_ROOT / "frontend" / "scripts" / "assert-runtime-assets-current.mjs").read_text(
        encoding="utf-8",
    )

    assert package_json["scripts"]["runtime:assert-current"] == (
        "node scripts/assert-runtime-assets-current.mjs"
    )
    assert "OJT_EXPECTED_FRONTEND_IMAGE" in script
    assert "OJT_EXPECTED_FRONTEND_INDEX" in script
    assert "OJT_RUNTIME_BASE_URL" in script
    assert "Runtime frontend assets do not match the expected frontend build." in script
    assert "/usr/share/nginx/html/index.html" in script
    assert "docker compose up -d --build frontend" in script


def test_docker_build_contexts_exclude_local_state_and_secrets() -> None:
    root_ignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    frontend_ignore = (REPO_ROOT / "frontend" / ".dockerignore").read_text(
        encoding="utf-8",
    ).splitlines()

    root_required = {
        ".git/",
        ".env",
        ".env.*",
        "data/",
        "docs/",
        "frontend/",
        "frontend/node_modules/",
        "frontend/dist/",
        "frontend/playwright-report/",
        "frontend/test-results/",
        "latex/",
        "submit/",
        "tests/",
        "var/",
        "plan/",
        "image.png",
        "latex/*.aux",
        "latex/*.log",
        "latex/*.out",
        "latex/*.toc",
        "submit/*.aux",
        "submit/*.log",
        "submit/*.out",
        "submit/*.toc",
        "texput.log",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
    }
    frontend_required = {
        ".git/",
        "node_modules/",
        "dist/",
        ".vite/",
        "playwright-report/",
        "test-results/",
        ".auth/",
        "var/",
        "e2e/",
        "scripts/",
        "playwright.config.ts",
        "*.tsbuildinfo",
        ".env",
        ".env.*",
    }

    assert root_required <= set(root_ignore)
    assert frontend_required <= set(frontend_ignore)
