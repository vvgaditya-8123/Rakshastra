# Rakshastra: Product Strategy Document

## 1. Executive Summary

Rakshastra is an autonomous, AI-native cyber investigation platform designed specifically for Small and Medium Enterprises (SMEs) and digital forensics teams. By combining a Gemini-first reasoning engine with multi-source footprint correlation, interactive relationship graph mapping, and structured explainable narratives, Rakshastra automates the complex operations of a modern Security Operations Center (SOC) at a fraction of the cost.

## 2. Who Uses Rakshastra?
- **Corporate Threat Investigators**: Track phishing, crypto fraud, and credential theft attempts.
- **Digital Forensics Teams**: Map digital footprints, resolve alias reuse, and compile timeline evidence reports.
- **SMEs without Dedicated SOCs**: Obtain automated alerts, explainable risk explanations, and direct remediation advice.

## 3. What Pain it Solves
Enterprise threat investigation platforms are prohibitively expensive and require highly skilled security analysts. Rakshastra resolves:
- **Alert Fatigue**: Raw logs are automatically parsed, deduplicated, and resolved into unified operator profiles.
- **Forensic Ambiguity**: Explains exactly why a threat score was assigned, detailing matched keyword packs, correlation reuse, and counter-evidence.
- **Operational Overhead**: Replaces manual search queries with an autonomous task execution planner.

## 4. Monetization & Business Model
Rakshastra operates on a dual-monetization strategy:
1. **SaaS Web Subscription**: Unlimited access to the browser-based dashboard, graphical investigator portal, and notification gateway integrations.
2. **Pay-Per-Request API Gateway (x402 / Algorand)**: Third-party developers, threat feeds, and external SOCs query Rakshastra's high-fidelity intelligence endpoints (e.g. `/api/v1/threat/analyze-text`, `/api/v1/entity/correlate`) using micro-payments backed by Algorand smart contracts.

## 5. AI-Native Operating Model

### What the AI Does
- **Case Goal Planner**: Automatically establishes investigation goals (e.g. identify if actor is a drug seller, money mule, or bot operator).
- **Dynamic Task Planning**: Generates and executes investigation tasks (username lookup, graph expansion) prioritizing by usefulness.
- **Explainable Reasoning**: Synthesizes structured data into executive threat summaries and chronological narratives.

### What the Human Does
- **Onboarding and Configuration**: Feeds API credentials (Google Gemini API keys).
- **Strategic Manual Actions**: Issues data preservation orders, requests subpoenas based on AI recommendations.
- **Human-in-the-Loop Approval**: Reviews and approves/declines autonomous tasks in "Require Approval" mode.

## 6. How the System Fits the XPRIZE Business Criteria
The Build with Gemini XPRIZE targets scalable, real-world AI impact:
- **Massive Cost Reductions**: Shrinks SOC operations overhead by up to 90% via autonomous task planning.
- **Real Proof of Value**: Generates detailed, auditable decision logs and explainable reports showing clear trace records.

## 7. System Architecture and Integration
- **Web Dashboard**: Dark, professional, interactive GUI displaying investigation status, threat trees, and graph networks.
- **Backend APIs**: Python FastAPI server executing the orchestrator, memory stores, and intelligence engines.
- **Windows Companion App**: Local desktop scanner deployed on-premise to feed screenshot OCRs and manual logs back to the server.
