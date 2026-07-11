# Windows Companion App Strategy

## 1. What the Windows Companion App Does

The Rakshastra Windows Companion App is a native desktop client that allows operators to run on-premise security scanning, system monitoring, and evidence collections:
- **Desktop Threat Scans**: Scans system registries, local file folders, and network configurations.
- **Local Screenshot OCR**: Captures desktop activity or investigator screenshot files to run local/cloud OCR.
- **Credential Vault**: Securely manages local API keys (e.g. Gemini, custom endpoints) using Windows Credential Manager.

## 2. Why it Exists Separately from the Web Dashboard

- **System-Level Permissions**: A browser-based web dashboard cannot access the user's local filesystem or run diagnostic terminal commands (like registry scans) due to sandbox limits.
- **Local OCR Performance**: Heavy OCR workloads are executed locally on the user's machine before sending only resolved text parameters to the cloud, saving network bandwidth.
- **Offline Mode**: Operates in fully air-gapped on-premise environments, caching threat indicators until it can sync back to the cloud/server.

## 3. Installation via `winget`

To make setup simple for enterprises and developers, the desktop app is packaged and distributed using the official Windows Package Manager (`winget`):

```cmd
winget install Rakshastra.Companion
```

This automates the installation, registry registrations, and updates.

## 4. Connection & Synchronization

- The desktop companion connects to the Rakshastra API gateway (FastAPI server) via local or remote HTTP REST endpoints.
- Authenticaton is handled via secure API keys or Algorand-backed x402 wallets.
- **Simple Onboarding**: On first launch, the user inputs their server URL or scans a pairing QR code displayed in the web dashboard, linking the desktop scanner to their centralized threat graph instantly.
