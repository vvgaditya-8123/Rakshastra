"use strict";
/**
 * Rakshastra Desktop — Electron main process.
 *
 * Creates the application window, auto-starts the Python gateway backend,
 * and loads the web dashboard once the backend is ready.
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
const electron_1 = require("electron");
const path = __importStar(require("path"));
const gateway_1 = require("./gateway");
const installer_1 = require("./installer");
// ── Paths ────────────────────────────────────────────────────────────────
const IS_DEV = !electron_1.app.isPackaged;
function findProjectRoot(startPath) {
    let current = startPath;
    const fs = require("fs");
    while (true) {
        if (fs.existsSync(path.join(current, "pyproject.toml"))) {
            return current;
        }
        const parent = path.dirname(current);
        if (parent === current) {
            return startPath; // Reached root, fallback
        }
        current = parent;
    }
}
const ROOT_DIR = IS_DEV
    ? findProjectRoot(__dirname)
    : path.join(process.resourcesPath, "backend");
const PRELOAD_PATH = path.join(__dirname, "preload.js");
const ICON_PATH = path.join(ROOT_DIR, "assets", "logo.png");
// ── State ────────────────────────────────────────────────────────────────
let mainWindow = null;
let tray = null;
let gatewayInfo = null;
let isQuitting = false;
let startupLogs = [];
// ── Logging ──────────────────────────────────────────────────────────────
function log(msg) {
    const ts = new Date().toISOString().slice(11, 19);
    const formatted = `[${ts}] ${msg}`;
    console.log(formatted);
    startupLogs.push(formatted);
    // Keep last 500 lines
    if (startupLogs.length > 500)
        startupLogs.shift();
}
(0, gateway_1.setLogger)(log);
// ── Single instance lock ─────────────────────────────────────────────────
const gotLock = electron_1.app.requestSingleInstanceLock();
if (!gotLock) {
    electron_1.app.quit();
}
else {
    electron_1.app.on("second-instance", () => {
        if (mainWindow) {
            if (mainWindow.isMinimized())
                mainWindow.restore();
            mainWindow.focus();
        }
    });
}
// ── Window ───────────────────────────────────────────────────────────────
function createWindow() {
    const win = new electron_1.BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 900,
        minHeight: 600,
        title: "Rakshastra",
        icon: ICON_PATH,
        backgroundColor: "#0a0a1a",
        show: false, // Show after content loads
        webPreferences: {
            preload: PRELOAD_PATH,
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: false,
            webSecurity: true,
        },
        // Frameless for custom titlebar (optional — use frame: true if preferred)
        frame: true,
        titleBarStyle: "default",
    });
    mainWindow = win;
    // Show splash/loading state
    win.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(getSplashHTML())}`);
    win.show();
    // Handle external links — open in system browser
    win.webContents.setWindowOpenHandler(({ url }) => {
        if (url.startsWith("http")) {
            electron_1.shell.openExternal(url);
        }
        return { action: "deny" };
    });
    // Intercept navigation to external URLs
    win.webContents.on("will-navigate", (event, url) => {
        const serverUrl = `http://127.0.0.1:${(0, gateway_1.getPort)()}`;
        if (!url.startsWith(serverUrl) && !url.startsWith("data:")) {
            event.preventDefault();
            electron_1.shell.openExternal(url);
        }
    });
    // Minimize to tray instead of closing (on Windows)
    win.on("close", (event) => {
        if (!isQuitting && process.platform === "win32") {
            event.preventDefault();
            win.hide();
        }
    });
    win.on("closed", () => {
        mainWindow = null;
    });
    return win;
}
// ── Splash screen HTML ───────────────────────────────────────────────────
function getSplashHTML() {
    return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0a0a1a;
    color: #e0e0e0;
    font-family: 'Segoe UI', -apple-system, sans-serif;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    overflow: hidden;
  }
  .container {
    text-align: center;
    animation: fadeIn 0.6s ease;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .logo {
    font-size: 48px;
    font-weight: 800;
    background: linear-gradient(135deg, #e94560, #c23152, #8b1a3a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 16px;
    letter-spacing: -1px;
  }
  .subtitle {
    font-size: 14px;
    color: #666;
    margin-bottom: 40px;
    letter-spacing: 4px;
    text-transform: uppercase;
  }
  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #1a1a2e;
    border-top-color: #e94560;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto 20px;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  .status {
    font-size: 13px;
    color: #555;
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }
  .grid-bg {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
      linear-gradient(rgba(233,69,96,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(233,69,96,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
  }
</style>
</head>
<body>
  <div class="grid-bg"></div>
  <div class="container">
    <div class="logo">RAKSHASTRA</div>
    <div class="subtitle">Cyber Defense Agent</div>
    <div class="spinner"></div>
    <div class="status" id="status">Starting backend...</div>
  </div>
</body>
</html>`;
}
// ── Setup Wizard HTML ──────────────────────────────────────────────────
function getSetupHTML() {
    return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #060610;
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, system-ui, sans-serif;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    overflow: hidden;
  }
  .container {
    width: 650px;
    background: rgba(10, 10, 26, 0.6);
    border: 1px solid rgba(233, 69, 96, 0.2);
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(233, 69, 96, 0.15);
    animation: zoomIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  }
  @keyframes zoomIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
  }
  .logo-area {
    text-align: center;
    margin-bottom: 24px;
  }
  .logo {
    font-size: 32px;
    font-weight: 800;
    background: linear-gradient(135deg, #e94560, #c23152, #8b1a3a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
  }
  .subtitle {
    font-size: 11px;
    color: #555;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4px;
  }
  .title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 8px;
    color: #fff;
  }
  .desc {
    font-size: 13px;
    color: #8892b0;
    line-height: 1.6;
    margin-bottom: 20px;
  }
  .progress-container {
    margin-bottom: 20px;
    display: none;
  }
  .progress-label-row {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    margin-bottom: 8px;
    color: #8892b0;
  }
  .progress-bar-bg {
    width: 100%;
    height: 6px;
    background: #1a1a2e;
    border-radius: 3px;
    overflow: hidden;
  }
  .progress-bar-fill {
    width: 0%;
    height: 100%;
    background: linear-gradient(90deg, #e94560, #ff6b8b);
    transition: width 0.3s ease;
  }
  .console {
    width: 100%;
    height: 180px;
    background: #020208;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 12px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    line-height: 1.5;
    color: #4ade80;
    overflow-y: auto;
    margin-bottom: 20px;
    display: none;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .btn {
    display: block;
    width: 100%;
    padding: 12px;
    background: #e94560;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: center;
    margin-top: 10px;
  }
  .btn:hover {
    background: #ff5773;
    box-shadow: 0 0 12px rgba(233, 69, 96, 0.4);
  }
  .btn:disabled {
    background: #252538;
    color: #666;
    cursor: not-allowed;
    box-shadow: none;
  }
  .grid-bg {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
      linear-gradient(rgba(233,69,96,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(233,69,96,0.02) 1px, transparent 1px);
    background-size: 30px 30px;
    pointer-events: none;
  }
  .form-group {
    margin-bottom: 16px;
    text-align: left;
  }
  .form-label {
    display: block;
    font-size: 13px;
    color: #8892b0;
    margin-bottom: 6px;
    font-weight: 500;
  }
  .form-control {
    width: 100%;
    padding: 10px 12px;
    background: #0d0d1e;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    color: #fff;
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s ease;
  }
  .form-control:focus {
    border-color: #e94560;
  }
  .checkbox-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 10px;
  }
  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #8892b0;
    cursor: pointer;
  }
  .checkbox-label input {
    accent-color: #e94560;
    width: 16px;
    height: 16px;
  }
</style>
</head>
<body>
  <div class="grid-bg"></div>
  <div class="container">
    <div class="logo-area">
      <div class="logo">RAKSHASTRA</div>
      <div class="subtitle">Agent Core Setup</div>
    </div>
    
    <div id="welcome-view">
      <div class="title">Python Environment Required</div>
      <div class="desc">
        To power the local AI agent, we need to set up a Python virtual environment (.venv) and install the core dependencies. This installer will download 'uv' (a fast package manager), set up your workspace, copy default skills, and configure your path.
      </div>
      <button class="btn" id="btn-start" onclick="startInstallation()">Install Agent Backend</button>
    </div>

    <div id="install-view" style="display:none;">
      <div class="progress-container" id="progress-container" style="display:block;">
        <div class="progress-label-row">
          <span id="progress-label">Preparing installer...</span>
          <span id="progress-percent">0%</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" id="progress-bar"></div>
        </div>
      </div>

      <div class="console" id="console" style="display:block;"></div>
      
      <button class="btn" id="btn-fail" style="display:none;" onclick="window.location.reload()">Retry Installation</button>
    </div>

    <div id="config-view" style="display:none;">
      <div class="title">Configure AI Agent & Platforms</div>
      <div class="desc">Specify your model provider, API key, and select which communication channels to activate for the gateway. You can change these details later in the dashboard.</div>
      
      <div class="form-group">
        <label class="form-label" for="select-provider">AI Model Provider</label>
        <select class="form-control" id="select-provider" onchange="onProviderChange()">
          <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
          <option value="gemini">Google Gemini (Gemini 1.5 Pro/Flash)</option>
          <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
          <option value="openrouter">OpenRouter (Universal API Hub)</option>
          <option value="deepseek">DeepSeek API (api.deepseek.com)</option>
          <option value="ollama-cloud">Ollama Cloud (ollama.com)</option>
          <option value="custom">Local Ollama / Llama (Localhost)</option>
        </select>
      </div>

      <div class="form-group" id="group-base-url" style="display:none;">
        <label class="form-label" for="input-base-url">API Base URL</label>
        <input class="form-control" type="text" id="input-base-url" placeholder="http://localhost:11434/v1" value="http://localhost:11434/v1">
      </div>

      <div class="form-group" id="group-key">
        <label class="form-label" for="input-key" id="label-key">OpenAI API Key</label>
        <input class="form-control" type="password" id="input-key" placeholder="Paste your API key here (sk-...)">
      </div>

      <div class="form-group">
        <label class="form-label">Enable Platform Channels</label>
        <div class="checkbox-grid">
          <label class="checkbox-label">
            <input type="checkbox" id="chk-cli" checked> CLI Terminal Interface
          </label>
          <label class="checkbox-label">
            <input type="checkbox" id="chk-telegram"> Telegram Bot Integration
          </label>
          <label class="checkbox-label">
            <input type="checkbox" id="chk-slack"> Slack App Integration
          </label>
          <label class="checkbox-label">
            <input type="checkbox" id="chk-discord"> Discord Bot Integration
          </label>
        </div>
      </div>

      <button class="btn" id="btn-save" onclick="saveConfiguration()">Save & Launch App</button>
    </div>
  </div>

  <script>
    const desktop = window.rakshastraDesktop;

    function startInstallation() {
      document.getElementById('welcome-view').style.display = 'none';
      document.getElementById('install-view').style.display = 'block';
      
      if (desktop) {
        desktop.startInstall();
      } else {
        addLog('ERROR: Desktop bridge not found.', true);
      }
    }

    function addLog(text, isErr) {
      const consoleEl = document.getElementById('console');
      if (!consoleEl) return;
      const line = document.createElement('div');
      if (isErr) line.style.color = '#f87171';
      line.innerText = text;
      consoleEl.appendChild(line);
      consoleEl.scrollTop = consoleEl.scrollHeight;
    }

    function updateProgress(pct, label) {
      document.getElementById('progress-bar').style.width = pct + '%';
      document.getElementById('progress-percent').innerText = pct + '%';
      document.getElementById('progress-label').innerText = label;
    }

    function onProviderChange() {
      const provider = document.getElementById('select-provider').value;
      const label = document.getElementById('label-key');
      const input = document.getElementById('input-key');
      const baseUrlGroup = document.getElementById('group-base-url');
      const keyGroup = document.getElementById('group-key');
      
      // Hide base URL override by default
      baseUrlGroup.style.display = 'none';
      keyGroup.style.display = 'block';
      
      if (provider === 'openai') {
        label.innerText = 'OpenAI API Key';
        input.placeholder = 'sk-...';
      } else if (provider === 'gemini') {
        label.innerText = 'Google Gemini API Key';
        input.placeholder = 'AIzaSy...';
      } else if (provider === 'anthropic') {
        label.innerText = 'Anthropic API Key';
        input.placeholder = 'sk-ant-...';
      } else if (provider === 'openrouter') {
        label.innerText = 'OpenRouter API Key';
        input.placeholder = 'sk-or-...';
      } else if (provider === 'deepseek') {
        label.innerText = 'DeepSeek API Key';
        input.placeholder = 'sk-...';
      } else if (provider === 'ollama-cloud') {
        label.innerText = 'Ollama Cloud API Key';
        input.placeholder = 'Paste your Ollama Cloud key';
      } else if (provider === 'custom') {
        baseUrlGroup.style.display = 'block';
        label.innerText = 'API Key (Optional)';
        input.placeholder = 'Leave empty if no auth is required';
      }
    }

    // Set up custom listeners from preload script
    window.addEventListener('setup-log', (e) => {
      addLog(e.detail.text, e.detail.isErr);
    });

    window.addEventListener('setup-progress', (e) => {
      updateProgress(e.detail.pct, e.detail.label);
    });

    window.addEventListener('setup-complete', (e) => {
      if (e.detail.success) {
        updateProgress(100, 'Installation complete!');
        // Small delay, then show configuration screen
        setTimeout(() => {
          document.getElementById('install-view').style.display = 'none';
          document.getElementById('config-view').style.display = 'block';
          onProviderChange(); // Initialize view state
        }, 800);
      } else {
        updateProgress(100, 'Installation failed.');
        document.getElementById('btn-fail').style.display = 'block';
      }
    });

    async function saveConfiguration() {
      const provider = document.getElementById('select-provider').value;
      const apiKey = document.getElementById('input-key').value.trim();
      const baseUrl = document.getElementById('input-base-url').value.trim();
      const cli = document.getElementById('chk-cli').checked;
      const telegram = document.getElementById('chk-telegram').checked;
      const slack = document.getElementById('chk-slack').checked;
      const discord = document.getElementById('chk-discord').checked;

      const btn = document.getElementById('btn-save');
      btn.disabled = true;
      btn.innerText = 'Saving Configuration...';

      const config = {
        provider,
        apiKey,
        baseUrl,
        platforms: {
          cli,
          telegram,
          slack,
          discord
        }
      };

      if (desktop) {
        try {
          await desktop.saveConfig(config);
          desktop.launchApp();
        } catch (err) {
          alert('Failed to save configuration: ' + err.message);
          btn.disabled = false;
          btn.innerText = 'Save & Launch App';
        }
      }
    }
  </script>
</body>
</html>`;
}
let apiStatus = "OFFLINE";
let statusInterval = null;
function updateTrayMenu() {
    if (!tray)
        return;
    const statusLabel = apiStatus === "NOMINAL"
        ? "● Core Status: NOMINAL"
        : apiStatus === "DEGRADED"
            ? "▲ Core Status: DEGRADED"
            : "○ Core Status: OFFLINE";
    const contextMenu = electron_1.Menu.buildFromTemplate([
        {
            label: statusLabel,
            enabled: false,
        },
        { type: "separator" },
        {
            label: "Show Rakshastra",
            click: () => {
                mainWindow?.show();
                mainWindow?.focus();
            },
        },
        { type: "separator" },
        {
            label: "Restart Backend",
            click: async () => {
                log("[tray] Restart requested");
                await (0, gateway_1.stopGateway)();
                await launchGateway();
            },
        },
        { type: "separator" },
        {
            label: "Quit",
            click: () => {
                isQuitting = true;
                electron_1.app.quit();
            },
        },
    ]);
    tray.setContextMenu(contextMenu);
    tray.setToolTip(`Rakshastra Agent (${apiStatus})`);
}
function startStatusPolling() {
    if (statusInterval)
        clearInterval(statusInterval);
    statusInterval = setInterval(async () => {
        const port = (0, gateway_1.getPort)();
        try {
            const isUp = await (0, gateway_1.healthCheck)(port, "127.0.0.1");
            if (isUp) {
                const http = require("http");
                const req = http.get({ hostname: "127.0.0.1", port, path: "/api/v1/status", timeout: 2000 }, (res) => {
                    let data = "";
                    res.on("data", (chunk) => { data += chunk; });
                    res.on("end", () => {
                        try {
                            const json = JSON.parse(data);
                            if (json && json.status === "NOMINAL") {
                                apiStatus = "NOMINAL";
                            }
                            else {
                                apiStatus = "DEGRADED";
                            }
                        }
                        catch (err) {
                            apiStatus = "NOMINAL"; // Nominal if server is up but response format differs
                        }
                        updateTrayMenu();
                    });
                });
                req.on("error", () => {
                    apiStatus = "NOMINAL"; // nominal fallback if healthCheck is true but get fails
                    updateTrayMenu();
                });
                req.on("timeout", () => {
                    req.destroy();
                    apiStatus = "NOMINAL";
                    updateTrayMenu();
                });
            }
            else {
                apiStatus = "OFFLINE";
                updateTrayMenu();
            }
        }
        catch {
            apiStatus = "OFFLINE";
            updateTrayMenu();
        }
    }, 5000);
}
// ── System tray ──────────────────────────────────────────────────────────
function createTray() {
    try {
        let icon;
        const fs = require("fs");
        if (fs.existsSync(ICON_PATH)) {
            icon = electron_1.nativeImage.createFromPath(ICON_PATH).resize({ width: 16, height: 16 });
        }
        else {
            // Create a simple colored icon as fallback
            icon = electron_1.nativeImage.createEmpty();
        }
        tray = new electron_1.Tray(icon);
        updateTrayMenu();
        startStatusPolling();
        tray.on("double-click", () => {
            mainWindow?.show();
            mainWindow?.focus();
        });
    }
    catch (err) {
        log(`[tray] Failed to create tray: ${err}`);
    }
}
// ── Gateway launch ───────────────────────────────────────────────────────
async function launchGateway() {
    try {
        updateSplashStatus("Starting Rakshastra backend...");
        gatewayInfo = await (0, gateway_1.startGateway)({
            projectRoot: ROOT_DIR,
            onLog: (line) => {
                // Update splash screen with server output
                if (line.includes("Running on")) {
                    updateSplashStatus("Server ready! Loading dashboard...");
                }
            },
            onExit: (code) => {
                log(`[main] Backend exited with code ${code}`);
                if (!isQuitting && mainWindow) {
                    // Show error and offer restart
                    electron_1.dialog.showMessageBox(mainWindow, {
                        type: "error",
                        title: "Backend Stopped",
                        message: "The Rakshastra backend has stopped unexpectedly.",
                        buttons: ["Restart", "Quit"],
                    }).then((result) => {
                        if (result.response === 0) {
                            launchGateway();
                        }
                        else {
                            isQuitting = true;
                            electron_1.app.quit();
                        }
                    });
                }
            },
        });
        // Load the web dashboard
        if (mainWindow && gatewayInfo) {
            log(`[main] Loading dashboard from ${gatewayInfo.url}`);
            updateSplashStatus("Loading dashboard...");
            // Small delay to ensure the server is fully ready
            await new Promise((r) => setTimeout(r, 500));
            mainWindow.loadURL(gatewayInfo.url);
            // Show window when content is loaded
            mainWindow.webContents.once("did-finish-load", () => {
                log("[main] Dashboard loaded");
            });
        }
    }
    catch (err) {
        log(`[main] Failed to start gateway: ${err.message}`);
        if (mainWindow) {
            log("[main] Venv or backend not detected. Redirecting to GUI setup wizard...");
            mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(getSetupHTML())}`);
        }
    }
}
function updateSplashStatus(text) {
    if (mainWindow) {
        mainWindow.webContents
            .executeJavaScript(`document.getElementById('status') && (document.getElementById('status').textContent = ${JSON.stringify(text)})`)
            .catch(() => { });
    }
}
// ── IPC handlers ─────────────────────────────────────────────────────────
function setupIPC() {
    electron_1.ipcMain.on("get-app-version", (event) => {
        event.returnValue = electron_1.app.getVersion();
    });
    electron_1.ipcMain.on("window-minimize", () => mainWindow?.minimize());
    electron_1.ipcMain.on("window-maximize", () => {
        if (mainWindow?.isMaximized()) {
            mainWindow.unmaximize();
        }
        else {
            mainWindow?.maximize();
        }
    });
    electron_1.ipcMain.on("window-close", () => mainWindow?.close());
    electron_1.ipcMain.on("window-toggle-fullscreen", () => {
        if (mainWindow) {
            mainWindow.setFullScreen(!mainWindow.isFullScreen());
        }
    });
    electron_1.ipcMain.on("open-external", (_event, url) => {
        if (typeof url === "string" && url.startsWith("http")) {
            electron_1.shell.openExternal(url);
        }
    });
    electron_1.ipcMain.on("open-devtools", () => {
        mainWindow?.webContents.openDevTools();
    });
    electron_1.ipcMain.handle("get-gateway-info", () => {
        return {
            ...gatewayInfo,
            running: (0, gateway_1.isRunning)(),
            logs: startupLogs.slice(-50),
        };
    });
    electron_1.ipcMain.handle("restart-gateway", async () => {
        await (0, gateway_1.stopGateway)();
        await launchGateway();
        return { ok: true };
    });
    electron_1.ipcMain.on("setup-start-install", () => {
        log("[main] Starting background installation...");
        const installer = new installer_1.BackgroundInstaller(ROOT_DIR, (text, isErr) => {
            mainWindow?.webContents.send("setup-log", { text, isErr });
        }, (stepId, pct, label) => {
            mainWindow?.webContents.send("setup-progress", { stepId, pct, label });
        }, (success) => {
            mainWindow?.webContents.send("setup-complete", { success });
        });
        installer.run();
    });
    electron_1.ipcMain.on("setup-launch-app", () => {
        log("[main] Launching application after setup...");
        launchGateway();
    });
    electron_1.ipcMain.handle("setup-save-config", async (event, data) => {
        log("[main] Saving setup configuration...");
        const fs = require("fs");
        // 1. Save API key to .env
        const envPath = path.join(ROOT_DIR, ".env");
        let envContent = "";
        if (fs.existsSync(envPath)) {
            envContent = fs.readFileSync(envPath, "utf8");
        }
        // Determine appropriate env var name
        let keyVar = "";
        if (data.provider === "openai")
            keyVar = "OPENAI_API_KEY";
        else if (data.provider === "gemini")
            keyVar = "GEMINI_API_KEY";
        else if (data.provider === "anthropic")
            keyVar = "ANTHROPIC_API_KEY";
        else if (data.provider === "openrouter")
            keyVar = "OPENROUTER_API_KEY";
        else if (data.provider === "ollama-cloud")
            keyVar = "OLLAMA_API_KEY";
        else if (data.provider === "deepseek")
            keyVar = "DEEPSEEK_API_KEY";
        else if (data.provider === "custom")
            keyVar = "CUSTOM_API_KEY";
        if (keyVar) {
            const apiKeyVal = data.apiKey || (data.provider === "custom" ? "none" : "");
            const regex = new RegExp(`^${keyVar}=.*$`, "m");
            if (regex.test(envContent)) {
                envContent = envContent.replace(regex, `${keyVar}=${apiKeyVal}`);
            }
            else {
                envContent += `\n${keyVar}=${apiKeyVal}\n`;
            }
            log(`[main] Saved ${keyVar} to .env`);
        }
        // Save custom base URL to .env if applicable
        if (data.provider === "custom" && data.baseUrl) {
            const urlVar = "CUSTOM_BASE_URL";
            const regex = new RegExp(`^${urlVar}=.*$`, "m");
            if (regex.test(envContent)) {
                envContent = envContent.replace(regex, `${urlVar}=${data.baseUrl}`);
            }
            else {
                envContent += `\n${urlVar}=${data.baseUrl}\n`;
            }
            log(`[main] Saved ${urlVar} to .env`);
        }
        fs.writeFileSync(envPath, envContent, "utf8");
        // 2. Save provider to config.yaml
        const homedir = require("os").homedir();
        const configPath = path.join(homedir, ".rakshastra", "config.yaml");
        const configDir = path.dirname(configPath);
        if (!fs.existsSync(configDir)) {
            fs.mkdirSync(configDir, { recursive: true });
        }
        let configYaml = "";
        if (fs.existsSync(configPath)) {
            configYaml = fs.readFileSync(configPath, "utf8");
        }
        // Simple YAML parser/updater for model provider & platforms
        if (!configYaml.includes("model:")) {
            configYaml += `\nmodel:\n  provider: ${data.provider}\n`;
        }
        else {
            const modelRegex = /(model:\s*(?:\r?\n\s+.*)*?provider:\s*)(\S+)/;
            if (modelRegex.test(configYaml)) {
                configYaml = configYaml.replace(modelRegex, `$1${data.provider}`);
            }
            else {
                configYaml = configYaml.replace(/model:/, `model:\n  provider: ${data.provider}`);
            }
        }
        // Save providers custom base_url to config.yaml if provider is custom
        if (data.provider === "custom" && data.baseUrl) {
            if (!configYaml.includes("providers:")) {
                configYaml += `\nproviders:\n  custom:\n    base_url: ${data.baseUrl}\n    api_key: ${data.apiKey || "none"}\n`;
            }
            else if (!configYaml.includes("  custom:")) {
                configYaml = configYaml.replace(/providers:/, `providers:\n  custom:\n    base_url: ${data.baseUrl}\n    api_key: ${data.apiKey || "none"}`);
            }
            else {
                const baseRegex = /(custom:\s*(?:\r?\n\s+.*)*?base_url:\s*)(\S+)/;
                if (baseRegex.test(configYaml)) {
                    configYaml = configYaml.replace(baseRegex, `$1${data.baseUrl}`);
                }
                else {
                    configYaml = configYaml.replace(/  custom:/, `  custom:\n    base_url: ${data.baseUrl}`);
                }
            }
        }
        // Update platforms config
        if (!configYaml.includes("platforms:")) {
            configYaml += `\nplatforms:\n`;
        }
        for (const [platform, enabled] of Object.entries(data.platforms)) {
            const platRegex = new RegExp(`(${platform}:\\s*(?:\\r?\\n\\s+.*)*?enabled:\\s*)(\\S+)`);
            const blockRegex = new RegExp(`\\s+${platform}:`);
            if (platRegex.test(configYaml)) {
                configYaml = configYaml.replace(platRegex, `$1${enabled}`);
            }
            else if (blockRegex.test(configYaml)) {
                configYaml = configYaml.replace(blockRegex, `  ${platform}:\n    enabled: ${enabled}`);
            }
            else {
                configYaml = configYaml.replace(/platforms:/, `platforms:\n  ${platform}:\n    enabled: ${enabled}`);
            }
        }
        fs.writeFileSync(configPath, configYaml, "utf8");
        log("[main] Saved config.yaml successfully");
        return { ok: true };
    });
}
// ── App lifecycle ────────────────────────────────────────────────────────
electron_1.app.whenReady().then(async () => {
    log("[main] Rakshastra Desktop starting...");
    log(`[main] Project root: ${ROOT_DIR}`);
    log(`[main] Is dev: ${IS_DEV}`);
    setupIPC();
    createWindow();
    createTray();
    // Start the backend
    await launchGateway();
});
electron_1.app.on("window-all-closed", () => {
    // On macOS, apps typically stay in the dock
    if (process.platform !== "darwin") {
        isQuitting = true;
        electron_1.app.quit();
    }
});
electron_1.app.on("activate", () => {
    // macOS: re-create window when dock icon is clicked
    if (mainWindow === null) {
        const win = createWindow();
        if (gatewayInfo) {
            win.loadURL(gatewayInfo.url);
        }
    }
    else {
        mainWindow.show();
    }
});
electron_1.app.on("before-quit", async () => {
    isQuitting = true;
    log("[main] Shutting down...");
    await (0, gateway_1.stopGateway)();
});
// Handle certificate errors for localhost
electron_1.app.on("certificate-error", (event, _webContents, _url, _error, _certificate, callback) => {
    // Allow self-signed certs for localhost
    event.preventDefault();
    callback(true);
});
//# sourceMappingURL=main.js.map