import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { authenticateBrowser, type E2EAuthArtifacts } from "./support/auth";
import { cleanupAuthArtifacts, cleanupWorkflowArtifacts } from "./support/cleanup";
import { createReviewWorkflow, forceWorkflowResumeParseFailure } from "./support/workflows";

const e2eDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(e2eDir, "../..");
const messyCsvFixture = path.join(repoRoot, "data/fixtures/structured/lab_results_messy.csv");
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

test("workbench standard examples keep source, target, and sample data aligned", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  await page.goto("/workbench");

  await page.getByRole("button", { name: /json records/i }).click();
  await expect(page.getByLabel("Source format")).toHaveValue("json");
  await expect(page.getByLabel("Target format")).toHaveValue("yaml");
  await expect(page.getByLabel("Schema profile")).toHaveValue("lab_result_v1");
  await expect(page.getByLabel("Source data")).toHaveValue(/"patient_id"/);
  await expect(page.getByText("source json")).toBeVisible();

  await page.getByRole("button", { name: /yaml records/i }).click();
  await expect(page.getByLabel("Source format")).toHaveValue("yaml");
  await expect(page.getByLabel("Target format")).toHaveValue("json");
  await expect(page.getByLabel("Source data")).toHaveValue(/patient_id: P001/);
  await expect(page.getByText("source yaml")).toBeVisible();

  await page.getByRole("button", { name: /fhir observation/i }).click();
  await expect(page.getByLabel("Source format")).toHaveValue("json");
  await expect(page.getByLabel("Target format")).toHaveValue("json");
  await expect(page.getByLabel("Schema profile")).toHaveValue("");
  await expect(page.getByLabel("Source data")).toHaveValue(/"resourceType": "Observation"/);
  await expect(page.getByText("FHIR-like", { exact: true })).toBeVisible();
});

test("workbench links inspectable failed startup workflows", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  await page.goto("/workbench");

  await page.getByRole("button", { name: /json records/i }).click();
  await page.getByLabel("Source data").fill("{not valid json");
  const failedResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/workflows") &&
      response.request().method() === "POST" &&
      response.status() === 422,
  );
  await page.getByRole("button", { name: /start workflow/i }).click();
  const failedEnvelope = (await (await failedResponse).json()) as {
    error?: { workflow_id?: string | null } | null;
  };
  const workflowId = failedEnvelope.error?.workflow_id;
  if (!workflowId) throw new Error("Failed startup response did not include workflow_id.");
  workflowIdsToCleanup.push(workflowId);

  await expect(page.getByTestId("workflow-start-error")).toBeVisible();
  await page.getByTestId("open-failed-workflow").click();
  await expect(page).toHaveURL(new RegExp(`/workflows/${workflowId}$`));
  await expect(page.getByTestId("workflow-failure-notice")).toContainText("tool_execution_error");
});

test("workbench blocks blank pasted workflow fields before network submit", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  await page.goto("/workbench");

  let workflowPostCount = 0;
  page.on("request", (request) => {
    if (
      request.method() === "POST" &&
      request.url().includes("/api/v1/workflows")
    ) {
      workflowPostCount += 1;
    }
  });

  await page.getByLabel("Instruction").fill("   ");
  await page.getByRole("button", { name: /start workflow/i }).click();
  await expect(page.getByText("Workflow request blocked")).toBeVisible();
  await expect(page.getByText("Enter a workflow instruction before starting.")).toBeVisible();

  await page.getByLabel("Instruction").fill("Clean this CSV.");
  await page.getByLabel("Source data").fill(" \n\t ");
  await page.getByRole("button", { name: /start workflow/i }).click();
  await expect(page.getByText("Enter source data before starting a workflow.")).toBeVisible();
  expect(workflowPostCount).toBe(0);
});

test("authenticated user can run and approve a retrieval-backed workflow", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  await page.goto("/workbench");

  await expect(page.getByText("playwright-e2e-", { exact: false })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Workbench" })).toBeVisible();

  const workflowResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/workflows") &&
      response.request().method() === "POST" &&
      response.status() === 200,
  );
  await page.getByRole("button", { name: /start workflow/i }).click();
  const workflowEnvelope = (await (await workflowResponse).json()) as {
    data: { workflow_id: string; review?: { review_id: string } | null };
  };
  const workflowId = workflowEnvelope.data.workflow_id;
  workflowIdsToCleanup.push(workflowId);
  const reviewId = workflowEnvelope.data.review?.review_id;

  await expect(page).toHaveURL(new RegExp(`/workflows/${workflowId}$`), {
    timeout: 30_000,
  });
  await expect(page.getByRole("heading", { name: "Workflow detail" })).toBeVisible();
  await expect(page.getByRole("heading", { name: workflowId })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Decision required" })).toBeVisible();
  await expect(page.getByText("Field patient_id").first()).toBeVisible();
  await expect(page.getByText("Row 3").first()).toBeVisible();
  await expect(page.locator("text=/Field\\s+-/i")).toHaveCount(0);
  await expect(page.locator("span:visible", { hasText: /needs human review/i }).first()).toBeVisible();
  await expect(page.getByTestId("review-action-summary")).toBeVisible();
  await expect(page.getByText("8 actions")).toBeVisible();
  const patientIdAction = page.getByTestId("review-action-card").filter({ hasText: "patient_id" }).first();
  await expect(patientIdAction).toBeVisible();
  await expect(patientIdAction).toContainText("mask sensitive field for explanation");
  await expect(page.getByText(/more actions in the raw payload\./)).toBeVisible();
  await expect(page.getByTestId("review-raw-action-payload")).toBeHidden();
  await page.getByText("Raw action payload").click();
  await expect(page.getByTestId("review-raw-action-payload")).toBeVisible();
  await expect(page.getByTestId("review-raw-action-payload")).toContainText('"actions"');
  await expect(page.getByRole("button", { name: /approve with edits/i })).toHaveCount(0);

  await page.getByRole("tab", { name: "Evidence" }).click();
  await expect(page.getByText("Retrieval evidence")).toBeVisible();
  await expect(page.getByText("postgres_fts_vector_rrf")).toBeVisible();
  await expect(page.getByText("Retrieval safety flags")).toBeVisible();
  await expect(page.getByText("sensitive field context")).toBeVisible();

  await page.getByRole("tab", { name: "Audit" }).click();
  await expect(page.getByText("retrieval.completed")).toBeVisible();
  await expect(page.getByText("review.requested")).toBeVisible();

  await page.getByRole("tab", { name: "Review" }).click();
  await expect(page.getByRole("heading", { name: "Human review" })).toBeVisible();
  if (reviewId) {
    await expect(page.getByText(reviewId)).toBeVisible();
  }

  const reviewResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/review/") &&
      response.request().method() === "POST" &&
      response.status() === 200,
  );
  await page.getByRole("button", { name: /^approve$/i }).click({ force: true });
  await reviewResponse;

  await expect(page.getByText(/^completed$/i).first()).toBeVisible({
    timeout: 30_000,
  });
  await page.getByRole("tab", { name: "Output" }).click();
  await expect(page.getByRole("heading", { name: "Output artifact" })).toBeVisible();
  await expect(page.getByText("Artifact preview")).toBeVisible();
  await expect(page.getByText("[MASKED]").first()).toBeVisible();
  await expect(page.getByText("Output ref")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Explanation" })).toBeVisible();
  await page.getByRole("tab", { name: "Audit" }).click();
  await expect(page.getByText("workflow.completed")).toBeVisible();
});

test("authenticated user can request clarification and still approve the review", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  const workflowId = await createReviewWorkflow(context, baseURL);
  workflowIdsToCleanup.push(workflowId);

  await page.goto(`/workflows/${workflowId}`);
  await expect(page.getByRole("heading", { name: "Workflow detail" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Decision required" })).toBeVisible();

  const clarifyResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/review/") &&
      response.request().method() === "POST" &&
      response.status() === 200,
  );
  await page.getByRole("button", { name: /^clarify$/i }).click();
  await clarifyResponse;

  await expect(page.getByTestId("review-clarification-history")).toBeVisible();
  await expect(page.getByText("Clarification history")).toBeVisible();
  await expect(page.getByText("No additional payload.")).toBeVisible();
  await expect(page.getByText(/^pending$/i).first()).toBeVisible();

  await page.goto("/reviews");
  await expect(page.getByRole("table").getByText(workflowId)).toBeVisible();

  await page.goto(`/workflows/${workflowId}`);
  const approveResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/review/") &&
      response.request().method() === "POST" &&
      response.status() === 200,
  );
  await page.getByRole("button", { name: /^approve$/i }).click();
  await approveResponse;

  await expect(page.getByText(/^completed$/i).first()).toBeVisible({
    timeout: 30_000,
  });
  await page.getByRole("tab", { name: "Review" }).click();
  await expect(page.getByText("Clarification history")).toBeVisible();
  await page.getByRole("tab", { name: "Output" }).click();
  await expect(page.getByRole("heading", { name: "Output artifact" })).toBeVisible();
});

test("failed review resume refreshes workflow detail into failed state", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  const authArtifacts = await authenticateBrowser(context, baseURL);
  authArtifactsToCleanup.push(authArtifacts);
  if (!authArtifacts.userId) {
    throw new Error("Managed Playwright auth is required for workflow corruption fixture.");
  }
  const workflowId = await createReviewWorkflow(context, baseURL);
  workflowIdsToCleanup.push(workflowId);
  forceWorkflowResumeParseFailure(workflowId, authArtifacts.userId);

  await page.goto(`/workflows/${workflowId}`);
  await expect(page.getByRole("heading", { name: "Workflow detail" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Decision required" })).toBeVisible();

  const failedReviewResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/review/") &&
      response.request().method() === "POST" &&
      response.status() === 422,
  );
  await page.getByRole("button", { name: /^approve$/i }).click();
  const failedEnvelope = (await (await failedReviewResponse).json()) as {
    error?: { code?: string; workflow_id?: string | null } | null;
  };
  expect(failedEnvelope.error?.code).toBe("tool_execution_error");
  expect(failedEnvelope.error?.workflow_id).toBe(workflowId);

  const failureNotice = page.getByTestId("workflow-failure-notice");
  await expect(failureNotice).toBeVisible({ timeout: 30_000 });
  await expect(failureNotice).toContainText("tool_execution_error");
  await expect(page.getByText(/^failed$/i).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Decision required" })).toHaveCount(0);
});

test("authenticated user can upload a structured CSV workflow", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  await page.goto("/workbench");

  await page.getByRole("tab", { name: "Upload File" }).click();
  await page.locator('input[type="file"]').setInputFiles(messyCsvFixture);
  await expect(page.getByText("lab_results_messy.csv")).toBeVisible();

  const uploadResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/parse/upload/workflow") &&
      response.request().method() === "POST" &&
      response.status() === 200,
  );
  await page.getByRole("button", { name: /upload and start workflow/i }).click();
  const uploadEnvelope = (await (await uploadResponse).json()) as {
    data: { workflow_id: string };
  };
  const workflowId = uploadEnvelope.data.workflow_id;
  workflowIdsToCleanup.push(workflowId);

  await expect(page).toHaveURL(new RegExp(`/workflows/${workflowId}$`), {
    timeout: 30_000,
  });
  await expect(page.getByRole("heading", { name: workflowId })).toBeVisible();
  await expect(page.getByText("direct_text_upload")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Validation issues" })).toBeVisible();
});

test("workbench blocks blank upload instructions before network submit", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  await page.goto("/workbench");
  await page.getByRole("tab", { name: "Upload File" }).click();
  await page.locator('input[type="file"]').setInputFiles(messyCsvFixture);
  await page.getByLabel("Instruction").fill("   ");

  let uploadRequestCount = 0;
  page.on("request", (request) => {
    if (
      request.method() === "POST" &&
      request.url().includes("/api/v1/parse/upload/workflow")
    ) {
      uploadRequestCount += 1;
    }
  });

  await page.getByRole("button", { name: /upload and start workflow/i }).click();

  await expect(page.getByText("Upload request blocked")).toBeVisible();
  await expect(page.getByText("Enter an upload instruction before starting a workflow.")).toBeVisible();
  expect(uploadRequestCount).toBe(0);
});

test("workbench blocks oversized uploads before submission", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  const runtimeConfig = await context.request.get(`${baseURL}/api/v1/runtime/config`);
  expect(runtimeConfig.status()).toBe(200);
  const runtimeEnvelope = (await runtimeConfig.json()) as {
    data?: { upload?: { max_upload_bytes?: number } };
  };
  if (!runtimeEnvelope.data?.upload) {
    throw new Error("Runtime config response did not include upload settings.");
  }
  runtimeEnvelope.data.upload.max_upload_bytes = 4;

  await page.route("**/api/v1/runtime/config", async (route) => {
    await route.fulfill({
      body: JSON.stringify(runtimeEnvelope),
      contentType: "application/json",
      status: 200,
    });
  });

  await page.goto("/workbench");
  await page.getByRole("tab", { name: "Upload File" }).click();
  await page.locator('input[type="file"]').setInputFiles(messyCsvFixture);

  await expect(page.getByText(/file exceeds upload limit/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /upload and start workflow/i })).toBeDisabled();
});

test("workbench blocks unsupported upload types before submission", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  await page.goto("/workbench");
  await page.getByRole("tab", { name: "Upload File" }).click();
  await page.locator('input[type="file"]').setInputFiles({
    buffer: Buffer.from("not a supported upload"),
    mimeType: "application/octet-stream",
    name: "blocked.exe",
  });

  await expect(page.getByText(/unsupported file type \.exe/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /upload and start workflow/i })).toBeDisabled();
});

test("failed startup workflows remain inspectable from the error workflow id", async ({
  baseURL,
  context,
  page,
}) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL is required.");
  }

  authArtifactsToCleanup.push(await authenticateBrowser(context, baseURL));
  const response = await context.request.post(`${baseURL}/api/v1/workflows`, {
    headers: { Origin: new URL(baseURL).origin },
    data: {
      instruction: "Parse this JSON.",
      data: "{not valid json",
      input_format: "json",
      target_format: "json",
      schema_id: "lab_result_v1",
      require_human_review: true,
    },
  });
  expect(response.status()).toBe(422);
  const envelope = (await response.json()) as {
    error?: {
      code?: string;
      workflow_id?: string | null;
    } | null;
  };
  expect(envelope.error?.code).toBe("tool_execution_error");
  const workflowId = envelope.error?.workflow_id;
  if (!workflowId) throw new Error("Failed startup response did not include workflow_id.");
  workflowIdsToCleanup.push(workflowId);

  await page.goto(`/workflows/${workflowId}`);
  await expect(page.getByRole("heading", { name: "Workflow detail" })).toBeVisible();
  await expect(page.getByRole("heading", { name: workflowId })).toBeVisible();
  await expect(page.getByText(/^failed$/i).first()).toBeVisible();
  const failureNotice = page.getByTestId("workflow-failure-notice");
  await expect(failureNotice).toBeVisible();
  await expect(failureNotice).toContainText("Workflow failed");
  await expect(failureNotice).toContainText("tool_execution_error");
  await expect(failureNotice).toContainText("ToolExecutionError");
});

test("workflow queue keeps server sorting and viewport containment stable", async ({
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

  const sortResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/workflows/summary") &&
      response.url().includes("sort=issue_count") &&
      response.status() === 200,
  );
  await page.getByLabel("Sort").selectOption("issue_count");
  await sortResponse;

  const directionResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/workflows/summary") &&
      response.url().includes("sort=issue_count") &&
      response.url().includes("direction=asc") &&
      response.status() === 200,
  );
  await page.getByLabel("Direction").selectOption("asc");
  await directionResponse;

  await expect(page.getByText(/Showing \d+-\d+ of \d+/)).toBeVisible();
  const desktopOverflow = await page.evaluate(
    () => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) - window.innerWidth,
  );
  expect(desktopOverflow).toBeLessThanOrEqual(0);

  await page.setViewportSize({ width: 390, height: 844 });
  const mobileOverflow = await page.evaluate(
    () => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) - window.innerWidth,
  );
  expect(mobileOverflow).toBeLessThanOrEqual(0);
});
