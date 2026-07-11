# Algorand x402 Pay-Per-Request Integration Plan

## 1. What gets Unlocked by Payment

While Rakshastra provides a free tier for local/manual investigations, the production-grade intelligence APIs are secured behind Algorand-backed x402 payment verification hooks. Paying customers unlock:
- **High-Fidelity Threat Classification (`/api/v1/threat/analyze-text`)**: Modular scans against the 9 major threat intelligence packs.
- **Entity Footprint Correlation (`/api/v1/entity/correlate`)**: Resolving aliases and tracking identifier reuse across historical datasets.
- **Explainable Reasoning (`/api/v1/report/generate`)**: Generating structured AI narratives and Markdown reports.

## 2. API Payment Boundary

Paid endpoints are marked with an x402 payment validation wrapper:
- **Free Endpoint**: `GET /api/v1/status` (Health/Node status checks).
- **Paid Endpoint**: `POST /api/v1/threat/analyze-text`, `POST /api/v1/entity/correlate`.

Requests to paid endpoints must include an Algorand Transaction ID (`X-Algorand-Tx-ID`) verifying that the correct fee (e.g. 0.05 ALGO per query) was transferred to the server's public wallet address.

## 3. pay-per-request Verification Architecture

```
Client Request (with X-Algorand-Tx-ID)
       ↓
API Payment Gateway Hook
       ↓
Query Algorand Node/Indexer (Verify Tx amount, recipient, and uniqueness)
       ↓
    [Valid] → Process request via Gemini-First Engine
    [Invalid] → Return 402 Payment Required
```

### Uniqueness and Double-Spend Protection
To prevent transaction ID replay attacks, the server maintains a SQLite table of verified transaction IDs (`verified_x402_txs`). If an ID is submitted more than once, it is rejected.

## 4. Mainnet & Leaderboard Readiness

- **Standard Token Fees**: Supports micro-payments in ALGO or custom Algorand Standard Assets (ASAs).
- **Leaderboard Tracking**: High-performance servers report verified x402 usage statistics to a public blockchain dashboard, creating a verifiable leaderboard of platform usage.
