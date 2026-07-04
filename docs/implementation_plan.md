# Implementation Plan - WhatsApp Bot Mode & Windows Termination Fix

This plan covers transitioning the WhatsApp bridge to **bot** mode (allowing friends to message the bot and enabling group chats) and fixing the Windows process termination issue that causes gateway connection timeouts.

## Proposed Changes

### Configuration

#### [MODIFY] [.env](file:///C:/Users/intel/AppData/Local/rakshastra/.env)
* Update `WHATSAPP_MODE=self-chat` to `WHATSAPP_MODE=bot`.
* This will allow the Baileys bridge and WhatsApp adapter to forward messages sent by contacts other than yourself (like your friend `919755745209`) to the Rakshastra gateway.

---

### WhatsApp Platform Adapter

#### [MODIFY] [adapter.py](file:///c:/PROJECT/plugins/platforms/whatsapp/adapter.py)
* Update `_terminate_bridge_process()` to always include the `/F` (force) flag when calling `taskkill` on Windows.
* This ensures that when the gateway stops, restarts, or reconnects the WhatsApp bridge, the headless Node.js process is immediately and reliably terminated rather than failing and leaving stale processes holding port 3000.

---

## Verification Plan

### Automated Tests
* We can run python to verify config loading.
* Run: `poetry run pytest tests/tools/test_cyber_intelligence_tools.py` to ensure core test suites are unaffected.

### Manual Verification
1. Start the gateway: `poetry run rakshastra gateway`.
2. Confirm the WhatsApp bridge starts and connects without timing out.
3. Message the bot from your friend's number (`919755745209`) and verify it processes the message and responds successfully.
