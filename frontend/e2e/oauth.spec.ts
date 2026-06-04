import { expect, test } from "@playwright/test";

test("Google sign-in button starts a real OAuth browser handoff", async ({ baseURL, page }) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }
  const redirectUri = new URL("/auth/callback", baseURL).toString();

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();

  const preflight = await page.request.get(
    `/api/v1/auth/google/url?redirect_uri=${encodeURIComponent(redirectUri)}`,
  );
  test.skip(
    preflight.status() !== 200,
    "Google OAuth credentials are not configured in this environment.",
  );
  const envelope = (await preflight.json()) as {
    data: { authorization_url: string; state: string };
  };
  const authorizationUrl = new URL(envelope.data.authorization_url);
  expect(authorizationUrl.origin).toBe("https://accounts.google.com");
  expect(authorizationUrl.pathname).toContain("/o/oauth2");
  expect(authorizationUrl.searchParams.get("client_id")).toBeTruthy();
  expect(authorizationUrl.searchParams.get("redirect_uri")).toBe(redirectUri);
  expect(authorizationUrl.searchParams.get("scope")).toContain("openid");
  expect(authorizationUrl.searchParams.get("state")).toBe(envelope.data.state);

  await page.getByRole("button", { name: /sign in with google/i }).click();
  await page.waitForURL((url) => url.origin === "https://accounts.google.com", {
    timeout: 20_000,
  });

  const destination = new URL(page.url());
  expect(destination.origin).toBe("https://accounts.google.com");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});
