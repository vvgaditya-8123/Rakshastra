# Rakshastra ☤

> **The Autonomous Security Engineer for SMEs**  
> *The AI Security Operating System for Modern Businesses*

---

## Problem

Small and Medium Enterprises (SMEs) face critical cybersecurity challenges:
- **No Dedicated SOCs**: Most SMEs cannot afford 24/7 Security Operations Centers.
- **Prohibitive Costs**: Enterprise-grade security suites are expensive and complex to configure.
- **Skilled Talent Shortage**: Cybersecurity talent is scarce, leaving SMEs vulnerable to targeted attacks, ransomware, and compliance violations.

---

## Vision

Rakshastra acts as an **Autonomous Security Operating System for Modern Businesses**—providing continuous threat identification, automated compliance audits, and intelligent configuration hardening without requiring a dedicated security team.

---

## Architecture

Rakshastra is built on a structured execution stack, transforming raw model inference into a robust security daemon:

```mermaid
graph TD
    A[Rakshastra Bootloader] --> B[Rakshastra Core]
    B --> C[Knowledge Graph]
    B --> D[Security Memory]
    B --> E[Planner]
    E --> F[Tool Executor]
    F --> G[Skills]
    G --> H[Security Operating System]
```

- **Rakshastra Bootloader**: Initializes environment context, active profiles, and core dependencies.
- **Rakshastra Core**: Orchestrates conversation, manages agent iterations, and drives the reasoning loop.
- **Knowledge Graph**: Maps enterprise digital assets, dependencies, and network topology.
- **Security Memory**: Persists security history, incident trails, and past system states using FTS5 search.
- **Planner**: Generates step-by-step diagnostic actions, schedules scans, and designs mitigation strategies.
- **Tool Executor**: Safely runs system commands, executes diagnostic scripts, and navigates environments.
- **Skills**: Encapsulates playbooks, compliance guidelines, and security verification procedures.
- **Security Operating System**: The unified, self-healing outcome providing continuous protection.

---

## Features

- **Continuous Vulnerability Assessment**: Periodically scans systems, code repos, and ports.
- **Isolated Execution Sandboxing**: Executes diagnostic tools within sandboxed Docker/SSH containers to prevent damage.
- **Closed Learning Loop**: Autonomously extracts new security playbooks and refines existing skills after resolving incidents.
- **Multi-Platform Security Gateway**: Sends real-time threat alerts and receives commands via Telegram, Discord, Slack, and WhatsApp.
- **Cron Scheduling**: Automates daily posture checks, weekly compliance reports, and regular backup validation.

---

## Roadmap

- [ ] **Security Knowledge Graph**: Integrate CVE mappings and live dependency graphs.
- [ ] **Expanded Toolset**: Package masscan, nmap, and OWASP ZAP wrapper integrations.
- [ ] **Autonomous Mitigation**: Implement automated hot-patching and security group configuration.
- [ ] **Compliance Engine**: Built-in support for automated SOC2, HIPAA, and ISO27001 audits.

---

## Folder Structure

- [`agent/`](file:///c:/PROJECT/agent): Core agent logic, memory consolidation, and reasoning.
- [`tools/`](file:///c:/PROJECT/tools): Tool wrappers for terminal backends (Docker, local, SSH), browser automation, and web searching.
- [`skills/`](file:///c:/PROJECT/skills): Predefined security skills, checklists, and compliance templates.
- [`optional-skills/`](file:///c:/PROJECT/optional-skills): Specialized but inactive skills for custom security scenarios.
- [`gateway/`](file:///c:/PROJECT/gateway): Platform integrations (Slack, Telegram, Discord, Signal) for notification and remote control.
- [`cli.py`](file:///c:/PROJECT/cli.py): Interactive command-line client.
- [`Dockerfile`](file:///c:/PROJECT/Dockerfile), [`docker-compose.yml`](file:///c:/PROJECT/docker-compose.yml): Deployment configurations.

---

## Developer Guide

### Setup

Install the dependencies and set up the development environment:

```bash
uv pip install -e ".[all,dev]"
```

Run tests to verify the setup:

```bash
scripts/run_tests.sh
```

### Contributing

See [AGENTS.md](file:///c:/PROJECT/AGENTS.md) for contribution guidelines, core invariants, and design principles.
