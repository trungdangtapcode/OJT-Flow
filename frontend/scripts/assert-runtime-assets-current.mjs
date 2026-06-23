import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(scriptDir, "..");
const expectedIndexPath = process.env.OJT_EXPECTED_FRONTEND_INDEX
  ? path.resolve(frontendRoot, process.env.OJT_EXPECTED_FRONTEND_INDEX)
  : null;
const expectedImage = process.env.OJT_EXPECTED_FRONTEND_IMAGE ?? "med-frontend";
const runtimeBaseURL = process.env.OJT_RUNTIME_BASE_URL ?? "http://localhost:15173";

function extractAssetRefs(html) {
  return [
    ...new Set(
      Array.from(html.matchAll(/\b(?:src|href)="(\/assets\/[^"]+)"/g), (match) => match[1]),
    ),
  ].sort();
}

function expectedIndexHtml() {
  if (expectedIndexPath) {
    try {
      return readFileSync(expectedIndexPath, "utf8");
    } catch (error) {
      throw new Error(
        [
          `Could not read expected frontend index: ${expectedIndexPath}`,
          error instanceof Error ? error.message : String(error),
        ].join("\n"),
      );
    }
  }

  try {
    return execFileSync(
      "docker",
      ["run", "--rm", expectedImage, "cat", "/usr/share/nginx/html/index.html"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
    );
  } catch (error) {
    const stderr =
      typeof error === "object" && error !== null && "stderr" in error
        ? String(error.stderr)
        : "";
    throw new Error(
      [
        `Could not read expected frontend index from Docker image ${expectedImage}.`,
        "Build it first with `docker compose build frontend` or set OJT_EXPECTED_FRONTEND_INDEX=dist/index.html.",
        stderr.trim(),
      ]
        .filter(Boolean)
        .join("\n"),
    );
  }
}

function compareRefs(expected, actual) {
  const expectedSet = new Set(expected);
  const actualSet = new Set(actual);
  return {
    missing: expected.filter((assetRef) => !actualSet.has(assetRef)),
    unexpected: actual.filter((assetRef) => !expectedSet.has(assetRef)),
  };
}

const expectedRefs = extractAssetRefs(expectedIndexHtml());
if (expectedRefs.length === 0) {
  throw new Error("Expected frontend index did not contain any /assets/ references.");
}

const response = await fetch(new URL("/", runtimeBaseURL), {
  headers: { "Cache-Control": "no-store" },
});
if (!response.ok) {
  throw new Error(`Runtime frontend returned HTTP ${response.status} from ${runtimeBaseURL}/`);
}

const runtimeHtml = await response.text();
const actualRefs = extractAssetRefs(runtimeHtml);
const diff = compareRefs(expectedRefs, actualRefs);
if (diff.missing.length || diff.unexpected.length) {
  throw new Error(
    [
      "Runtime frontend assets do not match the expected frontend build.",
      `Runtime: ${runtimeBaseURL}`,
      `Expected source: ${expectedIndexPath ?? `Docker image ${expectedImage}`}`,
      `Missing from runtime: ${diff.missing.join(", ") || "none"}`,
      `Unexpected in runtime: ${diff.unexpected.join(", ") || "none"}`,
      "Rebuild and recreate the frontend container with `docker compose up -d --build frontend`.",
    ].join("\n"),
  );
}

console.log(
  JSON.stringify(
    {
      status: "ok",
      runtime: runtimeBaseURL,
      asset_count: actualRefs.length,
    },
    null,
    2,
  ),
);
