# Rakshastra Platform Architecture

## 1. Multi-Layered Overview

Rakshastra's architecture is divided into three primary layers:
1. **Presentation & Interface Layer**:
   - **React/Vite Web Dashboard**: Displays real-time threat tables, layout graph node expansions, and case logs.
   - **Windows Desktop Companion**: Runs on-premise, collects screenshot OCRs, scans registries, and syncs via API.
2. **REST API & Gateways Layer**:
   - **FastAPI Backend Server**: Exposes endpoints for threat analysis, entity resolution, and report generation.
   - **Messaging Gateways**: Connectors to Telegram, WhatsApp, and Discord.
3. **Core Intelligence Engines Layer**:
   - **Threat Intelligence Engine**: Detects categorized threats from slang and keyword packs.
   - **Entity Resolution Engine**: Resolves alias profiles.
   - **Graph Engine**: Calculates coordinate layouts.
   - **Explainable Reasoning Engine**: Generates natural language summaries.
   - **Autonomous Orchestrator**: Executes task planning loops.

## 2. Dynamic Workflow Execution

```
Raw Alert Ingested → Entity Resolution → Correlation Match → Graph Expansion → ExplainableAI Report
                                                                                      ↓
                                                                             Task Queue Refinement
```
- A raw event is normalized.
- Key identifiers (phones, wallets, usernames) are extracted.
- Multi-Source Correlation identifies matches in historical cases.
- Graph Engine updates node networks.
- Explainable AI creates investigator-friendly narratives.
- Task Queue triggers next investigative actions autonomously.
