# Rakshastra Repository Map

This document outlines the folder structure of the Rakshastra codebase, indicating the authoritative directories, packages, and the locations of static assets.

## Directory Layout

* **`web/`**
  - *Status*: **Authoritative Frontend**
  - *Description*: The React + TypeScript web dashboard driven by Vite. Serves the primary user interface.

* **`rakshastra_core/`**
  - *Status*: **Authoritative Core**
  - *Description*: The foundational security analytics and intelligence codebase:
    - `/intelligence/content_classifier.py`: Drug Intelligence classifiers.
    - `/intelligence/threat_intelligence.py`: Modular Threat Intelligence Engine with 9 packs.
    - `/intelligence/entity_resolution.py`: Footprint and alias extraction and merging.
    - `/intelligence/graph_engine.py`: Spring-embedder visualization layouts.
    - `/intelligence/timeline_engine.py`: Step replay and chronological investigation reconstruction.
    - `/intelligence/explainable_reasoning.py`: AI explanation generator and markdown report builder.
    - `/intelligence/autonomous_orchestrator.py`: Dynamic task planners and autonomous investigation loops.

* **`rakshastra_cli/`**
  - *Status*: **Authoritative CLI & Server**
  - *Description*: The main FastAPI backend (`web_server.py`) and command-line execution interfaces.

* **`gateway/`**
  - *Status*: **Authoritative Gateway**
  - *Description*: Platform messaging listeners and dispatchers.

* **`agent/`**
  - *Status*: **Authoritative Agent**
  - *Description*: Core agent prompt formatting and execution loop.

* **`tools/`**
  - *Status*: **Authoritative Tools**
  - *Description*: AI tool declarations and handlers.

* **`plugins/`**
  - *Status*: **Authoritative Plugins**
  - *Description*: Headless adapters for Telegram, Discord, and WhatsApp.

* **`assets/`**
  - *Status*: **Authoritative Assets**
  - *Description*: Screenshots, logos, and product graphics.

* **`tests/`**
  - *Status*: **Authoritative Tests**
  - *Description*: Unit and integration test suites.

* **`docs/`**
  - *Status*: **Authoritative Documentation**
  - *Description*: XPRIZE strategy documents, x402 payment specifications, and setup sheets.

* **`Landing Page/`**
  - *Status*: **Cleaned Legacy Copy**
  - *Description*: Stale copy of the main repository. Duplicated python backends, duplicate tests, and duplicate core packages have been pruned, leaving only the Next.js landing page assets.
