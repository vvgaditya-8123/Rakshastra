"use strict";
/**
 * Self-contained background installer for the Rakshastra Python backend.
 *
 * Spawns the required setup processes (uv download, venv creation, uv sync, skills sync)
 * and streams logs back to the Electron window, allowing users to install the entire
 * platform from the GUI.
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.BackgroundInstaller = exports.INSTALL_STEPS = void 0;
const child_process_1 = require("child_process");
const fs_1 = require("fs");
const path_1 = require("path");
const os = __importStar(require("os"));
exports.INSTALL_STEPS = [
    { id: "env", label: "Creating environment configurations...", pct: 10 },
    { id: "uv", label: "Checking/Installing uv package manager...", pct: 25 },
    { id: "venv", label: "Creating virtual environment...", pct: 45 },
    { id: "deps", label: "Installing dependencies (may take 2-5 mins)...", pct: 75 },
    { id: "skills", label: "Syncing skills directory...", pct: 85 },
    { id: "path", label: "Configuring system PATH...", pct: 95 },
    { id: "verify", label: "Verifying installation...", pct: 100 },
];
class BackgroundInstaller {
    projectRoot;
    onLog;
    onProgress;
    onComplete;
    aborted = false;
    constructor(projectRoot, onLog, onProgress, onComplete) {
        this.projectRoot = projectRoot;
        this.onLog = onLog;
        this.onProgress = onProgress;
        this.onComplete = onComplete;
    }
    abort() {
        this.aborted = true;
    }
    log(msg, isErr = false) {
        this.onLog(msg, isErr);
    }
    progress(stepId) {
        const step = exports.INSTALL_STEPS.find(s => s.id === stepId);
        if (step) {
            this.onProgress(step.id, step.pct, step.label);
        }
    }
    async run() {
        try {
            this.log("Starting Rakshastra installation pipeline...");
            // Step 1: Env
            this.progress("env");
            await this.setupEnv();
            if (this.aborted)
                return;
            // Step 2: uv
            this.progress("uv");
            const uvPath = await this.setupUv();
            if (this.aborted)
                return;
            // Step 3: venv
            this.progress("venv");
            await this.setupVenv(uvPath);
            if (this.aborted)
                return;
            // Step 4: deps
            this.progress("deps");
            await this.setupDeps(uvPath);
            if (this.aborted)
                return;
            // Step 5: skills
            this.progress("skills");
            await this.setupSkills();
            if (this.aborted)
                return;
            // Step 6: path
            this.progress("path");
            await this.setupPath();
            if (this.aborted)
                return;
            // Step 7: verify
            this.progress("verify");
            const ok = await this.verify();
            this.onComplete(ok);
        }
        catch (err) {
            this.log(`\nERROR: Installation failed: ${err.message}`, true);
            this.onComplete(false);
        }
    }
    async setupEnv() {
        this.log("[1/7] Initializing .env configuration...");
        const envPath = (0, path_1.join)(this.projectRoot, ".env");
        if (!(0, fs_1.existsSync)(envPath)) {
            const examplePath = (0, path_1.join)(this.projectRoot, ".env.example");
            if ((0, fs_1.existsSync)(examplePath)) {
                const fs = require("fs");
                fs.copyFileSync(examplePath, envPath);
                this.log("  Created .env from .env.example");
            }
            else {
                (0, fs_1.writeFileSync)(envPath, "# Rakshastra Environment Configuration\n");
                this.log("  Created clean .env file");
            }
        }
        else {
            this.log("  .env already exists");
        }
    }
    async setupUv() {
        this.log("[2/7] Checking for uv package manager...");
        // Check if uv is on PATH
        try {
            (0, child_process_1.execSync)("uv --version", { stdio: "ignore" });
            this.log("  uv is already available on PATH");
            return "uv";
        }
        catch { }
        // Check common local install locations
        const home = os.homedir();
        const localCandidates = [
            (0, path_1.join)(home, ".local", "bin", "uv.exe"),
            (0, path_1.join)(home, ".cargo", "bin", "uv.exe"),
        ];
        for (const c of localCandidates) {
            if ((0, fs_1.existsSync)(c)) {
                this.log(`  uv found locally at: ${c}`);
                return `"${c}"`;
            }
        }
        this.log("  uv not found. Downloading and installing uv...");
        return new Promise((resolve, reject) => {
            const cmd = "powershell";
            const args = [
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "irm https://astral.sh/uv/install.ps1 | iex"
            ];
            const child = (0, child_process_1.spawn)(cmd, args, { windowsHide: true });
            child.stdout.on("data", (data) => this.log(`  ${data.toString().trim()}`));
            child.stderr.on("data", (data) => this.log(`  ${data.toString().trim()}`, true));
            child.on("close", (code) => {
                if (code === 0) {
                    // Re-check paths
                    for (const c of localCandidates) {
                        if ((0, fs_1.existsSync)(c)) {
                            this.log("  uv installed successfully");
                            resolve(`"${c}"`);
                            return;
                        }
                    }
                    resolve("uv");
                }
                else {
                    reject(new Error(`uv installation exited with code ${code}`));
                }
            });
        });
    }
    async setupVenv(uvPath) {
        this.log("[3/7] Setting up virtual environment (.venv)...");
        const venvDir = (0, path_1.join)(this.projectRoot, ".venv");
        if ((0, fs_1.existsSync)((0, path_1.join)(venvDir, "Scripts", "python.exe"))) {
            this.log("  Virtual environment (.venv) already exists");
            return;
        }
        return new Promise((resolve, reject) => {
            const args = ["venv", ".venv", "--python", "3.11"];
            this.log(`  Running: ${uvPath} ${args.join(" ")}`);
            const child = (0, child_process_1.spawn)(uvPath.replace(/"/g, ""), args, {
                cwd: this.projectRoot,
                windowsHide: true,
                shell: true
            });
            child.stdout.on("data", (data) => this.log(`  ${data.toString().trim()}`));
            child.stderr.on("data", (data) => this.log(`  ${data.toString().trim()}`));
            child.on("close", (code) => {
                if (code === 0) {
                    this.log("  Virtual environment created successfully");
                    resolve();
                }
                else {
                    // Retry without version pin
                    this.log("  Creating with default Python version...", true);
                    const child2 = (0, child_process_1.spawn)(uvPath.replace(/"/g, ""), ["venv", ".venv"], {
                        cwd: this.projectRoot,
                        windowsHide: true,
                        shell: true
                    });
                    child2.on("close", (code2) => {
                        if (code2 === 0) {
                            resolve();
                        }
                        else {
                            reject(new Error(`Failed to create venv (code ${code2})`));
                        }
                    });
                }
            });
        });
    }
    async setupDeps(uvPath) {
        this.log("[4/7] Installing dependencies (this will sync the environment)...");
        return new Promise((resolve, reject) => {
            const hasLock = (0, fs_1.existsSync)((0, path_1.join)(this.projectRoot, "uv.lock"));
            let args;
            if (hasLock) {
                this.log("  Using uv.lock for hash-locked sync...");
                args = ["sync", "--extra", "all", "--locked"];
            }
            else {
                this.log("  Lockfile missing, performing pip editable install...");
                args = ["pip", "install", "-e", ".[all]"];
            }
            this.log(`  Running: ${uvPath} ${args.join(" ")}`);
            const child = (0, child_process_1.spawn)(uvPath.replace(/"/g, ""), args, {
                cwd: this.projectRoot,
                windowsHide: true,
                shell: true,
                env: {
                    ...process.env,
                    UV_PROJECT_ENVIRONMENT: (0, path_1.join)(this.projectRoot, ".venv")
                }
            });
            child.stdout.on("data", (data) => {
                const line = data.toString().trim();
                if (line)
                    this.log(`  ${line}`);
            });
            child.stderr.on("data", (data) => {
                const line = data.toString().trim();
                if (line)
                    this.log(`  ${line}`);
            });
            child.on("close", (code) => {
                if (code === 0) {
                    this.log("  Dependencies installed successfully");
                    resolve();
                }
                else {
                    // Fallback to simpler pip install
                    this.log("  Lockfile sync failed, attempting standard pip install...", true);
                    const child2 = (0, child_process_1.spawn)(uvPath.replace(/"/g, ""), ["pip", "install", "-e", "."], {
                        cwd: this.projectRoot,
                        windowsHide: true,
                        shell: true,
                        env: {
                            ...process.env,
                            UV_PROJECT_ENVIRONMENT: (0, path_1.join)(this.projectRoot, ".venv")
                        }
                    });
                    child2.on("close", (code2) => {
                        if (code2 === 0) {
                            resolve();
                        }
                        else {
                            reject(new Error(`Dependency install failed (code ${code2})`));
                        }
                    });
                }
            });
        });
    }
    async setupSkills() {
        this.log("[5/7] Syncing agent skills...");
        const venvPy = (0, path_1.join)(this.projectRoot, ".venv", "Scripts", "python.exe");
        const syncScript = (0, path_1.join)(this.projectRoot, "tools", "skills_sync.py");
        if ((0, fs_1.existsSync)(venvPy) && (0, fs_1.existsSync)(syncScript)) {
            return new Promise((resolve) => {
                const child = (0, child_process_1.spawn)(venvPy, [syncScript], { windowsHide: true });
                child.stdout.on("data", (data) => this.log(`  ${data.toString().trim()}`));
                child.on("close", () => {
                    this.log("  Skills synced to user profile");
                    resolve();
                });
            });
        }
        else {
            this.log("  Skills sync script or venv python missing — skipping sync");
        }
    }
    async setupPath() {
        this.log("[6/7] Adding virtual environment to system PATH...");
        const venvScripts = (0, path_1.join)(this.projectRoot, ".venv", "Scripts");
        try {
            const psCmd = `
        $p = [Environment]::GetEnvironmentVariable('Path', 'User');
        if ($p -notlike '*${venvScripts.replace(/\\/g, "\\\\")}*') {
          [Environment]::SetEnvironmentVariable('Path', '${venvScripts};' + $p, 'User')
        }
      `;
            const child = (0, child_process_1.spawn)("powershell", ["-NoProfile", "-Command", psCmd], { windowsHide: true });
            child.on("close", (code) => {
                if (code === 0) {
                    this.log("  Added .venv\\Scripts to user PATH");
                }
                else {
                    this.log("  Failed to update user PATH (non-critical)", true);
                }
            });
        }
        catch (e) {
            this.log(`  Failed to write PATH: ${e.message}`, true);
        }
    }
    async verify() {
        this.log("[7/7] Verifying installation...");
        const checks = [
            "pyproject.toml",
            "run_agent.py",
            "cli.py",
            ".venv/Scripts/python.exe",
        ];
        let allOk = true;
        for (const c of checks) {
            if ((0, fs_1.existsSync)((0, path_1.join)(this.projectRoot, c))) {
                this.log(`  ✓ Checked ${c}`);
            }
            else {
                this.log(`  ✗ Missing ${c}`, true);
                allOk = false;
            }
        }
        if (allOk) {
            this.log("\n════════════════════════════════════════════════");
            this.log("  INSTALLATION SUCCESSFUL!");
            this.log("════════════════════════════════════════════════");
        }
        else {
            this.log("\n════════════════════════════════════════════════", true);
            this.log("  INSTALLATION FAILED!", true);
            this.log("════════════════════════════════════════════════", true);
        }
        return allOk;
    }
}
exports.BackgroundInstaller = BackgroundInstaller;
//# sourceMappingURL=installer.js.map