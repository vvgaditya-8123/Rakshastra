import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timezone
from rakshastra_core.intelligence.graph_engine import GraphEngine

class MLCorrelationClassifier:
    """Extension hook for future ML models (e.g. semantic similarity, image/profile photo matching)."""
    def predict_correlation(self, text_a: str, text_b: str) -> float:
        # Placeholder score for semantic correlation
        return 0.0

    def match_images(self, hash_a: str, hash_b: str) -> float:
        # Placeholder score for profile photo matching
        if hash_a and hash_b and hash_a == hash_b:
            return 1.0
        return 0.0


class MultiSourceCorrelationEngine:
    """Correlates intelligence from multiple platforms to find actor/investigation reuse and linkages."""

    SUPPORTED_SOURCES = {
        "Telegram", "WhatsApp", "Instagram", "Discord", 
        "Email", "OCR", "PDF", "Image", "Manual", "CSV"
    }

    CONFIDENCE_WEIGHTS = {
        "phone": 0.95,
        "wallet": 0.95,
        "email": 0.90,
        "username": 0.85,
        "profile_photo": 0.80,
        "invite_link": 0.75,
        "url": 0.60
    }

    def __init__(self, db_path: Path, graph_engine: GraphEngine):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.graph_engine = graph_engine
        self.ml_classifier = MLCorrelationClassifier()
        self._ensure_schema()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS correlation_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    entity_type TEXT,
                    token TEXT,
                    source_platform TEXT,
                    timestamp TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def extract_entities(self, text: str, source_platform: str) -> List[Tuple[str, str]]:
        """Extract indicators and identifiers from the raw input text."""
        if not text:
            return []

        extracted = []

        # Regex patterns
        patterns = {
            "phone": r'\+?\d{10,15}',
            "email": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,7}\b',
            "wallet": r'\b(?:0x[a-fA-F0-9]{40}|bc1[a-zA-Z0-9]{39,59})\b',
            "username": r'@\w+',
            "invite_link": r'(?:t\.me|chat\.whatsapp\.com|discord\.gg)\/[a-zA-Z0-9_\-]+',
            "url": r'https?://[^\s/$.?#].[^\s]*'
        }

        for etype, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                token = m.group(0).strip()
                extracted.append((token, etype))

        return list(set(extracted))

    def process_evidence(
        self,
        session_id: str,
        source_platform: str,
        text: str,
        profile_photo_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingest, extract, correlate, and automatically update the graph."""
        if source_platform not in self.SUPPORTED_SOURCES:
            raise ValueError(f"Unsupported source platform: {source_platform}")

        timestamp = datetime.now(timezone.utc).isoformat() + "Z"
        
        # 1. Extract Entities
        entities = self.extract_entities(text, source_platform)
        if profile_photo_hash:
            entities.append((profile_photo_hash, "profile_photo"))

        # Save to database
        conn = self._get_connection()
        try:
            for token, etype in entities:
                conn.execute(
                    """
                    INSERT INTO correlation_entities (session_id, entity_type, token, source_platform, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, etype, token, source_platform, timestamp)
                )
            conn.commit()
        finally:
            conn.close()

        # 2. Correlate with existing investigations (other session_ids)
        correlation_results = self._correlate_session(session_id, entities, text, profile_photo_hash)

        # 3. Automatically update the graph
        self._update_graph_with_correlation(session_id, entities, correlation_results)

        return correlation_results

    def _correlate_session(
        self,
        current_session_id: str,
        current_entities: List[Tuple[str, str]],
        current_text: str,
        current_photo_hash: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze intersections between the current session and historical sessions."""
        conn = self._get_connection()
        try:
            # Query all other session entities
            rows = conn.execute(
                "SELECT session_id, entity_type, token, source_platform FROM correlation_entities WHERE session_id != ?",
                (current_session_id,)
            ).fetchall()
        finally:
            conn.close()

        # Group historical entities by session
        historical_sessions: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            sid = r["session_id"]
            if sid not in historical_sessions:
                historical_sessions[sid] = []
            historical_sessions[sid].append({
                "type": r["entity_type"],
                "token": r["token"],
                "source": r["source_platform"]
            })

        matched_evidence = []
        highest_confidence = 0.0
        reasoning = []
        suggested_merge = None
        risk_increase = 0.0

        for sid, hist_entities in historical_sessions.items():
            matches: Dict[str, List[str]] = {}
            match_probs = []

            for cur_token, cur_type in current_entities:
                if cur_type == "profile_photo":
                    continue
                for hist in hist_entities:
                    if cur_token == hist["token"] and cur_type == hist["type"]:
                        if cur_type not in matches:
                            matches[cur_type] = []
                        matches[cur_type].append(cur_token)
                        
                        # Add match confidence
                        weight = self.CONFIDENCE_WEIGHTS.get(cur_type, 0.50)
                        match_probs.append(weight)

            # Check profile photo match using ML hook placeholder
            for hist in hist_entities:
                if hist["type"] == "profile_photo" and current_photo_hash:
                    photo_match_score = self.ml_classifier.match_images(current_photo_hash, hist["token"])
                    if photo_match_score > 0.70:
                        if "profile_photo" not in matches:
                            matches["profile_photo"] = []
                        matches["profile_photo"].append(current_photo_hash)
                        match_probs.append(self.CONFIDENCE_WEIGHTS["profile_photo"] * photo_match_score)

            if match_probs:
                # Probabilistic union logic: P(A or B) = 1 - (1 - P(A)) * (1 - P(B))
                combined_prob = 1.0
                for p in match_probs:
                    combined_prob *= (1.0 - p)
                session_conf = round(1.0 - combined_prob, 3)

                # Record match details
                matched_evidence.append({
                    "matching_session_id": sid,
                    "confidence": session_conf,
                    "matched_indicators": matches
                })

                if session_conf > highest_confidence:
                    highest_confidence = session_conf
                    suggested_merge = {
                        "session_a": current_session_id,
                        "session_b": sid,
                        "confidence": session_conf
                    }

                    # Populate reasoning points
                    reasoning = []
                    for etype, tokens in matches.items():
                        reasoning.append(f"Reused {etype}(s) detected across investigations: {tokens}")

        if highest_confidence > 0.0:
            # Risk increase scales with correlation confidence (up to a max of +0.50 risk score increment)
            risk_increase = round(highest_confidence * 0.5, 3)

        return {
            "matched_evidence": matched_evidence,
            "confidence": highest_confidence,
            "reasoning": reasoning,
            "suggested_merge": suggested_merge if highest_confidence >= 0.70 else None,
            "risk_increase": risk_increase
        }

    def _update_graph_with_correlation(
        self,
        session_id: str,
        entities: List[Tuple[str, str]],
        correlation_results: Dict[str, Any]
    ):
        """Build and link nodes in the GraphEngine reflecting these discoveries."""
        # 1. Add Investigation Node itself
        self.graph_engine.add_node(session_id, "Groups", f"Investigation {session_id}", {"state": "active"})

        # 2. Add Node for each entity and link to Investigation
        node_type_mapping = {
            "phone": "Phones",
            "email": "Emails",
            "wallet": "Wallets",
            "username": "Accounts",
            "invite_link": "Channels",
            "url": "Servers"
        }

        for token, etype in entities:
            gtype = node_type_mapping.get(etype, "Bots")
            self.graph_engine.add_node(token, gtype, token, {"type": etype})
            
            # Edge from Investigation (session_id) to Entity
            edge_id = f"E-{session_id[:4].upper()}-{token[:4].upper()}"
            self.graph_engine.add_edge(edge_id, session_id, token, "uses", {})

        # 3. Add link between correlated investigations if confidence is high
        for match in correlation_results["matched_evidence"]:
            if match["confidence"] >= 0.50:
                other_sid = match["matching_session_id"]
                edge_id = f"LINK-{session_id[:4].upper()}-{other_sid[:4].upper()}"
                self.graph_engine.add_edge(
                    edge_id,
                    session_id,
                    other_sid,
                    "connected_to",
                    {"confidence": match["confidence"], "reason": "Reused identifiers detected"}
                )
