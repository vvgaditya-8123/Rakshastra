"use strict";
/**
 * Preload script — secure bridge between the Electron renderer and Node.js.
 *
 * Exposes a limited API to the web dashboard via contextBridge so it can
 * interact with the desktop shell (window controls, app info, etc.)
 * without direct access to Node.js APIs.
 */
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
electron_1.contextBridge.exposeInMainWorld("rakshastraDesktop", {
    /** Platform identifier */
    platform: process.platform,
    /** App version from package.json */
    version: electron_1.ipcRenderer.sendSync("get-app-version"),
    /** Whether running inside the desktop shell (always true here) */
    isDesktop: true,
    /** Window controls */
    minimize: () => electron_1.ipcRenderer.send("window-minimize"),
    maximize: () => electron_1.ipcRenderer.send("window-maximize"),
    close: () => electron_1.ipcRenderer.send("window-close"),
    toggleFullscreen: () => electron_1.ipcRenderer.send("window-toggle-fullscreen"),
    /** Open a URL in the system browser */
    openExternal: (url) => electron_1.ipcRenderer.send("open-external", url),
    /** Gateway status */
    getGatewayInfo: () => electron_1.ipcRenderer.invoke("get-gateway-info"),
    /** Restart the backend */
    restartGateway: () => electron_1.ipcRenderer.invoke("restart-gateway"),
    /** Open devtools */
    openDevTools: () => electron_1.ipcRenderer.send("open-devtools"),
    /** Setup installer trigger */
    startInstall: () => electron_1.ipcRenderer.send("setup-start-install"),
    /** Setup finished launcher trigger */
    launchApp: () => electron_1.ipcRenderer.send("setup-launch-app"),
    /** Setup save configuration */
    saveConfig: (config) => electron_1.ipcRenderer.invoke("setup-save-config", config),
});
// Forward setup events from Main Process to the HTML Setup Page
electron_1.ipcRenderer.on("setup-log", (_event, data) => {
    window.dispatchEvent(new CustomEvent("setup-log", { detail: data }));
});
electron_1.ipcRenderer.on("setup-progress", (_event, data) => {
    window.dispatchEvent(new CustomEvent("setup-progress", { detail: data }));
});
electron_1.ipcRenderer.on("setup-complete", (_event, data) => {
    window.dispatchEvent(new CustomEvent("setup-complete", { detail: data }));
});
// Inject desktop detection flag before the page loads
window.addEventListener("DOMContentLoaded", () => {
    // The web dashboard checks this to enable desktop-specific features
    window.__RAKSHASTRA_IS_DESKTOP__ = true;
});
//# sourceMappingURL=preload.js.map