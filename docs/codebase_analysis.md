# Rakshastra Codebase Analysis Report

This report provides a comprehensive breakdown of the cloned codebase, explaining the layout, architecture, file responsibilities, and how they will be repurposed for **Rakshastra - The Autonomous Security Engineer for SMEs**.

---

## 1. System Architecture Overview

Rakshastra is structured as a robust agentic runtime designed to run complex loops, execute system commands in sandboxed environments, interact with external messaging platforms, and build procedural memory (skills). 

The value path maps as follows:
```
[User Input/CLI/Gateway] 
       │
       ▼
  [cli.py / gateway] ──(Session DB / Logs)
       │
       ▼
 [run_agent.py (AIAgent)] ──(Context & System Prompts)
       │
       ▼
[agent/conversation_loop.py] ◄──► [agent/memory_manager.py]
       │
       ▼
[model_tools.py] ──(Tool Registry & Discoverer)
       │
       ▼
[tools/tool_executor.py] ──(Guardrails & Tirith Security)
       │
       ▼
[tools/terminal_tool.py] ──(Environments: Local, Docker, SSH)
```

---

## 2. Core System Entry Points

These top-level files bootstrap the environment, parse user commands, initialize the agent loop, and manage available tools.

| File | Primary Purpose | Security Context / Future Use |
| :--- | :--- | :--- |
| [`cli.py`](../cli.py) | Bootstraps the terminal UI, manages configs, commands, spinner states, and parses subcommands. | Will be customized to feature security diagnostics commands (e.g., `rakshastra scan`). |
| [`run_agent.py`](../run_agent.py) | Contains the main `AIAgent` class that manages system state, budget, models, and sets up session contexts. | Orchestrates credential scopes for secure environments. |
| [`model_tools.py`](../model_tools.py) | Manages tool schemas, registers tool functions, and handles JSON-to-Python model function calls. | Used to register specialized cybersecurity tools (e.g. nmap, vulnerability auditors). |
| [`toolsets.py`](../toolsets.py) | Defines groupings of tools (e.g., standard, full, restricted). | Grouping security-critical tools versus passive observation tools. |

---

## 3. Core Agent Logic (`agent/`)

The [`agent/`](../agent) directory manages the cognitive processes, prompt assembly, API requests, rate-limiting, and learning mechanisms of the agent.

### A. Conversation Loop & State
- [`conversation_loop.py`](../agent/conversation_loop.py): The main loop executing API calls, checking token/iteration budgets, executing tools, and verifying outputs.
- [`turn_context.py`](../agent/turn_context.py): Stores state data specific to a single interaction turn (errors, tool results, tokens).
- [`agent_init.py`](../agent/agent_init.py): Loads profiles, sets default environment values, and configures the system context.

### B. Memory, Prompts & Context
- [`memory_manager.py`](../agent/memory_manager.py): Implements memory persistence. For Rakshastra, this will be repurposed into **Security Memory** to store historical configurations, past vulnerabilities, and network maps.
- [`context_compressor.py`](../agent/context_compressor.py): Summarizes long conversations into condensed contexts to optimize model context windows.
- [`prompt_builder.py`](../agent/prompt_builder.py): Assembles system prompts, injection metadata, and context files.

### C. Tool Orchestration & Guardrails
- [`tool_executor.py`](../agent/tool_executor.py): Handles execution details, captures stdout/stderr, and prevents execution leakage.
- [`tool_guardrails.py`](../agent/tool_guardrails.py): Restricts dangerous shell commands. This is critical for Rakshastra to prevent the agent from running destructive actions.

### D. Model Integration Adapters
Adapts provider-specific schemas (e.g. Anthropic, Bedrock, Gemini, OpenRouter) to a standardized internal message format.
- [`gemini_native_adapter.py`](../agent/gemini_native_adapter.py)
- [`anthropic_adapter.py`](../agent/anthropic_adapter.py)

---

## 4. Tools Ecosystem (`tools/`)

The [`tools/`](../tools) directory provides interfaces for the agent to act on its environment.

### A. Environment Backends (`tools/environments/`)
Contains backends that allow commands to run in isolated environments:
- **Local**: Runs natively on the host shell.
- **Docker**: Launches containers for sandboxed execution (essential for executing untrusted scripts or network tests).
- **SSH**: Executes commands on remote servers (e.g., scanning remote target machines).

### B. Specialized Tool Implementations
- [`terminal_tool.py`](../tools/terminal_tool.py): Opens PTY channels, manages active terminals, and handles interactive shell sessions.
- [`file_tools.py`](../tools/file_tools.py): Creates, reads, searches, and modifies files.
- [`mcp_tool.py`](../tools/mcp_tool.py): Connects to external Model Context Protocol (MCP) servers (e.g. database connectors, security scanner endpoints).
- [`delegate_tool.py`](../tools/delegate_tool.py): Spawns subagents to parallelize work.

### C. Safety & Guardrails
- [`tirith_security.py`](../tools/tirith_security.py): A security layer that evaluates commands and files against safety policies before execution.
- [`threat_patterns.py`](../tools/threat_patterns.py): Checks commands for dangerous patterns (e.g., deleting root directory, writing suspicious scripts).

---

## 5. Skills Framework (`skills/`)

Skills act as **Procedural Memory**—pre-written system instruction packets (with schemas and markdown guidelines) that teach the agent how to run multi-step tasks.

For Rakshastra, we will create new skills under the [`skills/`](../skills) directory:
- `network-reconnaissance`: Playbooks for port scanning, banner grabbing, and network map creation.
- `vulnerability-audit`: Diagnostic steps for scanning packages, checking firewall settings, and finding misconfigurations.
- `compliance-verification`: Instructions to audit local configuration against standard baselines (SOC2, HIPAA, ISO27001).

---

## 6. Target Customization Strategy

To transform this foundation into Rakshastra:

```
                  ┌──────────────────────┐
                  │   Upstream Hermes    │
                  └──────────┬───────────┘
                             │ (Customization Boundary)
                             ▼
  ┌─────────────────────────────────────────────────────┐
  │                 RAKSHASTRA OS LAYER                 │
  ├─────────────────────────────────────────────────────┤
  │ 1. Sandboxed Diagnostics (Docker/SSH Terminal Use)  │
  │ 2. Security Graph Memory (Asset Dependency Mapping) │
  │ 3. Automated Audits (SOC2 / Compliance Skills)      │
  │ 4. Threat Guardrails (Tirith Safety Overrides)      │
  └─────────────────────────────────────────────────────┘
```

1. **Safety First**: Retain and strengthen `tirith_security.py` and `threat_patterns.py` to ensure the agent does not execute malicious commands.
2. **Isolated Toolset**: Make Docker the default execution environment for tools, isolating diagnostic activities.
3. **Security Knowledge Memory**: Modify `memory_manager.py` to persist system state mappings and inventory dependency graphs.
