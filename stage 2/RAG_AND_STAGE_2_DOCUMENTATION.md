# Rakshastra Cyber Defense — RAG & Stage 2 Documentation

This document explains the architecture implemented in **Stage 2** (APT Attribution, Threat Predictors, SOAR, Graph AI, and Frontend Dashboard) and the subsequent **RAG Upgrade** integrating Qdrant vector database and Hugging Face embeddings.

---

## 🛠️ Summary of Changes: Stage 2 to RAG

The implementation consists of two main phases:

### Phase 1: Stage 2 Core Architecture
We established the end-to-end threat intelligence and incident response pipeline:
1. **MITRE ATT&CK Store (`mitre_attack_store.py`)**: Knowledge Graph seeding 40+ threat actors and techniques.
2. **Attribution Engine (`apt_attribution.py`)**: Calculates similarity coefficients between observed actions and actor profiles.
3. **Attack Predictor (`attack_predictor.py`)**: Markov-chain prediction model suggesting likely next TTPs and host mitigations.
4. **Graph AI Engine (`attack_graph.py`)**: BFS path calculations mapping compromised assets, blast radii, and network chokepoints.
5. **Enhanced UEBA (`behavioral_analytics.py`)**: Adds multi-phase beaconing and data staging detection.
6. **SOAR Response (`soar_engine.py`)**: Automated execution/simulation of mitigation playbooks (e.g. ransomware containment).
7. **Service & API Layers**: Fully wired FastAPI models, controllers, and router configurations.
8. **Interactive UI (`APTDashboardPage.tsx`)**: Premium dark-themed dashboard combining active incident response, prediction, search, and SOAR controls.

### Phase 2: RAG Upgrades (Vector Semantic Search)
We upgraded the threat intelligence repository from simple keyword-based matching to **hybrid vector semantic search**:
* **Qdrant Vector Database Integration**: Added a dedicated `qdrant` vector storage service inside `docker-compose.yml`.
* **Multi-Provider Embeddings Pipeline**: Programmed `_get_embeddings` to check and leverage:
  1. **Hugging Face Serverless Inference API** (using `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions).
  2. **OpenAI Embeddings API** (`text-embedding-3-small` at 1536 dimensions).
  3. **Gemini Embeddings API** (`text-embedding-004` at 1536 dimensions).
  4. **Deterministic Fallback**: Offline seed hashing (SHA-256) mapping deterministic mock vectors so testing does not require internet or API credentials.
* **Dynamic Dimensions:** Added automatic vector dimension calculation to dynamically resize Qdrant collections depending on the selected provider.
* **Robust Fallback:** Retains the SQLite FTS5 BM25 search mechanism. If Qdrant goes offline, the RAG engine seamlessly degrades to SQLite search, preventing crashes.

---

## 🚀 Installation Guide

Follow these steps to set up and run the vector RAG database:

### 1. Prerequisite
Ensure **Docker Desktop** (or the Docker daemon) is started and running on your host system.

### 2. Start the Qdrant Vector DB
Run the following command in your project root to pull and start the Qdrant container:
```bash
docker compose up -d qdrant
```
This launches Qdrant at `http://localhost:6333` with persistent storage mapped to `~/.rakshastra/qdrant_data`.

### 3. Configure API Credentials (Optional)
To use Hugging Face, OpenAI, or Gemini for real embeddings, add the appropriate key to your system environment or a `.env` file in the project root:

```bash
# For Hugging Face Serverless API (Recommended Free Option)
HF_TOKEN=your_hugging_face_token_here

# For OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# For Gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 📖 Usage Guide

### 1. Run the RAG Validator
We have provided a validation script to test connection, ingestion, vector synchronization, and semantic query matching:
```bash
python scratch/test_qdrant_rag.py
```
If Qdrant is running, it will output: `[SUCCESS] Successfully connected to Qdrant Vector Database!` and show semantic match results.

### 2. Backend Python API
In corporate modules, import and query the RAG engine:

```python
from rakshastra_core.intelligence.threat_intel_rag import ThreatIntelRAG

# Initialize RAG (automatically connects to local Qdrant or falls back to SQLite)
rag = ThreatIntelRAG(db_path="data/threat_intel_rag.db")

# Ingest new advisory
rag.ingest_advisory(
    doc_id="CERT-IN-2026-04",
    source_type="cert_in",
    title="Credential Dumping Attack Warning",
    content="Attackers are targeting LSASS memory to harvest domain credentials...",
    severity="CRITICAL",
    tags=["lsass", "credential_access"]
)

# Perform Semantic Search
results = rag.search("LSASS dumping mitigations")
for doc in results:
    print(doc["title"], doc["mitigations"])
```

### 3. Web Dashboard Search
1. Start the Rakshastra web server and open the dashboard in your browser.
2. Click **APT Attribution** in the sidebar.
3. Scroll to the **Threat Intelligence RAG Explorer** widget.
4. Enter any query (e.g., *"LockBit ransomware"* or *"Ivanti authentication bypass"*). The interface will execute semantic vector search and display ranked alerts, mitigations, and affected assets.
