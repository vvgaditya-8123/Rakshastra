/**
 * Dynamic electron-builder wrapper.
 *
 * npm hoists packages non-deterministically, so a hardcoded electronDist
 * path in package.json silently breaks when the layout changes. This
 * script resolves the installed Electron's dist directory at build time
 * via require.resolve and passes it to electron-builder as a CLI override.
 *
 * Tests: test_desktop_electron_pin.py verifies this file exists and uses
 * require.resolve("electron/package.json") + -c.electronDist=.
 */

const path = require("path");
const { execSync } = require("child_process");

// Resolve the installed electron's package.json to find its dist directory.
// This works regardless of hoisting — require.resolve walks node_modules.
const electronPkgPath = require.resolve("electron/package.json");
const electronDir = path.dirname(electronPkgPath);
const electronDist = path.join(electronDir, "dist");

// Forward all CLI args to electron-builder, injecting the resolved dist.
const args = process.argv.slice(2);
const cmd = [
  "npx",
  "electron-builder",
  `-c.electronDist=${electronDist}`,
  ...args,
].join(" ");

console.log(`[electron-builder] electronDist: ${electronDist}`);
console.log(`[electron-builder] Running: ${cmd}`);

try {
  execSync(cmd, { stdio: "inherit", cwd: __dirname + "/.." });
} catch (err) {
  process.exit(err.status || 1);
}
