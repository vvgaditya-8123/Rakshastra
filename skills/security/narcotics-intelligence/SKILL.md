---
name: narcotics-intelligence
description: >
  Autonomous narcotics cyber intelligence skill for Indian law enforcement.
  Orchestrates the full Rakshastra ecosystem (multi-model reasoning, browser,
  terminal, OSINT, memory, graph analysis) to detect, investigate, attribute,
  and report dark-web and social-media narcotics supply chains — all from a
  single high-level instruction.
version: 1.0.0
author: Rakshastra Core Team
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  rakshastra:
    tags:
      - narcotics
      - cybercrime
      - OSINT
      - law-enforcement
      - intelligence
      - investigation
      - NDPS
      - darkweb
      - social-media
      - graph-analysis
    related_skills:
      - security/forensics
      - security/incident-response
      - social-media
      - research
---

# Rakshastra: Narcotics Cyber Intelligence Orchestrator

> **Problem Statement 1** — AI-Powered Narcotics Detection and Cyber Intelligence
> for Indian Law Enforcement (LEA)

## 1. PURPOSE

This skill turns Rakshastra into an **autonomous narcotics cyber investigator**.
The investigator issues one high-level instruction — "Investigate this Telegram
channel" — and Rakshastra orchestrates the entire pipeline: evidence
acquisition, NLP slang decoding, entity extraction, graph construction,
cross-platform correlation, risk scoring, and a court-ready intelligence
report.

### What This Skill Is NOT

- A simple Q&A responder. It does **not** answer questions about drugs.
- A single-model pipeline. It treats every available model as a **specialist**.
- A manual, step-by-step workflow. The investigator provides intent; the skill
  decides sequencing, model assignment, and data flow automatically.

---

## 2. ARCHITECTURE — HERMES / OPENCLAW ORCHESTRATION

```
┌─────────────────────────────────────────────────────────────┐
│                    INVESTIGATOR (Human)                      │
│         "Investigate Telegram channel @DarkLabPunjab"        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              RAKSHASTRA ORCHESTRATOR (this skill)            │
│                                                             │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Research  │  │ Language │  │  Vision  │  │ Reasoning │  │
│  │  Agent    │  │  Agent   │  │  Agent   │  │  Agent    │  │
│  └─────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│        │             │             │               │        │
│  ┌─────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  ┌─────┴─────┐  │
│  │  Risk     │  │  Report  │  │  Memory  │  │  OSINT    │  │
│  │  Agent    │  │  Agent   │  │  Agent   │  │  Agent    │  │
│  └───────────┘  └──────────┘  └──────────┘  └───────────┘  │
│                                                             │
│  Tools: terminal, browser, code execution, file I/O,        │
│         web search, memory read/write, MCP servers          │
└─────────────────────────────────────────────────────────────┘
```

### Specialist Assignment Rules

The orchestrator does NOT hardcode model names. It queries the active model
configuration and routes tasks based on capability:

| Specialist       | Capability Required         | Typical Assignment                   |
|------------------|-----------------------------|--------------------------------------|
| Research Agent   | Web search, browsing        | Primary model + `web_search` tool    |
| Language Agent   | Multilingual NLP, slang     | Primary model (long context)         |
| Vision Agent     | Image/video analysis        | Auxiliary vision model               |
| Reasoning Agent  | Multi-step logical deduction| Primary model (extended thinking)    |
| Risk Agent       | Structured scoring          | Primary model (JSON mode)            |
| Report Agent     | Document generation         | Primary model (long output)          |
| Memory Agent     | Session recall, entity store| Primary model + `memory_*` tools     |
| OSINT Agent      | Browser automation          | Primary model + `browser_*` tools    |

When subagents are available, the orchestrator delegates to parallel subagents.
When running single-model, it executes phases sequentially using the same
model with different system prompt contexts.

---

## 3. ACTIVATION

This skill activates when the investigator's instruction matches ANY of:

- Contains keywords: `investigate`, `narcotics`, `drug`, `NDPS`, `darknet`,
  `dark web`, `trafficking`, `slang`, `dealer`, `contraband`, `substance`,
  `meth`, `heroin`, `cocaine`, `cannabis`, `fentanyl`, `MDMA`, `psychotropic`
- References a social media channel, handle, or URL in context of surveillance
- Mentions Indian law enforcement entities: NCB, DRI, ATS, STF, NIA, CBI,
  Customs, BSF, NDPS Act, Narcotic Drugs
- Asks to "monitor", "track", "flag", "analyze" any messaging platform for
  illicit activity
- References Problem Statement 1 or "cyber narcotics intelligence"

---

## 4. INVESTIGATION PIPELINE — 8 STAGES

Every investigation follows this pipeline. Stages are executed in order, but
the orchestrator may loop back (e.g., Stage 3 entity extraction may trigger
additional Stage 1 acquisition for newly discovered accounts).

### Stage 1: Evidence Acquisition

**Objective**: Collect raw intelligence from the target.

**Actions**:
1. Identify the target type (Telegram channel, Instagram profile, dark web
   URL, phone number, crypto wallet, etc.)
2. Use `browser_navigate` / `web_search` to gather publicly available data
3. For messaging platforms:
   - Scrape channel message history (public channels only)
   - Extract member lists, admin names, pinned messages
   - Capture media metadata (file sizes, timestamps, captions)
4. For dark web targets:
   - Document .onion URLs, market listings, vendor profiles
   - Extract PGP keys, shipping regions, pricing
5. For crypto wallets:
   - Query blockchain explorers for transaction history
   - Document wallet addresses, amounts, timestamps
6. Store ALL raw evidence using `write_file` with SHA-256 hashes
7. Log provenance: source URL, collection timestamp, tool used

**Output**: Raw evidence files in `~/.rakshastra/investigations/<case-id>/evidence/`

**Safety**: Only access publicly available information. No unauthorized access.
No social engineering. No interaction with subjects.

---

### Stage 2: NLP Slang Decoding & Content Analysis

**Objective**: Decode narcotics slang, coded language, and obfuscated
communication.

**Actions**:
1. Process all text evidence through the Language Agent
2. Maintain and apply the **Indian Narcotics Slang Lexicon**:

   | Slang Term       | Substance       | Region         | Confidence |
   |------------------|-----------------|----------------|------------|
   | maal             | Generic drugs   | Pan-India      | HIGH       |
   | stuff            | Heroin/Cocaine  | Pan-India      | MEDIUM     |
   | gaanja/ganja     | Cannabis        | Pan-India      | HIGH       |
   | chitta           | Heroin          | Punjab         | HIGH       |
   | brown sugar      | Heroin (impure) | Pan-India      | HIGH       |
   | cream            | Cocaine         | Metro cities   | MEDIUM     |
   | ice              | Methamphetamine | Pan-India      | HIGH       |
   | tabs/acid/trips  | LSD             | Urban          | HIGH       |
   | molly            | MDMA            | Urban/Party    | HIGH       |
   | hash/charas      | Hashish         | North India    | HIGH       |
   | sulpha           | Pharma opioids  | Punjab/Haryana | HIGH       |
   | pudiya           | Small drug pack | North India    | HIGH       |

3. Detect coded transaction patterns:
   - Price discussions disguised as normal commerce
   - Dead-drop location references
   - Quantity codes (e.g., "2 shirts" = 2 grams)
   - Payment method references (UPI, hawala, crypto)
4. Multi-language support: Hindi, Punjabi, Tamil, Telugu, Bengali, English
5. Confidence scoring for each decoded term (0-100)

**Output**: Annotated evidence with decoded meanings, confidence scores

---

### Stage 3: Entity Extraction & Identity Resolution

**Objective**: Build a structured entity database from raw intelligence.

**Actions**:
1. Extract ALL identifiable entities:
   - Phone numbers (Indian format: +91 XXXXX XXXXX)
   - Email addresses
   - Social media handles (Telegram, Instagram, WhatsApp, Snapchat)
   - Crypto wallet addresses (BTC, ETH, USDT, etc.)
   - UPI IDs
   - Physical addresses / landmarks
   - Vehicle registrations
   - Aadhaar / PAN references (masked for privacy)
   - IP addresses
   - Domain names
2. Cross-reference entities across platforms:
   - Same phone number on Telegram + WhatsApp
   - Same username variants across platforms
   - Shared crypto wallets between vendors
3. Resolve identities:
   - Link entities to probable real persons
   - Assign confidence scores to each linkage
4. Store entities in memory for cross-investigation correlation

**Output**: Entity database in JSON format with cross-reference map

---

### Stage 4: Graph Construction & Network Analysis

**Objective**: Build and analyze the narcotics supply chain network graph.

**Actions**:
1. Construct a directed graph:
   - **Nodes**: Entities (persons, accounts, wallets, locations)
   - **Edges**: Relationships (communicates_with, transacts_with,
     ships_to, controls, aliases_of)
2. Annotate edges with:
   - Relationship type
   - Evidence source
   - Confidence score
   - First/last seen timestamps
3. Apply graph algorithms:
   - **Centrality analysis**: Identify kingpins (highest betweenness centrality)
   - **Community detection**: Find operational cells/clusters
   - **Path analysis**: Trace supply chain from source to consumer
   - **Temporal analysis**: Detect activity patterns (time-of-day, day-of-week)
4. Identify key structural roles:
   - Source suppliers
   - Distributors / middlemen
   - Mules / couriers
   - Financial operators (money launderers)
   - Digital operators (channel admins, bot operators)
5. Generate graph visualization data for the dashboard

**Output**: Network graph in JSON, role assignments, centrality scores

---

### Stage 5: Cross-Platform Correlation

**Objective**: Correlate intelligence across platforms and data sources.

**Actions**:
1. Cross-reference extracted entities across:
   - Messaging platforms (Telegram, WhatsApp, Signal, Wickr)
   - Social media (Instagram, Facebook, Twitter/X, Snapchat)
   - Marketplaces (dark web markets, public classifieds)
   - Financial systems (crypto exchanges, UPI, bank references)
   - Government databases (if authorized access is available)
2. Apply correlation techniques:
   - Username similarity matching (Levenshtein distance, soundex)
   - Temporal correlation (same-time-window activity across platforms)
   - Network overlap (shared contacts across platforms)
   - Financial flow correlation (matching amounts and timestamps)
   - Linguistic fingerprinting (writing style analysis)
3. Build a unified identity graph with multi-platform evidence chains
4. Flag potential law enforcement interest overlaps

**Output**: Correlation matrix, unified identity profiles

---

### Stage 6: Risk Scoring & Threat Assessment

**Objective**: Score each entity and the overall network for operational risk.

**Actions**:
1. Apply the Rakshastra Threat Scoring Matrix:

   | Factor                     | Weight | Scale   |
   |----------------------------|--------|---------|
   | Substance severity (NDPS)  | 0.25   | 1-10    |
   | Distribution scale         | 0.20   | 1-10    |
   | Network reach              | 0.15   | 1-10    |
   | Financial sophistication   | 0.15   | 1-10    |
   | Digital operational security| 0.10  | 1-10    |
   | Cross-border indicators    | 0.10   | 1-10    |
   | Recidivism indicators      | 0.05   | 1-10    |

2. Classify entities by threat tier:
   - **CRITICAL** (9.0-10.0): Immediate intervention required
   - **HIGH** (7.0-8.9): Priority investigation target
   - **MEDIUM** (4.0-6.9): Monitoring recommended
   - **LOW** (1.0-3.9): Peripheral / consumer-level
3. Generate NDPS Act section mapping:
   - Map detected substances to specific NDPS Act sections
   - Estimate applicable sentencing ranges
   - Flag commercial quantity thresholds
4. Produce actionable intelligence brief for each CRITICAL/HIGH entity

**Output**: Risk scores, threat tiers, NDPS Act mapping, priority target list

---

### Stage 7: Attribution & Evidence Chain

**Objective**: Build prosecution-grade evidence chains.

**Actions**:
1. For each high-priority target, construct:
   - **Evidence chain**: Source → extraction method → entity → correlation →
     attribution (each link timestamped and hash-verified)
   - **Confidence assessment**: Overall attribution confidence with methodology
   - **Counter-arguments**: Identify weaknesses in the evidence chain
2. Document chain of custody:
   - Original source URL/location
   - Collection timestamp (UTC)
   - Collection method and tool
   - File hash (SHA-256)
   - Analyst who triggered collection (the investigator)
3. Separate facts from inference:
   - **FACT**: Directly observed data points
   - **INFERENCE**: Conclusions drawn from correlation
   - **ASSESSMENT**: Analytical judgments with confidence levels
4. Generate court-compatible documentation format

**Output**: Evidence chain documents, chain of custody logs

---

### Stage 8: Intelligence Report Generation

**Objective**: Produce a comprehensive intelligence report.

**Actions**:
1. Generate the **Rakshastra Intelligence Report (RIR)**:

   ```
   ╔══════════════════════════════════════════════════════════════╗
   ║  RAKSHASTRA INTELLIGENCE REPORT                             ║
   ║  Classification: [LEA CONFIDENTIAL]                         ║
   ╠══════════════════════════════════════════════════════════════╣
   ║  Case ID:          CASE-XXXX-NDPS-XXX                       ║
   ║  Date Generated:   YYYY-MM-DD HH:MM UTC                     ║
   ║  Investigator:     [Requesting Officer]                     ║
   ║  Threat Level:     [CRITICAL/HIGH/MEDIUM/LOW]               ║
   ╚══════════════════════════════════════════════════════════════╝

   1. EXECUTIVE SUMMARY
      - Key findings in 3-5 bullet points
      - Recommended immediate actions

   2. TARGET PROFILE
      - Primary subject(s) identification
      - Known aliases and platform presence
      - Network role classification

   3. INTELLIGENCE ANALYSIS
      - Substance identification and NDPS mapping
      - Supply chain topology
      - Financial flow analysis
      - Geographic distribution pattern

   4. NETWORK GRAPH
      - Visual representation of entity relationships
      - Centrality analysis results
      - Community/cell identification

   5. RISK ASSESSMENT
      - Threat scoring breakdown
      - Priority target list
      - Recommended intervention strategy

   6. EVIDENCE INVENTORY
      - Catalogued evidence with hashes
      - Source provenance
      - Chain of custody documentation

   7. LEGAL FRAMEWORK
      - Applicable NDPS Act sections
      - IT Act provisions (Section 66A, 67, 69, 79)
      - Evidence admissibility assessment

   8. RECOMMENDATIONS
      - Immediate actions
      - Long-term monitoring recommendations
      - Inter-agency coordination suggestions
      - Technical surveillance recommendations

   APPENDICES
      A. Raw evidence catalog
      B. Entity database export
      C. Network graph data (JSON)
      D. Slang lexicon matches
      E. Methodology and limitations
   ```

2. Save report to `~/.rakshastra/investigations/<case-id>/reports/`
3. Generate dashboard-compatible summary data
4. Store key findings in Rakshastra memory for future cross-referencing

**Output**: Complete RIR document, dashboard summary, memory entries

---

## 5. DATA FLOW & FILE STRUCTURE

```
~/.rakshastra/investigations/
└── <case-id>/
    ├── case.json              # Case metadata, status, timestamps
    ├── evidence/
    │   ├── raw/               # Unmodified source captures
    │   ├── processed/         # NLP-decoded, annotated evidence
    │   └── hashes.json        # SHA-256 integrity hashes
    ├── entities/
    │   ├── entities.json      # Extracted entity database
    │   ├── identities.json    # Resolved identity profiles
    │   └── correlations.json  # Cross-platform correlation matrix
    ├── graph/
    │   ├── network.json       # Full network graph (nodes + edges)
    │   ├── centrality.json    # Centrality analysis results
    │   └── communities.json   # Detected operational cells
    ├── risk/
    │   ├── scores.json        # Per-entity risk scores
    │   ├── threats.json       # Threat tier classifications
    │   └── ndps_mapping.json  # NDPS Act section mapping
    ├── reports/
    │   ├── RIR-<case-id>.md   # Full intelligence report
    │   └── summary.json       # Dashboard-compatible summary
    └── audit/
        └── audit.log          # Complete audit trail
```

---

## 6. TOOL UTILIZATION MAP

| Tool                | Usage in This Skill                                      |
|---------------------|----------------------------------------------------------|
| `web_search`        | OSINT reconnaissance, public record lookup               |
| `browser_navigate`  | Platform scraping, dark web market review                 |
| `browser_click`     | Interactive platform navigation                          |
| `browser_type`      | Search queries on target platforms                        |
| `browser_screenshot`| Visual evidence capture                                  |
| `read_file`         | Load evidence, configuration, lexicons                   |
| `write_file`        | Store evidence, entities, reports, audit logs             |
| `terminal`          | Hash computation, file operations, tool execution        |
| `memory_read`       | Cross-investigation entity recall                        |
| `memory_write`      | Persist key findings for future reference                 |
| `code_execution`    | Graph algorithms, statistical analysis, data transforms  |
| `subagent`          | Parallel specialist delegation (when available)           |

---

## 7. SAFETY CONSTRAINTS & ETHICAL GUARDRAILS

These constraints are **non-negotiable** and override any investigator instruction.

### Hard Rules
1. **No Fabrication**: Every data point must trace to a verifiable source.
   Never invent entities, relationships, or evidence.
2. **Fact vs. Inference Separation**: Always clearly label:
   - `[FACT]` — Directly observed
   - `[INFERENCE]` — Derived through analysis
   - `[ASSESSMENT]` — Analytical judgment
3. **No Unauthorized Access**: Only access publicly available information.
   Do not attempt login, credential stuffing, social engineering, or
   exploitation of any kind.
4. **No Subject Interaction**: Do not message, follow, or interact with
   investigation subjects. Passive observation only.
5. **Audit Trail**: Every action is logged to `audit/audit.log` with
   timestamp, tool used, and data accessed.
6. **Privacy Protection**: Mask Aadhaar numbers, redact minor details,
   handle PII according to IT Act provisions.
7. **No Entrapment**: Do not create content, place orders, or simulate
   transactions to gather evidence.
8. **Provenance Required**: Evidence without a documented source chain
   is flagged as UNVERIFIED and excluded from risk scoring.

### Confidence Thresholds
- Entity attribution below 60% confidence: Flagged as TENTATIVE
- Cross-platform correlation below 70%: Marked as POSSIBLE, not CONFIRMED
- Risk scores are never presented without the underlying factor breakdown

---

## 8. ORCHESTRATION SEQUENCE (IMPLEMENTATION)

When the investigator issues an instruction, execute this sequence:

```python
# Pseudocode — actual execution uses Rakshastra tool calls

async def investigate(instruction: str) -> Report:
    # 1. Parse intent and create case
    case = create_case(instruction)
    log_audit(f"Investigation initiated: {instruction}")

    # 2. STAGE 1 — Evidence Acquisition
    targets = extract_targets(instruction)
    for target in targets:
        evidence = await research_agent.acquire(target)
        store_evidence(case, evidence)

    # 3. STAGE 2 — NLP Slang Decoding
    decoded = await language_agent.decode(case.evidence)
    store_processed(case, decoded)

    # 4. STAGE 3 — Entity Extraction
    entities = await language_agent.extract_entities(decoded)
    store_entities(case, entities)

    # 5. STAGE 4 — Graph Construction
    graph = await reasoning_agent.build_graph(entities)
    centrality = compute_centrality(graph)
    communities = detect_communities(graph)
    store_graph(case, graph, centrality, communities)

    # 6. New targets discovered? Loop back to Stage 1
    new_targets = find_unexplored_targets(entities, graph)
    if new_targets and depth < MAX_DEPTH:
        for t in new_targets:
            evidence = await research_agent.acquire(t)
            store_evidence(case, evidence)
        # Re-run stages 2-5 with expanded evidence

    # 7. STAGE 5 — Cross-Platform Correlation
    correlations = await reasoning_agent.correlate(entities, graph)
    store_correlations(case, correlations)

    # 8. STAGE 6 — Risk Scoring
    scores = await risk_agent.score(entities, graph, correlations)
    store_risk(case, scores)

    # 9. STAGE 7 — Attribution
    chains = await reasoning_agent.attribute(entities, scores)
    store_attribution(case, chains)

    # 10. STAGE 8 — Report
    report = await report_agent.generate(case)
    store_report(case, report)

    # 11. Persist to memory for cross-investigation recall
    await memory_agent.persist(case.key_findings)

    log_audit(f"Investigation complete: {case.id}")
    return report
```

---

## 9. EXAMPLE INTERACTIONS

### Example 1: Telegram Channel Investigation
```
Investigator: "Investigate Telegram channel @DarkLabPunjab"

Rakshastra:
→ [STAGE 1] Acquiring evidence from @DarkLabPunjab via browser...
  ✓ 847 messages captured (public channel)
  ✓ 12 media files documented
  ✓ Admin list extracted: 3 administrators

→ [STAGE 2] Decoding narcotics slang...
  ✓ 67 matches found across 847 messages
  ✓ Primary substances: Heroin (chitta), Cannabis (maal)
  ✓ Transaction patterns: 23 suspected deals

→ [STAGE 3] Extracting entities...
  ✓ 8 phone numbers, 5 Telegram handles, 2 UPI IDs, 1 BTC wallet
  ✓ 3 probable identities resolved

→ [STAGE 4] Building network graph...
  ✓ 14 nodes, 31 edges constructed
  ✓ Kingpin candidate identified: Node TG-ADMIN-001 (centrality: 0.89)

→ [STAGE 5] Cross-platform correlation...
  ✓ TG-ADMIN-001 matched to Instagram handle @NeonTripsIndia (87% confidence)
  ✓ Shared phone number confirmed on WhatsApp

→ [STAGE 6] Risk scoring complete...
  ✓ TG-ADMIN-001: CRITICAL (9.2/10)
  ✓ 2 entities scored HIGH, 5 scored MEDIUM

→ [STAGE 7] Evidence chain constructed...
  ✓ 3 prosecution-grade chains documented
  ✓ SHA-256 hashes verified for all evidence

→ [STAGE 8] Report generated...
  ✓ RIR-2026-NDPS-089.md saved to investigations folder
  ✓ Key findings persisted to memory
```

### Example 2: Crypto Wallet Tracing
```
Investigator: "Trace this Bitcoin wallet: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"

Rakshastra:
→ Initiating blockchain analysis...
→ Querying public blockchain explorers...
→ 47 transactions identified across 8 months
→ Fund flow analysis: Mixing service detected (Wasabi Wallet pattern)
→ 3 exit wallets traced to KYC exchanges
→ Cross-referencing with known narcotics market wallets...
→ Report: RIR-2026-CRYPTO-042.md generated
```

---

## 10. LEGAL FRAMEWORK REFERENCE

This skill references and maps findings to:

| Statute                          | Relevance                                    |
|----------------------------------|----------------------------------------------|
| NDPS Act, 1985                   | Substance classification, sentencing         |
| IT Act, 2000 — S.66A             | Offensive online communication               |
| IT Act, 2000 — S.67              | Publishing obscene material electronically   |
| IT Act, 2000 — S.69              | Power to issue directions for interception    |
| IT Act, 2000 — S.79              | Intermediary liability                       |
| Prevention of Money Laundering   | Financial flow analysis                      |
| Indian Evidence Act — S.65B      | Electronic evidence admissibility            |
| Bharatiya Nyaya Sanhita (BNS)    | Criminal conspiracy, abetment               |

---

## 11. DASHBOARD INTEGRATION

The skill pushes live data to the Rakshastra dashboard:

- **Entity Graph**: Nodes and edges for the cross-platform entity graph panel
- **Threat Heatmap**: Geographic risk data for the India heatmap
- **Alert Feed**: Real-time alerts as entities are flagged
- **Timeline**: Investigation stage progression events
- **Evidence Locker**: Catalogued evidence with integrity hashes
- **AI Reasoning Panel**: Live reasoning steps from each specialist agent

All dashboard data is served through the existing `/api/status` and session
infrastructure — no additional API endpoints are required.

---

## 12. CROSS-INVESTIGATION MEMORY

This skill uses Rakshastra's memory system to persist:

- **Entity fingerprints**: Phone numbers, handles, wallets seen across cases
- **Network patterns**: Recurring supply chain topologies
- **Slang evolution**: New coded terms discovered during investigations
- **Modus operandi**: Identified operational patterns

When a new investigation begins, the memory is queried for prior matches,
enabling cross-case correlation and pattern detection across investigations.

---

## 13. LIMITATIONS & DISCLAIMERS

1. This skill operates on **publicly available information only**.
2. All intelligence products are **analytical assessments**, not legal
   determinations.
3. Risk scores are based on observable indicators and should be validated
   by qualified investigators before operational action.
4. The slang lexicon requires periodic updates as coded language evolves.
5. Cross-platform correlation confidence should be independently verified
   before being used as the basis for legal proceedings.
6. This tool does not replace human judgment in investigation decisions.

---

## 14. DRUG INTELLIGENCE ENGINE BACKEND (scripts/narcotics_agent.py)

To facilitate autonomous and programmatic analyses during the hackathon, the **Drug Intelligence Engine** is packaged with a dedicated Python script:
[narcotics_agent.py](file:///c:/Rakshastra/skills/security/narcotics-intelligence/scripts/narcotics_agent.py).

### Features
- **Dynamic Model Resolution**: Uses whatever active model is selected by the user in `config.yaml` using the core `call_llm` client.
- **Multilingual NLP Slang Deciphering**: Decodes Hinglish, Hindi, Punjabi, and local street slangs dynamically via LLM context prompting.
- **Emoji-based Trade Codes**: Automatically flags emojis representing contraband or dealer communication chains (e.g. `❄️`, `🍁`, `💊`, `💉`, `🔌`).
- **Unified Social Analysis**: Scans chat logs, user stories, and post content for Telegram, WhatsApp, and Instagram.
- **LEA Report Export**: Outputs a court-ready detailed Markdown intelligence report including suspected NDPS Act sections, risk scores, extracted target entities, and cryptographic SHA-256 evidence hashes.

### Usage
Run the script using the Rakshastra virtual environment:
```bash
.venv\Scripts\python.exe skills/security/narcotics-intelligence/scripts/narcotics_agent.py --input <path_to_raw_feed_file> --platform <all|telegram|whatsapp|instagram> --output <path_to_report.md>
```
