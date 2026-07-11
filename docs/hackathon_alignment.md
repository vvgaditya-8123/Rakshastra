# Build with Gemini Hackathon Alignment

This document outlines how Rakshastra leverages Google Gemini to solve complex cyber defense and investigation challenges.

## 1. Why Gemini is the Core Backend

Rakshastra relies on Google Gemini's advanced capabilities:
- **Massive Context Windows**: Allows investigators to feed long chat logs, multiple email chains, and OCR screenshots directly into a single session without context loss or truncation.
- **Multimodal Native Processing**: Directly processes screenshots, PDFs, and manual investigator notes, extracting entities (usernames, phone numbers, wallets) from mixed-media sources.
- **High-Fidelity Tool Calling**: Drives the Autonomous Investigation Orchestrator, enabling the AI agent to dynamically select tools (e.g. searching previous databases, querying the graph) and build a dynamic task plan.

## 2. Gemini-First Onboarding

- **Streamlined Setup**: The configuration flow default-selects Google Gemini, prompting for the Gemini API Key as the primary onboarding path.
- **Credential Pruning**: Excludes complex credentials by defaulting auxiliary tasks (vision, summarization) to route directly through the active Gemini API Key, reducing onboarding friction.

## 3. Measurable Impact for XPRIZE Judges

- **Heuristic-Backed Reliability**: An offline template fallback ensures the platform remains operational in secure, isolated environments, while automatically delegating to active Gemini models when online.
- **Explainable System Decisions**: Instead of simple classification outputs, Gemini is instructed to construct logical step-by-step reasoning chains, aiding humans in auditing automated security workflows.
