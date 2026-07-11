# Rakshastra API Documentation

Rakshastra exposes a set of REST endpoints under `/api/v1/` for threat analysis, correlation, reporting, and graph operations.

## 1. Threat Analysis

### `POST /api/v1/threat/analyze-text`
Analyzes raw text against modular threat intelligence packs (scams, crypto fraud, phishing, etc.).
- **Input**:
  ```json
  {
    "text": "Send 0.05 BTC to bc1qxy2kg..."
  }
  ```
- **Output**:
  ```json
  {
    "risk_score": 0.85,
    "detected_threat": "Crypto Scam",
    "reasoning": "Matched crypto wallet address",
    "matched_indicators": ["bc1qxy2kg..."],
    "suggested_action": "Block address",
    "confidence": 0.95
  }
  ```

---

## 2. Entity Correlation

### `POST /api/v1/entity/correlate`
Compares extracted identifiers against historical cases to find reuse.
- **Input**:
  ```json
  {
    "session_id": "session_001",
    "source_platform": "Telegram",
    "text": "Moderator: @DirectMeds, Phone: +919893212345"
  }
  ```
- **Output**:
  ```json
  {
    "matched_evidence": [
      {
        "matching_session_id": "session_099",
        "confidence": 0.95,
        "matched_indicators": {
          "phone": ["+919893212345"]
        }
      }
    ],
    "confidence": 0.95,
    "reasoning": [
      "Reused phone(s) detected across investigations: ['+919893212345']"
    ],
    "suggested_merge": {
      "session_a": "session_001",
      "session_b": "session_099",
      "confidence": 0.95
    },
    "risk_increase": 0.475
  }
  ```

---

## 3. Explanation Generation

### `POST /api/v1/report/generate`
Generates natural language summaries and step-by-step reasoning chains.
- **Input**:
  ```json
  {
    "session_id": "session_001",
    "threat_output": { "risk_score": 0.85, "detected_threat": "Drug Intelligence" },
    "entity_output": {},
    "graph_output": {},
    "correlation_output": {}
  }
  ```
- **Output**:
  ```json
  {
    "threat_summary": {
      "what_was_found": "Detected MDMA sales indicators",
      "why_it_matters": "Active drug distribution network",
      "confidence": "85%",
      "overall_threat_level": "CRITICAL"
    },
    "reasoning_chain": [
      "Step 1: normalized text parsed",
      "Conclusion: drug network identified"
    ],
    "markdown_report": "# Explainable AI Report..."
  }
  ```
