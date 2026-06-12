import { expect, test } from "@playwright/test";

import { authenticateBrowser, type E2EAuthArtifacts } from "./support/auth";
import { cleanupAuthArtifacts } from "./support/cleanup";

let authArtifactsToCleanup: E2EAuthArtifacts[] = [];

test.afterEach(() => {
  cleanupAuthArtifacts(authArtifactsToCleanup);
  authArtifactsToCleanup = [];
});

test("smoke: login gate and authenticated shell are reachable", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in with google/i })).toBeVisible();

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  await page.goto("/assistant");

  await expect(page.getByRole("heading", { name: "AI Assistant" })).toBeVisible();
  await expect(page.getByText("Playwright E2E User")).toBeVisible();
  await expect(page.getByRole("navigation")).toBeVisible();
});
