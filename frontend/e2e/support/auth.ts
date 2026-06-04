import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { BrowserContext } from "@playwright/test";

const supportDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(supportDir, "../../..");

export type E2EAuthArtifacts = {
  managed: boolean;
  sessionId: string | null;
  userId: string | null;
};

const createSessionScript = String.raw`
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone

from ojtflow.config import get_settings
from ojtflow.core.contracts.auth import GoogleIdentityProfile
from ojtflow.infrastructure.storage.auth_postgres import PostgresAuthRepository

suffix = secrets.token_hex(6)
repo = PostgresAuthRepository(get_settings().postgres_dsn)
profile = GoogleIdentityProfile(
    google_sub=f"playwright-e2e-{suffix}",
    email=f"playwright-e2e-{suffix}@example.com",
    email_verified=True,
    display_name="Playwright E2E User",
    avatar_url=None,
)
user = repo.upsert_google_user(profile)
raw_token = secrets.token_urlsafe(48)
token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
session = repo.create_session(
    user_id=user.user_id,
    token_hash=token_hash,
    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    user_agent="playwright-e2e",
    ip_address="127.0.0.1",
)
print(json.dumps({
    "token": raw_token,
    "user_id": user.user_id,
    "session_id": session.session_id,
}))
`;

export function createBackendSessionToken(): { artifacts: E2EAuthArtifacts; token: string } {
  const existingToken = process.env.OJT_E2E_SESSION_TOKEN?.trim();
  if (existingToken) {
    return {
      artifacts: { managed: false, sessionId: null, userId: null },
      token: existingToken,
    };
  }

  try {
    const output = execFileSync("docker", ["compose", "exec", "-T", "api", "python", "-"], {
      cwd: repoRoot,
      input: createSessionScript,
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
    }).trim();
    const session = JSON.parse(output) as {
      session_id: string;
      token: string;
      user_id: string;
    };
    return {
      artifacts: {
        managed: true,
        sessionId: session.session_id,
        userId: session.user_id,
      },
      token: session.token,
    };
  } catch (error) {
    const stderr =
      typeof error === "object" && error !== null && "stderr" in error
        ? String((error as { stderr?: unknown }).stderr)
        : "";
    throw new Error(
      [
        "Could not create a Playwright backend session.",
        "Start the Docker stack first with `docker compose up -d --build` and run migrations.",
        stderr.trim(),
      ]
        .filter(Boolean)
        .join("\n"),
    );
  }
}

export async function authenticateBrowser(
  context: BrowserContext,
  baseURL: string,
): Promise<E2EAuthArtifacts> {
  const session = createBackendSessionToken();
  await context.addCookies([
    {
      name: "ojtflow_session",
      value: session.token,
      url: baseURL,
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
  return session.artifacts;
}
