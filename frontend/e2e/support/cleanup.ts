import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { E2EAuthArtifacts } from "./auth";

const supportDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(supportDir, "../../..");

const cleanupWorkflowsScript = String.raw`
import json
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from ojtflow.config import get_settings
from ojtflow.infrastructure.storage.postgres import PostgresBackboneStore

workflow_ids = sorted(set(json.loads(os.environ["OJT_E2E_WORKFLOW_IDS"])))
if not workflow_ids:
    raise SystemExit(0)

settings = get_settings()
store = PostgresBackboneStore(settings.postgres_dsn, settings.data_dir)
data_root = settings.data_dir.resolve()
storage_refs = []
deleted_datasets = 0
deleted_events = 0
deleted_reviews = 0
deleted_evidence = 0
deleted_workflows = 0


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

with store.connect() as connection:
    with connection.cursor() as cursor:
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

for storage_ref in storage_refs:
    parsed = urlparse(storage_ref)
    if parsed.scheme != "file":
        continue
    try:
        path = Path(unquote(parsed.path))
        if is_safe_artifact_path(path):
            path.unlink(missing_ok=True)
    except OSError:
        pass

print(
    "cleaned "
    f"{deleted_workflows} workflow(s), "
    f"{deleted_datasets} dataset row(s), "
    f"{deleted_events} event(s), "
    f"{deleted_reviews} review(s), "
    f"{deleted_evidence} evidence item(s)"
)
`;

const cleanupAuthScript = String.raw`
import json
import os

from ojtflow.config import get_settings
from ojtflow.infrastructure.storage.auth_postgres import PostgresAuthRepository

user_ids = sorted(set(json.loads(os.environ["OJT_E2E_AUTH_USER_IDS"])))
session_ids = sorted(set(json.loads(os.environ["OJT_E2E_AUTH_SESSION_IDS"])))
if not user_ids and not session_ids:
    raise SystemExit(0)

repo = PostgresAuthRepository(get_settings().postgres_dsn)
deleted_organizations = 0
with repo.connect() as connection:
    with connection.cursor() as cursor:
        if session_ids:
            cursor.execute(
                "delete from ojtflow.sessions where session_id = any(%s::text[])",
                (session_ids,),
            )
            deleted_sessions = cursor.rowcount
        else:
            deleted_sessions = 0
        if user_ids:
            cursor.execute(
                """
                delete from ojtflow.organizations
                where created_by_user_id = any(%s::text[])
                """,
                (user_ids,),
            )
            deleted_organizations = cursor.rowcount
            cursor.execute(
                """
                delete from ojtflow.users
                where user_id = any(%s::text[])
                  and google_sub like 'playwright-e2e-%%'
                """,
                (user_ids,),
            )
            deleted_users = cursor.rowcount
        else:
            deleted_users = 0
    connection.commit()

print(
    f"cleaned {deleted_users} e2e auth user(s), "
    f"{deleted_sessions} session(s), "
    f"{deleted_organizations} organization(s)"
)
`;

export function cleanupWorkflowArtifacts(workflowIds: string[]): void {
  const uniqueWorkflowIds = [...new Set(workflowIds.filter(Boolean))];
  if (uniqueWorkflowIds.length === 0) return;

  runCleanupScript(cleanupWorkflowsScript, {
    OJT_E2E_WORKFLOW_IDS: JSON.stringify(uniqueWorkflowIds),
  });
}

export function cleanupAuthArtifacts(artifacts: E2EAuthArtifacts[]): void {
  const managedArtifacts = artifacts.filter((artifact) => artifact.managed);
  const userIds = uniqueStrings(managedArtifacts.map((artifact) => artifact.userId));
  const sessionIds = uniqueStrings(managedArtifacts.map((artifact) => artifact.sessionId));
  if (userIds.length === 0 && sessionIds.length === 0) return;

  runCleanupScript(cleanupAuthScript, {
    OJT_E2E_AUTH_SESSION_IDS: JSON.stringify(sessionIds),
    OJT_E2E_AUTH_USER_IDS: JSON.stringify(userIds),
  });
}

function uniqueStrings(values: Array<string | null>): string[] {
  return [
    ...new Set(values.filter((value): value is string => Boolean(value))),
  ];
}

function runCleanupScript(script: string, env: Record<string, string>): void {
  if (process.env.OJT_E2E_SESSION_TOKEN?.trim()) {
    const python = localPythonExecutable();
    execFileSync(python, ["-"], {
      cwd: repoRoot,
      env: { ...process.env, ...env },
      input: script,
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
    });
    return;
  }

  execFileSync(
    "docker",
    [
      "compose",
      "exec",
      "-T",
      ...Object.entries(env).flatMap(([key, value]) => ["-e", `${key}=${value}`]),
      "api",
      "python",
      "-",
    ],
    {
      cwd: repoRoot,
      input: script,
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
    },
  );
}

function localPythonExecutable(): string {
  const configuredPython = process.env.OJT_E2E_PYTHON?.trim();
  if (configuredPython) return configuredPython;

  return "python";
}
