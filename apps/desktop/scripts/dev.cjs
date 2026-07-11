/**
 * Development launcher for Rakshastra Desktop.
 *
 * 1. Compiles TypeScript (electron/*.ts -> dist-electron/*.js)
 * 2. Copies preload.js to dist-electron/
 * 3. Launches Electron pointing at the compiled main.js
 */

const { execSync, spawn } = require("child_process");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");

console.log("[dev] Compiling TypeScript...");
try {
  execSync("npx tsc -p tsconfig.json", { cwd: ROOT, stdio: "inherit" });
} catch {
  console.error("[dev] TypeScript compilation failed");
  process.exit(1);
}

console.log("[dev] Launching Electron...");
const electron = require("electron");
const electronPath = typeof electron === "string" ? electron : electron.default || electron;

const child = spawn(electronPath, [path.join(ROOT, "dist-electron", "main.js")], {
  cwd: ROOT,
  stdio: "inherit",
  env: {
    ...process.env,
    ELECTRON_IS_DEV: "1",
  },
});

child.on("exit", (code) => {
  process.exit(code || 0);
});
