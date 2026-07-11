import tempfile
from pathlib import Path
from rakshastra_core.intelligence import InvestigationTimelineEngine

def test_timeline_engine_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_timeline.db"
        engine = InvestigationTimelineEngine(db_path)
        session_id = "investigation_session_001"

        # 1. Add Events out of chronological order
        engine.add_event("EV3", session_id, "2026-07-09T10:15:00Z", "risk_changed", "Risk increased to 0.75", {"risk_score": 0.75})
        engine.add_event("EV1", session_id, "2026-07-09T10:00:00Z", "message_collected", "Telegram message received", {"text": "buy molly"})
        engine.add_event("EV2", session_id, "2026-07-09T10:05:00Z", "entity_detected", "Phone number +919893212345 extracted", {"token": "+919893212345", "type": "phone"})
        engine.add_event("EV4", session_id, "2026-07-09T10:30:00Z", "evidence_created", "Evidence created for drug sales", {"id": "EVID-001", "finding": "MDMA drug sales"})

        # 2. Verify sorting
        timeline = engine.get_timeline(session_id)
        assert len(timeline) == 4
        # Chronological check (EV1: 10:00, EV2: 10:05, EV3: 10:15, EV4: 10:30)
        assert timeline[0]["id"] == "EV1"
        assert timeline[1]["id"] == "EV2"
        assert timeline[2]["id"] == "EV3"
        assert timeline[3]["id"] == "EV4"

        # 3. Replay up to EV2
        replay_state = engine.replay(session_id, up_to_index=1)
        assert replay_state["events_replayed_count"] == 2
        assert "+919893212345" in replay_state["cumulative_state"]["entities"]
        assert replay_state["cumulative_state"]["current_risk_score"] == 0.0

        # Replay entire timeline
        replay_all = engine.replay(session_id)
        assert replay_all["events_replayed_count"] == 4
        assert replay_all["cumulative_state"]["current_risk_score"] == 0.75
        assert len(replay_all["cumulative_state"]["evidence_records"]) == 1

        # 4. Exports
        json_export = engine.export_json(session_id)
        assert "timeline" in json_export
        
        csv_export = engine.export_csv(session_id)
        assert "Timestamp,Event Type" in csv_export
        
        md_export = engine.export_markdown(session_id)
        assert "# Investigation Timeline Report" in md_export
