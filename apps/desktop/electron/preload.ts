/**
 * Preload script — secure bridge between the Electron renderer and Node.js.
 *
 * Exposes a limited API to the web dashboard via contextBridge so it can
 * interact with the desktop shell (window controls, app info, etc.)
 * without direct access to Node.js APIs.
 */

import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("rakshastraDesktop", {
  /** Platform identifier */
  platform: process.platform,

  /** App version from package.json */
  version: ipcRenderer.sendSync("get-app-version"),

  /** Whether running inside the desktop shell (always true here) */
  isDesktop: true,

  /** Window controls */
  minimize: () => ipcRenderer.send("window-minimize"),
  maximize: () => ipcRenderer.send("window-maximize"),
  close: () => ipcRenderer.send("window-close"),
  toggleFullscreen: () => ipcRenderer.send("window-toggle-fullscreen"),

  /** Open a URL in the system browser */
  openExternal: (url: string) => ipcRenderer.send("open-external", url),

  /** Gateway status */
  getGatewayInfo: () => ipcRenderer.invoke("get-gateway-info"),

  /** Restart the backend */
  restartGateway: () => ipcRenderer.invoke("restart-gateway"),

  /** Open devtools */
  openDevTools: () => ipcRenderer.send("open-devtools"),

  /** Setup installer trigger */
  startInstall: () => ipcRenderer.send("setup-start-install"),

  /** Setup finished launcher trigger */
  launchApp: () => ipcRenderer.send("setup-launch-app"),

  /** Setup save configuration */
  saveConfig: (config: any) => ipcRenderer.invoke("setup-save-config", config),
});

// Forward setup events from Main Process to the HTML Setup Page
ipcRenderer.on("setup-log", (_event, data) => {
  window.dispatchEvent(new CustomEvent("setup-log", { detail: data }));
});

ipcRenderer.on("setup-progress", (_event, data) => {
  window.dispatchEvent(new CustomEvent("setup-progress", { detail: data }));
});

ipcRenderer.on("setup-complete", (_event, data) => {
  window.dispatchEvent(new CustomEvent("setup-complete", { detail: data }));
});

// Inject desktop detection flag before the page loads
window.addEventListener("DOMContentLoaded", () => {
  // The web dashboard checks this to enable desktop-specific features
  (window as any).__RAKSHASTRA_IS_DESKTOP__ = true;
});
