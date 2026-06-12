import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "../..");

const cleanupScript = String.raw`
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from ojtflow.config import get_settings
from ojtflow.infrastructure.storage.auth_postgres import PostgresAuthRepository
from ojtflow.infrastructure.storage.postgres import PostgresBackboneStore

settings = get_settings()
backbone = PostgresBackboneStore(settings.postgres_dsn, settings.data_dir)
auth = PostgresAuthRepository(settings.postgres_dsn)
PLAYWRIGHT_GOOGLE_SUB_LIKE = "playwright-%"
PLAYWRIGHT_INSTRUCTION_LIKE = "Playwright E2E:%"
data_root = settings.data_dir.resolve()

workflow_ids = []
storage_refs = []
deleted_datasets = 0
deleted_events = 0
deleted_reviews = 0
deleted_evidence = 0
deleted_workflows = 0
deleted_organizations = 0


def collect_file_refs(value):
    if isinstance(value, str):
        return [value] if value.startswith("file://") else []
    if isinstance(value, list):
        refs = []
        for item in value:
            refs.extend(collect_file_refs(item))
        return refs
    if isinstance(value, dict):
        refs = []
        for item in value.values():
            refs.extend(collect_file_refs(item))
        return refs
    return []


def is_safe_artifact_path(path):
    try:
        path.resolve().relative_to(data_root)
    except ValueError:
        return False
    return path.is_file()

with backbone.connect() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select w.workflow_id
            from ojtflow.workflows w
            left join ojtflow.users u on u.user_id = w.owner_user_id
            where u.google_sub like %s
               or coalesce(w.state_json->>'user_instruction', '') like %s
               or coalesce(w.state_json->>'instruction', '') like %s
            """,
            (
                PLAYWRIGHT_GOOGLE_SUB_LIKE,
                PLAYWRIGHT_INSTRUCTION_LIKE,
                PLAYWRIGHT_INSTRUCTION_LIKE,
            ),
        )
        workflow_ids = [row["workflow_id"] for row in cursor.fetchall()]
        if workflow_ids:
            cursor.execute(
                "select count(*) as count from ojtflow.workflow_events where workflow_id = any(%s::text[])",
                (workflow_ids,),
            )
            deleted_events = cursor.fetchone()["count"]
            cursor.execute(
                "select count(*) as count from ojtflow.reviews where workflow_id = any(%s::text[])",
                (workflow_ids,),
            )
            deleted_reviews = cursor.fetchone()["count"]
            cursor.execute(
                "select count(*) as count from ojtflow.evidence where workflow_id = any(%s::text[])",
                (workflow_ids,),
            )
            deleted_evidence = cursor.fetchone()["count"]
            cursor.execute(
                """
                select storage_ref
                from ojtflow.datasets
                where workflow_id = any(%s::text[])
                """,
                (workflow_ids,),
            )
            storage_refs = [row["storage_ref"] for row in cursor.fetchall()]
            cursor.execute(
                """
                select state_json
                from ojtflow.workflows
                where workflow_id = any(%s::text[])
                """,
                (workflow_ids,),
            )
            for row in cursor.fetchall():
                storage_refs.extend(collect_file_refs(row["state_json"]))
            cursor.execute(
                """
                select input_refs, output_refs, event_json
                from ojtflow.workflow_events
                where workflow_id = any(%s::text[])
                """,
                (workflow_ids,),
            )
            for row in cursor.fetchall():
                storage_refs.extend(collect_file_refs(row["input_refs"]))
                storage_refs.extend(collect_file_refs(row["output_refs"]))
                storage_refs.extend(collect_file_refs(row["event_json"]))
            cursor.execute(
                "delete from ojtflow.datasets where workflow_id = any(%s::text[])",
                (workflow_ids,),
            )
            deleted_datasets = cursor.rowcount
            cursor.execute(
                "delete from ojtflow.workflows where workflow_id = any(%s::text[])",
                (workflow_ids,),
            )
            deleted_workflows = cursor.rowcount
    connection.commit()

deleted_files = 0
for storage_ref in storage_refs:
    parsed = urlparse(storage_ref)
    if parsed.scheme != "file":
        continue
    try:
        path = Path(unquote(parsed.path))
        if is_safe_artifact_path(path):
            path.unlink()
            deleted_files += 1
    except OSError:
        pass

with auth.connect() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            "select user_id from ojtflow.users where google_sub like %s",
            (PLAYWRIGHT_GOOGLE_SUB_LIKE,),
        )
        user_ids = [row["user_id"] for row in cursor.fetchall()]
        if user_ids:
            cursor.execute(
                "delete from ojtflow.sessions where user_id = any(%s::text[])",
                (user_ids,),
            )
            deleted_sessions = cursor.rowcount
            cursor.execute(
                "delete from ojtflow.organizations where created_by_user_id = any(%s::text[])",
                (user_ids,),
            )
            deleted_organizations = cursor.rowcount
        else:
            deleted_sessions = 0
        cursor.execute(
            "delete from ojtflow.users where google_sub like %s",
            (PLAYWRIGHT_GOOGLE_SUB_LIKE,),
        )
        deleted_users = cursor.rowcount
    connection.commit()

print(json.dumps({
    "deleted_workflows": deleted_workflows,
    "deleted_datasets": deleted_datasets,
    "deleted_events": deleted_events,
    "deleted_reviews": deleted_reviews,
    "deleted_evidence": deleted_evidence,
    "deleted_dataset_files": deleted_files,
    "deleted_organizations": deleted_organizations,
    "deleted_auth_sessions": deleted_sessions,
    "deleted_auth_users": deleted_users,
}, sort_keys=True))
`;

try {
  const output = execFileSync("docker", ["compose", "exec", "-T", "api", "python", "-"], {
    cwd: repoRoot,
    input: cleanupScript,
    encoding: "utf8",
    stdio: ["pipe", "pipe", "pipe"],
  });
  process.stdout.write(output);
} catch (error) {
  const stderr =
    typeof error === "object" && error !== null && "stderr" in error
      ? String(error.stderr)
      : "";
  throw new Error(
    [
      "Could not clean Playwright E2E artifacts.",
      "Start the Docker stack first with `docker compose up -d --build`.",
      stderr.trim(),
    ]
      .filter(Boolean)
      .join("\n"),
  );
}
