import tempfile
from pathlib import Path
from rakshastra_core.intelligence import GraphEngine

def test_graph_engine_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_graph.db"
        engine = GraphEngine(db_path)

        # 1. Add Nodes
        engine.add_node("N1", "People", "Alice (Suspect)", {"role": "moderator"})
        engine.add_node("N2", "Accounts", "@DirectMedsExpress", {"platform": "telegram"})
        engine.add_node("N3", "Wallets", "0xabc123", {"balance": "1.4 BTC"})
        engine.add_node("N4", "Phones", "+919893212345", {})

        # 2. Add Edges
        engine.add_edge("E1", "N1", "N2", "owns", {"timestamp": "2026-07-09T10:00:00Z", "description": "Alice owns Telegram account"})
        engine.add_edge("E2", "N2", "N3", "transferred", {"timestamp": "2026-07-09T11:30:00Z", "amount": 0.5, "currency": "BTC", "description": "Transferred BTC to dealer wallet"})
        engine.add_edge("E3", "N2", "N4", "communicated", {"timestamp": "2026-07-09T10:15:00Z", "description": "Communicated via text"})

        # 3. Get entire graph JSON
        graph_data = engine.get_graph_json()
        assert len(graph_data["nodes"]) == 4
        assert len(graph_data["edges"]) == 3

        # 4. Force-Directed Layout
        layout_data = engine.compute_force_directed_layout(iterations=5)
        # Verify positions changed or exist
        n1 = next(n for n in layout_data["nodes"] if n["id"] == "N1")
        assert "x" in n1 and "y" in n1

        # 5. Expand Graph (1 hop from N1)
        expanded_1 = engine.expand_graph("N1", hops=1)
        assert len(expanded_1["nodes"]) == 2  # N1 and N2 (connected by owns)
        assert len(expanded_1["edges"]) == 1

        # Expand Graph (2 hops from N1)
        expanded_2 = engine.expand_graph("N1", hops=2)
        assert len(expanded_2["nodes"]) == 4  # Alice, telegram, wallet, phone
        assert len(expanded_2["edges"]) == 3

        # 6. Timeline Reconstruction
        timeline = engine.reconstruct_timeline()
        assert len(timeline) == 3
        # Check chronological order (E1: 10:00, E3: 10:15, E2: 11:30)
        assert timeline[0]["description"] == "Alice owns Telegram account"
        assert timeline[1]["description"] == "Communicated via text"
        assert timeline[2]["description"] == "Transferred BTC to dealer wallet"

        # 7. Save Snapshot and History
        snap_id = engine.save_snapshot("Added nodes and edges")
        assert snap_id.startswith("SNAP-")
        
        history = engine.get_history()
        assert len(history) == 1
        assert history[0]["action"] == "Added nodes and edges"
        assert len(history[0]["snapshot"]["nodes"]) == 4
