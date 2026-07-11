import pytest
import tempfile
from pathlib import Path
from rakshastra_core.intelligence.keyword_engine import DrugSlangEngine
from rakshastra_core.intelligence.content_classifier import DrugIntelligenceEngine
from rakshastra_core.intelligence.bot_detector import BotDetector
from rakshastra_core.intelligence.entity_resolution import EntityResolutionEngine
from rakshastra_core.intelligence.intelligence_graph import IntelligenceGraph
from rakshastra_core.intelligence.threat_prioritization import ThreatPrioritizationEngine
from rakshastra_core.intelligence.audit_compliance import AuditComplianceEngine

@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "security.db"

def test_drug_slang_matching():
    engine = DrugSlangEngine()
    
    # Text matching mdma slang
    text_mdma = "Looking for molly and manda in Mumbai"
    slang_res = engine.detect_slang(text_mdma)
    assert "mdma" in slang_res
    assert "molly" in slang_res["mdma"]

    # Emoji matching
    text_emoji = "Deal ready: 💊🌿"
    emojis = engine.detect_emojis(text_emoji)
    assert "💊" in emojis
    assert "🌿" in emojis

    # Hinglish detection
    text_hinglish = "Bhai pure quality ka maal ready hai. Jaldi DM karo."
    assert engine.contains_hinglish_context(text_hinglish) is True

def test_drug_intelligence_engine():
    engine = DrugIntelligenceEngine()
    
    # Highly suspicious text
    res = engine.analyze_content("💊 molly ready here Mumbai. Maal ready hai.")
    assert res["drug_probability_score"] >= 0.8
    assert res["requires_investigation"] is True

def test_bot_detector():
    detector = BotDetector()
    
    # Highly repetitive messages with command shapes
    messages = [
        "/start",
        "Buy mdma now: click start to buy",
        "/start",
        "Buy mdma now: click start to buy",
        "/buy",
        "/price"
    ]
    res = detector.detect_bot_behavior(messages)
    assert res["is_automated"] is True
    assert res["automation_confidence"] >= 0.6

def test_entity_resolution():
    engine = EntityResolutionEngine()
    
    # Link phone, telegram handle, and crypto wallet
    engine.link_entities("+919999999999", "@dealer_xyz")
    engine.link_entities("@dealer_xyz", "0xDeAdBeEfFaCe1234567890123456789012345678")
    engine.link_entities("0xDeAdBeEfFaCe1234567890123456789012345678", "dealer@okaxis")

    profile = engine.resolve_operator("@dealer_xyz")
    assert profile["linked_nodes_count"] == 4
    assert "@dealer_xyz" in profile["usernames"]
    assert "+919999999999" in profile["phone_numbers"]
    assert "0xDeAdBeEfFaCe1234567890123456789012345678" in profile["crypto_wallets"]
    assert "dealer@okaxis" in profile["upi_ids"]

def test_intelligence_graph(temp_db):
    graph = IntelligenceGraph(temp_db)
    
    graph.add_intelligence_node("OP-1", "suspect", "Suspected Operator A", {"risk": "high"})
    graph.add_intelligence_node("TG-A", "telegram", "@mumbai_mdma_bot", {"followers": 1500})
    
    graph.add_intelligence_relation("rel-1", "OP-1", "TG-A", "owns", {"confidence": 0.95})
    
    network = graph.get_criminal_network("OP-1")
    assert len(network["nodes"]) == 2
    assert len(network["edges"]) == 1
    assert network["edges"][0]["relation_type"] == "owns"

def test_threat_prioritization():
    engine = ThreatPrioritizationEngine()
    
    targets = [
        {"name": "t1", "drug_probability": 0.9, "automation_confidence": 0.8, "platform_count": 3, "network_size": 15, "has_financials": True},
        {"name": "t2", "drug_probability": 0.2, "automation_confidence": 0.1, "platform_count": 1, "network_size": 2, "has_financials": False}
    ]
    
    prioritized = engine.prioritize_watchlist(targets)
    assert prioritized[0]["name"] == "t1"
    assert prioritized[0]["severity"] in ("CRITICAL", "HIGH")
    assert prioritized[1]["name"] == "t2"
    assert prioritized[1]["severity"] == "LOW"

def test_audit_compliance():
    engine = AuditComplianceEngine()
    
    log = engine.log_action("investigator_01", "entity_linking", "@suspect", "Telegram channel scrap")
    assert log["lawfulness_status"] == "VERIFIED_PUBLIC_OSINT"
