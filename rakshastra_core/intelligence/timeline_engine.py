import json
import sqlite3
import csv
import io
from pathlib import Path
from typing import Dict, Any, List, Optional

class InvestigationTimelineEngine:
    """Ingests chronological investigation events and supports step replay and exports."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS timeline_events (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT,
                    event_type TEXT,
                    description TEXT,
                    properties TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def add_event(
        self,
        event_id: str,
        session_id: str,
        timestamp: str,
        event_type: str,
        description: str,
        properties: dict
    ) -> bool:
        """Add a chronological event block to the timeline."""
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO timeline_events (id, session_id, timestamp, event_type, description, properties)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, session_id, timestamp, event_type, description, json.dumps(properties))
            )
            conn.commit()
        finally:
            conn.close()
        return True

    def get_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve sorted timeline events for an investigation session."""
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT * FROM timeline_events 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
                """,
                (session_id,)
            ).fetchall()
            
            timeline = []
            for r in rows:
                timeline.append({
                    "id": r["id"],
                    "session_id": r["session_id"],
                    "timestamp": r["timestamp"],
                    "event_type": r["event_type"],
                    "description": r["description"],
                    "properties": json.loads(r["properties"] or "{}")
                })
            return timeline
        finally:
            conn.close()

    # ── Replay Capability ────────────────────────────────────────────────────

    def replay(self, session_id: str, up_to_index: Optional[int] = None, up_to_timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Reconstruct the cumulative state of the investigation up to a point in time or step index."""
        events = self.get_timeline(session_id)
        
        # Filter events
        filtered_events = []
        for i, ev in enumerate(events):
            if up_to_index is not None and i > up_to_index:
                break
            if up_to_timestamp is not None and ev["timestamp"] > up_to_timestamp:
                break
            filtered_events.append(ev)

        # Build cumulative state
        extracted_entities = {}
        risk_score = 0.0
        evidence_records = []
        messages_processed = []

        for ev in filtered_events:
            etype = ev["event_type"]
            props = ev["properties"]

            if etype == "message_collected":
                messages_processed.append(props.get("text", ""))
            elif etype == "entity_detected":
                token = props.get("token")
                if token:
                    extracted_entities[token] = props.get("type", "unknown")
            elif etype == "risk_changed":
                risk_score = props.get("risk_score", risk_score)
            elif etype == "evidence_created":
                evidence_records.append({
                    "id": props.get("id"),
                    "finding": props.get("finding")
                })

        return {
            "session_id": session_id,
            "events_replayed_count": len(filtered_events),
            "replayed_events": filtered_events,
            "cumulative_state": {
                "entities": extracted_entities,
                "current_risk_score": risk_score,
                "evidence_records": evidence_records,
                "messages_processed_count": len(messages_processed)
            }
        }

    # ── Export Formats ───────────────────────────────────────────────────────

    def export_json(self, session_id: str) -> str:
        """Export timeline events as JSON string."""
        events = self.get_timeline(session_id)
        return json.dumps({"session_id": session_id, "timeline": events}, indent=2)

    def export_csv(self, session_id: str) -> str:
        """Export timeline events as CSV string."""
        events = self.get_timeline(session_id)
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["ID", "Timestamp", "Event Type", "Description", "Properties"])
        for ev in events:
            writer.writerow([
                ev["id"],
                ev["timestamp"],
                ev["event_type"],
                ev["description"],
                json.dumps(ev["properties"])
            ])
            
        return output.getvalue()

    def export_markdown(self, session_id: str) -> str:
        """Export timeline events as a formatted Markdown document."""
        events = self.get_timeline(session_id)
        md = []
        md.append(f"# Investigation Timeline Report: {session_id}")
        md.append(f"Generated chronological timeline containing {len(events)} events.")
        md.append("\n---\n")

        for idx, ev in enumerate(events):
            md.append(f"### {idx + 1}. [{ev['timestamp']}] {ev['event_type'].upper()}")
            md.append(f"**Description**: {ev['description']}")
            if ev["properties"]:
                md.append("**Details**:")
                for k, v in ev["properties"].items():
                    md.append(f"- **{k}**: {v}")
            md.append("\n---\n")
            
        return "\n".join(md)
