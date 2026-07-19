import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rakshastra_core.intelligence.threat_intel_rag import ThreatIntelRAG

def test_qdrant_rag():
    print("====================================================")
    print("        RAKSHASTRA VECTOR RAG VALIDATOR             ")
    print("====================================================\n")
    
    # 1. Initialize RAG with a test DB file
    db_file = Path(__file__).parent / "temp_test_rag.db"
    if db_file.exists():
        os.remove(db_file)
        
    print(f"Connecting to Hybrid RAG (Qdrant URL: {os.environ.get('QDRANT_URL', 'http://localhost:6333')})...")
    rag = ThreatIntelRAG(db_path=str(db_file))
    
    # 2. Check Qdrant connection status
    summary = rag.get_summary()
    print(f"RAG Status Summary: {summary}\n")
    
    if summary["qdrant_connected"]:
        print("[SUCCESS] Successfully connected to Qdrant Vector Database!")
        print(f"Active collection 'threat_intel' verified at: {summary['qdrant_url']}\n")
    else:
        print("[WARNING] Could not connect to Qdrant. Operating in SQLite FTS5 fallback mode.")
        print("-> Make sure to run 'docker compose up -d qdrant' and try again.\n")
        
    # 3. Test Ingestion
    print("Ingesting test advisory...")
    doc_id = "TEST-ADVISORY-001"
    rag.ingest_advisory(
        doc_id=doc_id,
        source_type="cert_in",
        title="Validation Alert on Ransomware Beaconing Patterns",
        content="This is a test security advisory describing active beaconing behavior of LockBit affiliates targeting infrastructure assets.",
        published_date="2026-07-19",
        severity="HIGH",
        tags=["test", "beaconing", "lockbit"],
        cve_ids=["CVE-2023-4966"],
        apt_groups=["LockBit"]
    )
    print(f"Document {doc_id} ingested successfully.\n")
    
    # 4. Test Query Retrieval
    search_query = "LockBit beaconing assets"
    print(f"Executing semantic search for query: '{search_query}'...")
    results = rag.search(search_query, top_k=3)
    
    print(f"Found {len(results)} matching documents:")
    for i, doc in enumerate(results, 1):
        print(f"  {i}. [{doc['id']}] {doc['title']} (Severity: {doc['severity']})")
        print(f"     Excerpt: {doc['content'][:120]}...\n")
        
    # 5. Clean up local test DB file
    if db_file.exists():
        os.remove(db_file)
    print("Validation run complete.")

if __name__ == "__main__":
    test_qdrant_rag()
