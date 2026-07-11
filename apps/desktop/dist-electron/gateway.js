"use strict";
/**
 * Gateway — manages the Python Rakshastra backend as a child process.
 *
 * The desktop app spawns `rakshastra serve --no-open --port <port> --host 127.0.0.1`
 * and monitors it. When the Electron window closes, the gateway is killed.
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
exports.setLogger = setLogger;
exports.healthCheck = healthCheck;
exports.startGateway = startGateway;
exports.stopGateway = stopGateway;
exports.getPort = getPort;
exports.isRunning = isRunning;
const child_process_1 = require("child_process");
const fs_1 = require("fs");
const path_1 = require("path");
const http = __importStar(require("http"));
const DEFAULT_PORT = 9119;
const DEFAULT_HOST = "127.0.0.1";
const HEALTH_POLL_MS = 500;
const STARTUP_TIMEOUT_MS = 60_000;
let _child = null;
let _port = DEFAULT_PORT;
let _log = console.log;
function setLogger(fn) {
    _log = fn;
}
/** Find the Python executable for the project's venv. */
function findPython(projectRoot) {
    const candidates = [
        (0, path_1.join)(projectRoot, ".venv", "Scripts", "python.exe"),
        (0, path_1.join)(projectRoot, ".venv", "bin", "python"),
        (0, path_1.join)(projectRoot, "venv", "Scripts", "python.exe"),
        (0, path_1.join)(projectRoot, "venv", "bin", "python"),
    ];
    for (const p of candidates) {
        if ((0, fs_1.existsSync)(p))
            return p;
    }
    return null;
}
/** Find the rakshastra CLI entry point. */
function findRakshastraCli(projectRoot) {
    // Check if rakshastra is available as a script in the venv
    const venvScript = (0, path_1.join)(projectRoot, ".venv", "Scripts", "rakshastra.exe");
    if ((0, fs_1.existsSync)(venvScript))
        return venvScript;
    const venvScriptUnix = (0, path_1.join)(projectRoot, ".venv", "bin", "rakshastra");
    if ((0, fs_1.existsSync)(venvScriptUnix))
        return venvScriptUnix;
    return null;
}
/** Probe localhost:<port>/api/status to check if the server is up. */
function healthCheck(port, host) {
    return new Promise((resolve) => {
        const req = http.get({ hostname: host, port, path: "/api/status", timeout: 2000 }, (res) => {
            // Any 2xx means the server is alive
            resolve(res.statusCode !== undefined && res.statusCode >= 200 && res.statusCode < 400);
            res.resume();
        });
        req.on("error", () => resolve(false));
        req.on("timeout", () => {
            req.destroy();
            resolve(false);
        });
    });
}
/** Wait until the server responds or timeout. */
async function waitForServer(port, host, timeoutMs) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
        if (await healthCheck(port, host))
            return true;
        await new Promise((r) => setTimeout(r, HEALTH_POLL_MS));
    }
    return false;
}
/** Find a free port (asks the OS). */
function findFreePort() {
    return new Promise((resolve, reject) => {
        const srv = http.createServer();
        srv.listen(0, "127.0.0.1", () => {
            const addr = srv.address();
            if (addr && typeof addr === "object") {
                const port = addr.port;
                srv.close(() => resolve(port));
            }
            else {
                srv.close(() => reject(new Error("Could not find free port")));
            }
        });
        srv.on("error", reject);
    });
}
function killProcessOnPort(port) {
    if (process.platform !== "win32")
        return;
    try {
        const cmd = `netstat -ano | findstr :${port}`;
        const output = (0, child_process_1.execSync)(cmd).toString().trim();
        if (!output)
            return;
        const lines = output.split(/\r?\n/);
        for (const line of lines) {
            const parts = line.trim().split(/\s+/);
            const isListening = parts.includes("LISTENING");
            const pid = parts[parts.length - 1];
            if (pid && pid !== "0" && isListening) {
                _log(`[gateway] Port ${port} is occupied by PID ${pid}. Force-killing it...`);
                (0, child_process_1.execSync)(`taskkill /F /PID ${pid}`);
            }
        }
    }
    catch (err) {
        // Port might not be in use, which is normal
    }
}
/**
 * Start the Rakshastra backend gateway.
 *
 * 1. Checks if the server is already running on the default port.
 * 2. If not, spawns `rakshastra serve` (or `python -m rakshastra_cli.main serve`).
 * 3. Waits for the /api/status endpoint to respond.
 */
async function startGateway(opts) {
    const { projectRoot, onLog, onExit } = opts;
    const host = opts.host || DEFAULT_HOST;
    // Clean up any orphaned backend process on the default port
    killProcessOnPort(DEFAULT_PORT);
    // Check if already running on the default port
    _log("[gateway] Checking if server is already running...");
    if (await healthCheck(DEFAULT_PORT, host)) {
        _log(`[gateway] Server already running on port ${DEFAULT_PORT}`);
        _port = DEFAULT_PORT;
        return {
            port: DEFAULT_PORT,
            host,
            pid: null,
            url: `http://${host}:${DEFAULT_PORT}`,
        };
    }
    // Find port
    let port = opts.port || DEFAULT_PORT;
    if (await isPortInUse(port, host)) {
        _log(`[gateway] Port ${port} in use, finding a free port...`);
        port = await findFreePort();
    }
    _port = port;
    // Find the rakshastra CLI or Python
    const cliPath = findRakshastraCli(projectRoot);
    const pythonPath = findPython(projectRoot);
    let cmd;
    let args;
    if (cliPath) {
        cmd = cliPath;
        args = ["serve", "--no-open", "--port", String(port), "--host", host, "--skip-build"];
        _log(`[gateway] Using CLI: ${cmd}`);
    }
    else if (pythonPath) {
        cmd = pythonPath;
        args = ["-m", "rakshastra_cli.main", "serve", "--no-open", "--port", String(port), "--host", host, "--skip-build"];
        _log(`[gateway] Using Python: ${cmd}`);
    }
    else {
        throw new Error("Could not find rakshastra CLI or Python venv. " +
            "Run the setup wizard first to install dependencies.");
    }
    _log(`[gateway] Starting: ${cmd} ${args.join(" ")}`);
    _child = (0, child_process_1.spawn)(cmd, args, {
        cwd: projectRoot,
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true,
        env: {
            ...process.env,
            // Ensure the server knows it's being launched by the desktop app
            RAKSHASTRA_DESKTOP: "1",
            // Force skip browser open
            BROWSER: "none",
        },
    });
    _child.stdout?.on("data", (data) => {
        const lines = data.toString().split("\n").filter(Boolean);
        for (const line of lines) {
            _log(`[server] ${line}`);
            if (onLog)
                onLog(line);
        }
    });
    _child.stderr?.on("data", (data) => {
        const lines = data.toString().split("\n").filter(Boolean);
        for (const line of lines) {
            _log(`[server:err] ${line}`);
            if (onLog)
                onLog(line);
        }
    });
    _child.on("exit", (code) => {
        _log(`[gateway] Process exited with code ${code}`);
        _child = null;
        if (onExit)
            onExit(code);
    });
    _child.on("error", (err) => {
        _log(`[gateway] Process error: ${err.message}`);
        _child = null;
    });
    // Wait for the server to become ready
    _log(`[gateway] Waiting for server on port ${port}...`);
    const ready = await waitForServer(port, host, STARTUP_TIMEOUT_MS);
    if (!ready) {
        // Check if the process is still alive
        if (_child && !_child.killed) {
            _log("[gateway] Server didn't respond in time, but process is still running. Continuing...");
        }
        else {
            throw new Error("Rakshastra backend failed to start. Check that dependencies are installed.");
        }
    }
    _log(`[gateway] Server ready at http://${host}:${port}`);
    return {
        port,
        host,
        pid: _child?.pid ?? null,
        url: `http://${host}:${port}`,
    };
}
/** Check if a port is already in use. */
function isPortInUse(port, host) {
    return new Promise((resolve) => {
        const srv = http.createServer();
        srv.once("error", (err) => {
            resolve(err.code === "EADDRINUSE");
        });
        srv.once("listening", () => {
            srv.close(() => resolve(false));
        });
        srv.listen(port, host);
    });
}
/** Stop the gateway child process. */
async function stopGateway() {
    if (!_child)
        return;
    _log("[gateway] Stopping backend...");
    return new Promise((resolve) => {
        if (!_child) {
            resolve();
            return;
        }
        const timeout = setTimeout(() => {
            _log("[gateway] Force-killing after timeout");
            if (_child) {
                _child.kill("SIGKILL");
            }
            resolve();
        }, 5000);
        _child.once("exit", () => {
            clearTimeout(timeout);
            _child = null;
            _log("[gateway] Backend stopped");
            resolve();
        });
        // On Windows, SIGTERM doesn't work well — use taskkill
        if (process.platform === "win32" && _child.pid) {
            (0, child_process_1.spawn)("taskkill", ["/pid", String(_child.pid), "/T", "/F"], {
                windowsHide: true,
            });
        }
        else {
            _child.kill("SIGTERM");
        }
    });
}
function getPort() {
    return _port;
}
function isRunning() {
    return _child !== null && !_child.killed;
}
//# sourceMappingURL=gateway.js.map