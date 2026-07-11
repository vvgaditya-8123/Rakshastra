/**
 * Post-build step: ensure preload.js is in dist-electron/.
 * TypeScript compiles it there, but this script confirms it.
 */
const fs = require("fs");
const path = require("path");

const dist = path.join(__dirname, "..", "dist-electron");
const preload = path.join(dist, "preload.js");

if (!fs.existsSync(preload)) {
  console.error("[copy-preload] ERROR: preload.js not found in dist-electron/");
  console.error("[copy-preload] Run tsc first: npx tsc -p tsconfig.json");
  process.exit(1);
}

console.log("[copy-preload] preload.js present in dist-electron/");
