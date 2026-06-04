import { expect, test, type Page } from "@playwright/test";

import { authenticateBrowser, type E2EAuthArtifacts } from "./support/auth";
import { cleanupAuthArtifacts, cleanupWorkflowArtifacts } from "./support/cleanup";
import { createDenseWorkflowQueue, createReviewWorkflow } from "./support/workflows";

const primaryRoutes = [
  "/assistant",
  "/workflows",
  "/reviews",
  "/retrieval",
  "/workbench",
  "/audit",
  "/schemas",
  "/settings",
];
let authArtifactsToCleanup: E2EAuthArtifacts[] = [];
let workflowIdsToCleanup: string[] = [];

test.afterEach(() => {
  try {
    cleanupWorkflowArtifacts(workflowIdsToCleanup);
  } finally {
    cleanupAuthArtifacts(authArtifactsToCleanup);
    authArtifactsToCleanup = [];
    workflowIdsToCleanup = [];
  }
});

async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    overflow:
      Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) -
      window.innerWidth,
    overflowingElements: Array.from(document.querySelectorAll("body *")).filter((element) => {
      const rect = element.getBoundingClientRect();
      return rect.right > window.innerWidth + 1 || rect.left < -1;
    }).length,
  }));

  expect(metrics.overflow).toBeLessThanOrEqual(0);
  expect(metrics.overflowingElements).toBe(0);
}

async function expectNoVisibleErrorTokens(page: Page) {
  const visibleText = await page.locator("body").innerText();
  expect(visibleText).not.toMatch(
    /undefined|NaN|\[object Object\]|500 Internal Server Error|Traceback/,
  );
}

async function expectNoClippedInteractiveControls(page: Page) {
  const clipped = await page.evaluate(() =>
    Array.from(
      document.querySelectorAll("button, a, select, input, textarea, [role='button']"),
    )
      .filter((element) => {
        const rect = element.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return false;
        return (
          element.scrollWidth - element.clientWidth > 2 ||
          element.scrollHeight - element.clientHeight > 2
        );
      })
      .map((element) => ({
        tag: element.tagName,
        role: element.getAttribute("role"),
        label: element.getAttribute("aria-label"),
        text: element.textContent?.trim().replace(/\s+/g, " ").slice(0, 120),
        width: Math.round(element.getBoundingClientRect().width),
        scrollWidth: element.scrollWidth,
        clientWidth: element.clientWidth,
        scrollHeight: element.scrollHeight,
        clientHeight: element.clientHeight,
      })),
  );

  expect(clipped).toEqual([]);
}

async function expectRouteIntegrity(page: Page) {
  await expect(page.locator("h1")).toBeVisible();
  await expectNoVisibleErrorTokens(page);
  await expectNoHorizontalOverflow(page);
  await expectNoClippedInteractiveControls(page);
  await expectShellAccessibility(page);
}

async function expectShellAccessibility(page: Page) {
  const metrics = await page.evaluate(() => {
    const navLinks = Array.from(document.querySelectorAll("nav a")).map((link) => {
      const rect = link.getBoundingClientRect();
      return {
        ariaCurrent: link.getAttribute("aria-current"),
        label: link.getAttribute("aria-label"),
        height: Math.round(rect.height),
        top: Math.round(rect.top),
        width: Math.round(rect.width),
      };
    });
    const headerButtons = Array.from(document.querySelectorAll("header button")).map((button) => {
      const rect = button.getBoundingClientRect();
      return {
        label: button.getAttribute("aria-label"),
        height: Math.round(rect.height),
        width: Math.round(rect.width),
      };
    });
    const tabTargets = Array.from(document.querySelectorAll("[role='tab']"))
      .filter((tab) => {
        const rect = tab.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      })
      .map((tab) => {
        const rect = tab.getBoundingClientRect();
        return {
          label: tab.textContent?.trim().replace(/\s+/g, " "),
          height: Math.round(rect.height),
          width: Math.round(rect.width),
        };
      });
    return {
      headerButtons,
      isMobile: window.innerWidth <= 390,
      navLinks,
      navTopRange:
        navLinks.length > 0
          ? Math.max(...navLinks.map((link) => link.top)) -
            Math.min(...navLinks.map((link) => link.top))
          : 0,
      shellHeaderHeight: Math.round(
        document.querySelector("aside")?.getBoundingClientRect().height ?? 0,
      ),
      tabTargets,
    };
  });

  expect(metrics.navLinks).toHaveLength(8);
  expect(metrics.navLinks.filter((link) => link.ariaCurrent === "page")).toHaveLength(1);
  expect(metrics.navLinks.map((link) => link.label).sort()).toEqual([
    "Audit",
    "Assistant",
    "Retrieval",
    "Reviews",
    "Schemas",
    "Settings",
    "Workbench",
    "Workflows",
  ]);

  if (metrics.isMobile) {
    for (const link of metrics.navLinks) {
      expect(link.height).toBeGreaterThanOrEqual(44);
      expect(link.width).toBeGreaterThanOrEqual(44);
    }
    expect(metrics.navTopRange).toBeLessThanOrEqual(2);
    expect(metrics.shellHeaderHeight).toBeLessThanOrEqual(72);
    for (const button of metrics.headerButtons) {
      expect(button.height).toBeGreaterThanOrEqual(44);
      expect(button.width).toBeGreaterThanOrEqual(44);
    }
    for (const tab of metrics.tabTargets) {
      expect(tab.height).toBeGreaterThanOrEqual(44);
      expect(tab.width).toBeGreaterThanOrEqual(44);
    }
  }
}

test("primary app routes stay contained on desktop and mobile", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  workflowIdsToCleanup.push(await createReviewWorkflow(context, baseURL));

  for (const route of primaryRoutes) {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(route);
    await expectRouteIntegrity(page);

    await page.setViewportSize({ width: 390, height: 844 });
    await expectRouteIntegrity(page);

    await page.setViewportSize({ width: 320, height: 720 });
    await expectRouteIntegrity(page);
  }
});

test("workflow operations stays usable with a dense queue and selected detail", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  const workflowIds = await createDenseWorkflowQueue(context, baseURL);
  workflowIdsToCleanup.push(...workflowIds);

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/workflows");
  await expectRouteIntegrity(page);
  await expect(page.getByText("8 runs")).toBeVisible();
  await expect(page.getByRole("tab", { name: "Overview" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Steps" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Validation issues" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Retrieval evidence" })).toBeHidden();

  await page.getByRole("tab", { name: "Evidence" }).click();
  await expect(page.getByRole("heading", { name: "Retrieval evidence" })).toBeVisible();
  await expectRouteIntegrity(page);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/workflows");
  await expectRouteIntegrity(page);
  await expect(page.getByRole("heading", { name: "Workflow queue" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Overview" })).toHaveCount(0);

  await page.goto(`/workflows/${workflowIds[0]}`);
  await expectRouteIntegrity(page);
  for (const tab of ["Issues", "Evidence", "Review", "Audit"]) {
    await page.getByRole("tab", { name: tab }).click();
    await expectRouteIntegrity(page);
  }

  await page.setViewportSize({ width: 320, height: 720 });
  await page.goto(`/workflows/${workflowIds[0]}`);
  await page.getByRole("tab", { name: "Evidence" }).click();
  await expectRouteIntegrity(page);
});

test("new authenticated workspace shows scoped empty states", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));

  await page.goto("/workflows");
  await expect(page.getByText("No workflows yet")).toBeVisible();
  await expect(page.getByRole("link", { name: "Start in workbench" })).toBeVisible();

  await page.goto("/reviews");
  await expect(page.getByText("No pending reviews")).toBeVisible();
  await expect(page.getByRole("link", { name: "Create workflow" })).toBeVisible();

  await page.goto("/audit");
  await expect(page.getByText("No audit trails yet")).toBeVisible();
  await expect(page.getByRole("link", { name: "Create workflow" })).toBeVisible();
  await expect(page.getByText(/Showing 0-0 of 0/)).toHaveCount(0);
});

test("review queue loading state preserves table and card structure", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));

  let releaseReviewSummary: () => void = () => undefined;
  const reviewSummaryDelay = new Promise<void>((resolve) => {
    releaseReviewSummary = resolve;
  });
  await page.route("**/api/v1/reviews/summary**", async (route) => {
    await reviewSummaryDelay;
    await route.continue();
  });

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/reviews");
  await expect(page.getByRole("status", { exact: true, name: "Loading Matching reviews" })).toBeVisible();
  await expect(page.getByLabel("Loading review queue")).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Workflow" })).toBeVisible();
  await expect(page.getByTestId("review-queue-skeleton-row")).toHaveCount(7);
  await expectNoHorizontalOverflow(page);
  await expectNoClippedInteractiveControls(page);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/reviews");
  await expect(page.getByLabel("Loading review queue")).toBeVisible();
  await expect(page.getByTestId("review-queue-skeleton-card")).toHaveCount(3);
  await expect(page.getByRole("columnheader", { name: "Workflow" })).toHaveCount(0);
  await expectNoHorizontalOverflow(page);
  await expectNoClippedInteractiveControls(page);
  const reviewSummaryResponse = page.waitForResponse("**/api/v1/reviews/summary**");
  releaseReviewSummary();
  await reviewSummaryResponse;
  await page.unroute("**/api/v1/reviews/summary**");
});

test("audit loading states preserve trail and event structure", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  workflowIdsToCleanup.push(await createReviewWorkflow(context, baseURL));

  await page.setViewportSize({ width: 1440, height: 900 });
  let releaseAuditSummary: () => void = () => undefined;
  const auditSummaryDelay = new Promise<void>((resolve) => {
    releaseAuditSummary = resolve;
  });
  await page.route("**/api/v1/workflows/summary**", async (route) => {
    await auditSummaryDelay;
    await route.continue();
  });
  await page.goto("/audit");
  await expect(page.getByRole("status", { exact: true, name: "Loading Audit trails" })).toBeVisible();
  await expect(page.getByRole("status", { exact: true, name: "Loading audit trails" })).toBeVisible();
  await expect(page.getByTestId("audit-trail-skeleton-row")).toHaveCount(6);
  await expectNoHorizontalOverflow(page);
  await expectNoClippedInteractiveControls(page);
  const auditSummaryResponse = page.waitForResponse("**/api/v1/workflows/summary**");
  releaseAuditSummary();
  await auditSummaryResponse;
  await page.unroute("**/api/v1/workflows/summary**");

  const eventPage = await context.newPage();
  await eventPage.setViewportSize({ width: 1440, height: 900 });
  let releaseAuditEvents: () => void = () => undefined;
  const auditEventsDelay = new Promise<void>((resolve) => {
    releaseAuditEvents = resolve;
  });
  await eventPage.route("**/api/v1/workflows/*/events", async (route) => {
    await auditEventsDelay;
    await route.continue();
  });
  await eventPage.goto("/audit");
  await expect(eventPage.getByLabel("Loading audit event timeline")).toBeVisible();
  await expect(eventPage.getByTestId("audit-event-skeleton-row")).toHaveCount(5);
  await expectNoHorizontalOverflow(eventPage);
  await expectNoClippedInteractiveControls(eventPage);
  const auditEventsResponse = eventPage.waitForResponse("**/api/v1/workflows/*/events");
  releaseAuditEvents();
  await auditEventsResponse;
  await eventPage.unroute("**/api/v1/workflows/*/events");
  await eventPage.close();
});

test("workflow and schema loading states preserve operational structure", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));

  await page.setViewportSize({ width: 1440, height: 900 });
  let releaseWorkflowSummary: () => void = () => undefined;
  const workflowSummaryDelay = new Promise<void>((resolve) => {
    releaseWorkflowSummary = resolve;
  });
  await page.route("**/api/v1/workflows/summary**", async (route) => {
    await workflowSummaryDelay;
    await route.continue();
  });
  await page.goto("/workflows");
  await expect(page.getByRole("status", { exact: true, name: "Loading Workflows" })).toBeVisible();
  await expect(page.getByLabel("Loading workflow queue")).toBeVisible();
  await expect(page.getByTestId("workflow-queue-skeleton-row")).toHaveCount(6);
  await expectNoHorizontalOverflow(page);
  await expectNoClippedInteractiveControls(page);
  const workflowSummaryResponse = page.waitForResponse("**/api/v1/workflows/summary**");
  releaseWorkflowSummary();
  await workflowSummaryResponse;
  await page.unroute("**/api/v1/workflows/summary**");

  let releaseSchemas: () => void = () => undefined;
  const schemasDelay = new Promise<void>((resolve) => {
    releaseSchemas = resolve;
  });
  await page.route("**/api/v1/schemas", async (route) => {
    await schemasDelay;
    await route.continue();
  });
  await page.goto("/schemas");
  await expect(page.getByRole("status", { exact: true, name: "Loading Profiles" })).toBeVisible();
  await expect(page.getByLabel("Loading schema registry")).toBeVisible();
  await expect(page.getByTestId("schema-registry-skeleton-row")).toHaveCount(4);
  await expect(page.getByTestId("schema-field-skeleton-row")).toHaveCount(5);
  await expectNoHorizontalOverflow(page);
  await expectNoClippedInteractiveControls(page);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/schemas");
  await expect(page.getByLabel("Loading schema registry")).toBeVisible();
  await expect(page.getByTestId("schema-field-skeleton-card")).toHaveCount(4);
  await expect(page.getByTestId("schema-field-skeleton-row").first()).toBeHidden();
  await expectNoHorizontalOverflow(page);
  await expectNoClippedInteractiveControls(page);
  const schemasResponse = page.waitForResponse("**/api/v1/schemas");
  releaseSchemas();
  await schemasResponse;
  await page.unroute("**/api/v1/schemas");
});

test("header refresh refetches server state without a full page reload", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  workflowIdsToCleanup.push(await createReviewWorkflow(context, baseURL));

  await page.goto("/workflows");
  await expect(page.getByRole("heading", { name: "Workflow operations" })).toBeVisible();
  await expect(page.getByText("1 run")).toBeVisible();
  await page.evaluate(() => {
    (window as Window & { __ojtflowRefreshMarker?: string }).__ojtflowRefreshMarker =
      "refresh-kept-spa-context";
  });

  const refreshResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/workflows/stats") &&
      response.request().method() === "GET" &&
      response.status() === 200,
  );
  await page.getByRole("button", { name: "Refresh application data" }).click();
  await refreshResponse;

  await expect(page).toHaveURL(/\/workflows$/);
  await expect(page.getByRole("heading", { name: "Workflow operations" })).toBeVisible();
  await expect(page.getByText("1 run")).toBeVisible();
  await expect
    .poll(() =>
      page.evaluate(
        () => (window as Window & { __ojtflowRefreshMarker?: string }).__ojtflowRefreshMarker,
      ),
    )
    .toBe("refresh-kept-spa-context");
});

test("secondary routes expose actionable operational content", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  workflowIdsToCleanup.push(await createReviewWorkflow(context, baseURL));

  await page.goto("/audit");
  await expect(page.getByRole("heading", { name: "Audit trails" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Audit packet" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Event timeline" })).toBeVisible();
  await expect(page.getByText("workflow.created").first()).toBeVisible();

  await page.goto("/reviews");
  await expect(page.getByText("Matching reviews", { exact: true })).toBeVisible();
  await expect(page.getByText("Issue load", { exact: true })).toBeVisible();
  await expect(page.getByText("Evidence refs", { exact: true })).toBeVisible();

  await page.goto("/schemas");
  await expect(page.getByRole("heading", { name: "Schema registry" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Registry search" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Required fields" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Field contract" })).toBeVisible();

  await page.goto("/workbench");
  await expect(page.getByRole("heading", { name: "Data intake" })).toBeVisible();
  await expect(page.getByText("Standard examples")).toBeVisible();
  await expect(page.getByText("Source data")).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/workbench");
  const schemaSummaryValue = page.locator('[data-summary-label="Schema"]').first();
  await expect(schemaSummaryValue).toHaveText("lab_result_v1");
  const schemaSummaryMetrics = await schemaSummaryValue.evaluate((element) => {
    const style = window.getComputedStyle(element);
    return {
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
      textOverflow: style.textOverflow,
    };
  });
  expect(schemaSummaryMetrics.textOverflow).not.toBe("ellipsis");
  expect(schemaSummaryMetrics.scrollWidth).toBeLessThanOrEqual(
    schemaSummaryMetrics.clientWidth + 1,
  );
  await expectRouteIntegrity(page);

  const runtimeConfigResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/runtime/config") &&
      response.request().method() === "GET" &&
      response.status() === 200,
  );
  const runtimeReadinessResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/runtime/readiness") &&
      response.request().method() === "GET" &&
      response.status() === 200,
  );
  await page.goto("/settings");
  await runtimeConfigResponse;
  await runtimeReadinessResponse;
  await expect(page.getByRole("heading", { name: "Runtime configuration" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Security posture" })).toBeVisible();
  await expect(page.getByText("API health", { exact: true })).toBeVisible();
  await expect(page.getByText("Storage backend", { exact: true })).toBeVisible();
  await expect(page.locator('[data-summary-label="Storage"]').first()).toHaveText("postgres");
  await expect(page.getByText("Readiness checks")).toBeVisible();
  await expect(page.getByText("workflow repository", { exact: true })).toBeVisible();
  await expect(page.getByText("retrieval inventory", { exact: true })).toBeVisible();
  await expect(page.getByText(/probe strategy postgres_fts_vector_rrf/)).toBeVisible();
  await expect(page.getByText(/probe hit count [1-9]/)).toBeVisible();
  await expect(page.getByText("Embedding")).toBeVisible();
  await expect(page.getByText("Upload limit")).toBeVisible();
  await expect(page.getByText("Inline data limit")).toBeVisible();
  await expect(page.getByText("OAuth client configuration")).toBeVisible();
  await expect(page.getByText("Cookie policy")).toBeVisible();
  const settingsText = await page.locator("body").innerText();
  expect(settingsText).not.toMatch(/postgresql:\/\/|GOCSPX|client_secret/i);
});
