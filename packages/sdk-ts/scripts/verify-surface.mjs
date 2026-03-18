/**
 * Surface verification: ObligationRuntimeClient must expose methods for every
 * catalog operation (parity with Python SDK and MCP). Run after build: node scripts/verify-surface.mjs
 * Reads built dist/client.js to avoid ESM resolution issues when run from scripts/.
 */
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const clientPath = join(__dirname, "..", "dist", "client.js");
const code = readFileSync(clientPath, "utf8");

const EXPECTED_METHODS = [
  "openEnvironment",
  "createSession",
  "applyPatch",
  "interactiveCheck",
  "getGoal",
  "hover",
  "definition",
  "batchVerify",
  "getReviewPayload",
  "createPendingReview",
  "submitReviewDecision",
  "resume",
];

let failed = false;
for (const name of EXPECTED_METHODS) {
  if (!code.includes(`${name}(`)) {
    console.error(`Missing method in built client: ${name}`);
    failed = true;
  }
}
if (failed) process.exit(1);
console.log("Surface verification OK: all", EXPECTED_METHODS.length, "methods present");
