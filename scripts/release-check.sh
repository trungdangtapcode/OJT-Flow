#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
frontend_root="${repo_root}/frontend"
python_bin="${PYTHON_BIN:-python}"
skip_docker_build="${OJT_RELEASE_CHECK_SKIP_DOCKER_BUILD:-0}"
skip_e2e="${OJT_RELEASE_CHECK_SKIP_E2E:-0}"

run_step() {
  local label="$1"
  shift
  printf '\n==> %s\n' "${label}"
  "$@"
}

run_frontend_step() {
  local label="$1"
  shift
  printf '\n==> %s\n' "${label}"
  (cd "${frontend_root}" && "$@")
}

assert_e2e_residue_clean() {
  docker compose exec -T api python - <<'PY'
from ojtflow.config import get_settings
from ojtflow.infrastructure.storage.postgres import PostgresBackboneStore

settings = get_settings()
store = PostgresBackboneStore(settings.postgres_dsn, settings.data_dir)

with store.connect() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select count(*) as count
            from ojtflow.workflows w
            left join ojtflow.users u on u.user_id = w.owner_user_id
            where u.google_sub like 'playwright-%'
               or coalesce(w.state_json->>'user_instruction', '') like 'Playwright E2E:%'
               or coalesce(w.state_json->>'instruction', '') like 'Playwright E2E:%'
            """
        )
        workflow_count = cursor.fetchone()["count"]
        cursor.execute(
            """
            select count(*) as count
            from ojtflow.users
            where google_sub like 'playwright-%'
            """
        )
        user_count = cursor.fetchone()["count"]

print(f"playwright_marked_workflows {workflow_count}")
print(f"playwright_users {user_count}")

if workflow_count or user_count:
    raise SystemExit("Playwright E2E cleanup left Postgres residue.")
PY
}

assert_git_diff_hygiene() {
  git diff --check
  git diff --cached --check
}

run_step "Python test suite" \
  env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="${repo_root}/src" \
  "${python_bin}" -m pytest -q

run_step "Postgres migration manifest" \
  env PYTHONPATH="${repo_root}/src" \
  "${python_bin}" "${repo_root}/scripts/check-migrations.py"

run_step "Retrieval quality evaluation" "${python_bin}" "${repo_root}/scripts/evaluate-retrieval.py"

run_step "Graph-NER quality evaluation" "${python_bin}" "${repo_root}/scripts/evaluate-graph-ner.py"

run_step "Performance smoke" \
  env OJT_STORAGE_BACKEND=memory PYTHONPATH="${repo_root}/src" \
  "${python_bin}" "${repo_root}/scripts/performance-smoke.py" --mode asgi

run_frontend_step "Frontend TypeScript/Vite build" npm run build

if [[ "${skip_docker_build}" != "1" ]]; then
  run_step "Docker stack rebuild" docker compose up -d --build
else
  printf '\n==> Docker stack rebuild skipped by OJT_RELEASE_CHECK_SKIP_DOCKER_BUILD=1\n'
fi

run_frontend_step "Runtime frontend asset assertion" npm run runtime:assert-current

if [[ "${skip_e2e}" != "1" ]]; then
  printf '\n==> Browser E2E suite\n'
  set +e
  (cd "${frontend_root}" && npm run e2e)
  e2e_status=$?
  set -e

  run_frontend_step "E2E artifact cleanup" npm run e2e:cleanup
  run_step "E2E residue assertion" assert_e2e_residue_clean

  if [[ "${e2e_status}" -ne 0 ]]; then
    printf '\nBrowser E2E suite failed with status %s.\n' "${e2e_status}" >&2
    exit "${e2e_status}"
  fi

  run_frontend_step "E2E local report cleanup" npm run e2e:cleanup:local
else
  printf '\n==> Browser E2E suite skipped by OJT_RELEASE_CHECK_SKIP_E2E=1\n'
fi

run_step "Git whitespace/conflict-marker hygiene" assert_git_diff_hygiene

printf '\nRelease check completed successfully.\n'
