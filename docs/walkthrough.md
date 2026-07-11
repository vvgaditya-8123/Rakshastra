# Walkthrough - WhatsApp Bot Mode, Setup Prompts & Session Alignment

We have successfully transitioned the WhatsApp gateway integration to **bot** mode, aligned the setup wizard's session storage path with the adapter's path, and fixed process termination issues on Windows.

## Changes Made

### 1. Switched WhatsApp Mode to Bot Mode
- Updated the WhatsApp configuration file [C:\Users\intel\AppData\Local\rakshastra\.env](file:///C:/Users/intel/AppData/Local/rakshastra/.env) to run in `WHATSAPP_MODE=bot`.
- This ensures that messages sent by other allowed contacts (like friend `919755745209`) are processed and replied to, rather than being ignored under self-chat constraints.

### 2. Aligned Session Directory Paths
- Fixed a mismatch where the setup wizard [../rakshastra_cli/main.py](../rakshastra_cli/main.py) hardcoded the session path to `whatsapp/session`, while the platform adapter resolved it to `platforms/whatsapp/session` dynamically.
- Aligned `main.py` to use `get_rakshastra_dir("platforms/whatsapp/session", "whatsapp/session")` so that credentials saved by the wizard are automatically found by the adapter.
- Copied existing credentials to ensure that both paths contain active session details.

### 3. Enabled Wizard Mode Prompt Reconfiguration
- Modified the setup wizard [../rakshastra_cli/main.py](../rakshastra_cli/main.py) to always prompt the user to choose their mode (Separate bot number vs Personal number) even if it was previously configured.
- Shows the current setting as default if they press Enter, making reconfiguration easy.

### 4. Resolved Windows Taskkill Process Termination Timeout
- Modified `_terminate_bridge_process()` in [../plugins/platforms/whatsapp/adapter.py](../plugins/platforms/whatsapp/adapter.py) to always use the `/F` (force) flag when calling `taskkill` on Windows.
- This ensures that when the gateway stops, restarts, or reconnects the WhatsApp bridge, stale headless processes are immediately cleaned up and port 3000 is freed.

---

## Verification Results

### 1. Test Suite Verification
- Ran the tool registration and cyber intelligence tests:
  ```powershell
  .venv\Scripts\pytest tests/tools/test_cyber_intelligence_tools.py
  ```
  **Result:** `7 passed in 0.62s`.

### 2. Connection Verification
- Started the gateway in the background:
  ```powershell
  .venv\Scripts\rakshastra gateway start
  ```
  **Result:** Gateway spawned cleanly and immediately connected to WhatsApp:
  `✅ WhatsApp connected!`
  `[Whatsapp] Bridge ready (status: connected)`
