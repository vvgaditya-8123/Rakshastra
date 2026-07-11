import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from rakshastra_core.engines.infrastructure_graph import InfrastructureGraph

class IntelligenceGraph(InfrastructureGraph):
    """Extends the InfrastructureGraph to model criminal networks, operators, and transactional aliases."""

    def __init__(self, db_path: Path):
        super().__init__(db_path)
        self._ensure_intelligence_schema()

    def _ensure_intelligence_schema(self):
        conn = self._get_connection()
        try:
            # Table to store intelligence nodes specifically
            conn.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_nodes (
                    id TEXT PRIMARY KEY,
                    node_type TEXT, -- 'telegram', 'instagram', 'wallet', 'upi', 'phone', 'suspect'
                    display_name TEXT,
                    properties TEXT
                )
            """)
            # Table to store operator mapping/profile associations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_relations (
                    id TEXT PRIMARY KEY,
                    source_id TEXT,
                    target_id TEXT,
                    relation_type TEXT, -- 'owns', 'forwards_to', 'mentions', 'shares_media'
                    properties TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def add_intelligence_node(self, node_id: str, node_type: str, display_name: str, properties: dict) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO intelligence_nodes (id, node_type, display_name, properties)
                VALUES (?, ?, ?, ?)
                """,
                (node_id, node_type, display_name, json.dumps(properties))
            )
            conn.commit()
        finally:
            conn.close()

    def add_intelligence_relation(self, relation_id: str, source_id: str, target_id: str, relation_type: str, properties: dict) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO intelligence_relations (id, source_id, target_id, relation_type, properties)
                VALUES (?, ?, ?, ?, ?)
                """,
                (relation_id, source_id, target_id, relation_type, json.dumps(properties))
            )
            conn.commit()
        finally:
            conn.close()

    def get_criminal_network(self, suspect_id: str) -> Dict[str, Any]:
        """Traverse the intelligence relations table to build the mapped criminal network."""
        conn = self._get_connection()
        nodes = {}
        links = []
        try:
            # Simple level-1 and level-2 network extraction
            rows = conn.execute(
                """
                SELECT * FROM intelligence_relations 
                WHERE source_id = ? OR target_id = ?
                """,
                (suspect_id, suspect_id)
            ).fetchall()
            
            for row in rows:
                links.append({
                    "id": row["id"],
                    "source": row["source_id"],
                    "target": row["target_id"],
                    "relation_type": row["relation_type"],
                    "properties": json.loads(row["properties"] or "{}")
                })
                
                # Fetch details for the nodes involved
                for node_id in (row["source_id"], row["target_id"]):
                    if node_id not in nodes:
                        node_row = conn.execute("SELECT * FROM intelligence_nodes WHERE id = ?", (node_id,)).fetchone()
                        if node_row:
                            nodes[node_id] = {
                                "id": node_row["id"],
                                "type": node_row["node_type"],
                                "name": node_row["display_name"],
                                "properties": json.loads(node_row["properties"] or "{}")
                            }
                        else:
                            nodes[node_id] = {"id": node_id, "type": "unknown", "name": node_id, "properties": {}}
        finally:
            conn.close()

        return {
            "nodes": list(nodes.values()),
            "edges": links
        }
