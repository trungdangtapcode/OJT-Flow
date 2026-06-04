import { rmSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(scriptDir, "..");
const artifactDirs = ["test-results", "playwright-report"];
const deleted = [];

for (const artifactDir of artifactDirs) {
  const artifactPath = path.join(frontendRoot, artifactDir);
  rmSync(artifactPath, { force: true, recursive: true });
  deleted.push(artifactDir);
}

console.log(JSON.stringify({ deleted_local_artifacts: deleted }, null, 2));
