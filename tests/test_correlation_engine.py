import tempfile
from pathlib import Path
from rakshastra_core.intelligence import GraphEngine, MultiSourceCorrelationEngine

def test_multi_source_correlation():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_correlation.db"
        graph_db = Path(tmpdir) / "test_graph.db"
        
        graph_engine = GraphEngine(graph_db)
        engine = MultiSourceCorrelationEngine(db_path, graph_engine)

        # 1. Add Investigation 1 (Telegram source)
        res1 = engine.process_evidence(
            session_id="INV-001",
            source_platform="Telegram",
            text="Channel moderator is @DirectMeds. Phone number is +919893212345. Wallet address is 0xabc1234567890123456789012345678901234567.",
            profile_photo_hash="photo_signature_abc"
        )
        assert len(res1["matched_evidence"]) == 0
        assert res1["confidence"] == 0.0

        # 2. Add Investigation 2 (WhatsApp source with reused phone and username)
        res2 = engine.process_evidence(
            session_id="INV-002",
            source_platform="WhatsApp",
            text="Reach me on WhatsApp +919893212345 or telegram @DirectMeds.",
            profile_photo_hash="photo_signature_xyz"
        )
        # Check correlation matches
        assert len(res2["matched_evidence"]) == 1
        match = res2["matched_evidence"][0]
        assert match["matching_session_id"] == "INV-001"
        assert "phone" in match["matched_indicators"]
        assert "username" in match["matched_indicators"]
        
        # High confidence for multiple overlaps (phone + username)
        assert res2["confidence"] >= 0.95
        assert res2["suggested_merge"] is not None
        assert res2["suggested_merge"]["session_a"] == "INV-002"
        assert res2["suggested_merge"]["session_b"] == "INV-001"
        assert res2["risk_increase"] > 0.40

        # 3. Add Investigation 3 (Discord source with reused profile photo)
        res3 = engine.process_evidence(
            session_id="INV-003",
            source_platform="Discord",
            text="Contact moderator on discord.",
            profile_photo_hash="photo_signature_abc" # Same as INV-001
        )
        assert len(res3["matched_evidence"]) == 1
        match3 = res3["matched_evidence"][0]
        assert match3["matching_session_id"] == "INV-001"
        assert "profile_photo" in match3["matched_indicators"]
        assert res3["confidence"] == 0.80
        assert res3["suggested_merge"] is not None
        assert res3["risk_increase"] == 0.40

        # 4. Verify Graph Engine is automatically updated
        graph_data = graph_engine.get_graph_json()
        
        # We should have nodes for INV-001, INV-002, INV-003 and the extracted tokens
        node_ids = [n["id"] for n in graph_data["nodes"]]
        assert "INV-001" in node_ids
        assert "INV-002" in node_ids
        assert "+919893212345" in node_ids
        assert "@DirectMeds" in node_ids
        
        # Check linkages between correlated investigations (owns/uses/connected_to)
        edges = graph_data["edges"]
        connection_edges = [e for e in edges if e["type"] == "connected_to"]
        assert len(connection_edges) > 0
