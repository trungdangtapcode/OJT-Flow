import { expect, test } from "@playwright/test";

import { authenticateBrowser, type E2EAuthArtifacts } from "./support/auth";
import { cleanupAuthArtifacts, cleanupWorkflowArtifacts } from "./support/cleanup";
import { createWorkflow } from "./support/workflows";

let authArtifactsToCleanup: E2EAuthArtifacts[] = [];
let workflowIdsToCleanup: string[] = [];

test.afterEach(() => {
  try {
    cleanupWorkflowArtifacts(workflowIdsToCleanup);
  } finally {
    cleanupAuthArtifacts(authArtifactsToCleanup);
    workflowIdsToCleanup = [];
    authArtifactsToCleanup = [];
  }
});

test("login gate presents the access boundary and single OAuth action", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 720 });
  await page.goto("/workflows");

  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Access boundary" })).toBeVisible();
  await expect(page.getByText("OAuth session")).toBeVisible();
  await expect(page.getByText("Google identity")).toBeVisible();
  await expect(page.getByText("Authenticated owner")).toBeVisible();
  await expect(page.getByText("Review trail")).toBeVisible();
  await expect(page.getByText("Audit attached")).toBeVisible();
  await expect(page.getByText("HTTP-only cookie")).toBeVisible();
  await expect(page.getByText("Owner-bound data")).toBeVisible();
  await expect(page.getByText("API", { exact: true })).toBeVisible();
  await expect(page.getByText("/api/v1", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in with google/i })).toHaveCount(1);

  const layout = await page.evaluate(() => ({
    h1: document.querySelector("h1")?.textContent?.trim(),
    overflow:
      Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) -
      window.innerWidth,
  }));
  expect(layout.h1).toBe("Sign in to continue");
  expect(layout.overflow).toBeLessThanOrEqual(0);
});

test("authenticated user can sign out and return to the login gate", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));

  await page.goto("/workflows");
  await expect(page.getByRole("heading", { name: "Workflow operations" })).toBeVisible();
  await expect(page.getByText("Playwright E2E User")).toBeVisible();

  const logoutResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/auth/logout") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Sign out" }).click();
  const logout = await logoutResponse;
  expect(logout.status()).toBe(200);
  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in with google/i })).toBeVisible();

  const sessionCookies = (await context.cookies(baseURL)).filter(
    (cookie) => cookie.name === "ojtflow_session",
  );
  expect(sessionCookies).toHaveLength(0);

  const currentUser = await context.request.get(`${baseURL}/api/v1/auth/me`);
  expect(currentUser.status()).toBe(401);
});

test("revoked session during app use clears protected UI", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  const workflowId = await createWorkflow(context, baseURL, {
    requireHumanReview: false,
  });
  workflowIdsToCleanup.push(workflowId);

  await page.goto("/workflows");
  await expect(page.getByRole("heading", { name: "Workflow operations" })).toBeVisible();
  await expect(page.getByRole("heading", { name: workflowId })).toBeVisible();

  const logout = await context.request.post(`${baseURL}/api/v1/auth/logout`, {
    headers: { Origin: new URL(baseURL).origin },
  });
  expect(logout.status()).toBe(200);

  const expiredResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/workflows") && response.status() === 401,
  );
  await page.getByRole("button", { name: "Refresh application data" }).click();
  await expiredResponse;

  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in with google/i })).toBeVisible();
  await expect(page.getByText(workflowId)).toHaveCount(0);

  const currentUser = await context.request.get(`${baseURL}/api/v1/auth/me`);
  expect(currentUser.status()).toBe(401);
});

test("malformed API JSON surfaces as a structured login error", async ({ page }) => {
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      body: "{not-valid-json",
      contentType: "application/json",
      status: 502,
    });
  });

  await page.goto("/workflows");

  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByText(/invalid_response: API returned malformed JSON/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in with google/i })).toBeVisible();
});

test("network failures surface as a structured login error", async ({ page }) => {
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.abort("failed");
  });

  await page.goto("/workflows");

  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByText(/network_error: API request could not reach the server/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in with google/i })).toBeVisible();
});

test("invalid API envelope surfaces as a structured login error", async ({ page }) => {
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      body: JSON.stringify({
        user: {
          email: "bad-envelope@example.com",
        },
      }),
      contentType: "application/json",
      status: 200,
    });
  });

  await page.goto("/workflows");

  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByText(/invalid_response: API response envelope is invalid/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in with google/i })).toBeVisible();
});

test("Google callback errors return to login with visible context", async ({ page }) => {
  await page.goto("/auth/callback?error=access_denied");

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByText("Google sign-in failed: access_denied")).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in with google/i })).toBeVisible();
});

test("incomplete Google callbacks return to login with visible context", async ({ page }) => {
  await page.goto("/auth/callback?state=missing-code");

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByText("Google callback is missing code or state.")).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in with google/i })).toBeVisible();
});
