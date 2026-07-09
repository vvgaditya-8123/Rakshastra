import json
import math
import sqlite3
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

class GraphEngine:
    """Manages threat intelligence networks, computes layouts, tracks histories, and builds timelines."""

    VALID_NODE_TYPES = {"People", "Accounts", "Wallets", "Phones", "Emails", "Servers", "Groups", "Channels", "Bots"}
    VALID_EDGE_TYPES = {"owns", "uses", "connected_to", "mentions", "paid", "transferred", "communicated"}

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
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    id TEXT PRIMARY KEY,
                    node_type TEXT,
                    label TEXT,
                    properties TEXT,
                    x REAL,
                    y REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_edges (
                    id TEXT PRIMARY KEY,
                    source TEXT,
                    target TEXT,
                    edge_type TEXT,
                    properties TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS investigation_history (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    action TEXT,
                    snapshot TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def add_node(self, node_id: str, node_type: str, label: str, properties: dict) -> bool:
        if node_type not in self.VALID_NODE_TYPES:
            raise ValueError(f"Invalid Node Type: {node_type}. Must be one of {self.VALID_NODE_TYPES}")
        
        conn = self._get_connection()
        try:
            # Check if x, y already exists to preserve layout
            row = conn.execute("SELECT x, y FROM graph_nodes WHERE id = ?", (node_id,)).fetchone()
            x = row["x"] if row else random.uniform(-100, 100)
            y = row["y"] if row else random.uniform(-100, 100)
            
            conn.execute(
                """
                INSERT OR REPLACE INTO graph_nodes (id, node_type, label, properties, x, y)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (node_id, node_type, label, json.dumps(properties), x, y)
            )
            conn.commit()
        finally:
            conn.close()
        return True

    def add_edge(self, edge_id: str, source: str, target: str, edge_type: str, properties: dict) -> bool:
        if edge_type not in self.VALID_EDGE_TYPES:
            raise ValueError(f"Invalid Edge Type: {edge_type}. Must be one of {self.VALID_EDGE_TYPES}")
            
        conn = self._get_connection()
        try:
            # Ensure source and target exist
            src_row = conn.execute("SELECT id FROM graph_nodes WHERE id = ?", (source,)).fetchone()
            tgt_row = conn.execute("SELECT id FROM graph_nodes WHERE id = ?", (target,)).fetchone()
            if not src_row or not tgt_row:
                raise ValueError("Both source and target nodes must exist before adding an edge.")

            conn.execute(
                """
                INSERT OR REPLACE INTO graph_edges (id, source, target, edge_type, properties)
                VALUES (?, ?, ?, ?, ?)
                """,
                (edge_id, source, target, edge_type, json.dumps(properties))
            )
            conn.commit()
        finally:
            conn.close()
        return True

    # ── Force-Directed Layout Computation ────────────────────────────────────

    def compute_force_directed_layout(self, iterations: int = 50, k_param: float = 80.0) -> Dict[str, Any]:
        """Runs a spring-embedder layout simulation on current nodes and edges."""
        conn = self._get_connection()
        try:
            node_rows = conn.execute("SELECT id, x, y FROM graph_nodes").fetchall()
            edge_rows = conn.execute("SELECT source, target FROM graph_edges").fetchall()
        finally:
            conn.close()

        if not node_rows:
            return {"nodes": [], "edges": []}

        # Convert to working dicts
        positions = {row["id"]: [row["x"], row["y"]] for row in node_rows}
        
        # Spring-embedder algorithm
        width = 800.0
        height = 600.0
        area = width * height
        k = k_param or math.sqrt(area / len(positions))
        
        for _ in range(iterations):
            disp = {node_id: [0.0, 0.0] for node_id in positions}
            
            # Repulsive forces between all node pairs
            node_ids = list(positions.keys())
            for i in range(len(node_ids)):
                node_a = node_ids[i]
                pos_a = positions[node_a]
                for j in range(i + 1, len(node_ids)):
                    node_b = node_ids[j]
                    pos_b = positions[node_b]
                    
                    dx = pos_a[0] - pos_b[0]
                    dy = pos_a[1] - pos_b[1]
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist == 0.0:
                        dist = 0.1
                        
                    # Repulsive force
                    fr = (k * k) / dist
                    disp[node_a][0] += (dx / dist) * fr
                    disp[node_a][1] += (dy / dist) * fr
                    disp[node_b][0] -= (dx / dist) * fr
                    disp[node_b][1] -= (dy / dist) * fr
            
            # Attractive forces along edges
            for edge in edge_rows:
                u = edge["source"]
                v = edge["target"]
                if u in positions and v in positions:
                    dx = positions[u][0] - positions[v][0]
                    dy = positions[u][1] - positions[v][1]
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist == 0.0:
                        dist = 0.1
                        
                    # Attractive force
                    fa = (dist * dist) / k
                    disp[u][0] -= (dx / dist) * fa
                    disp[u][1] -= (dy / dist) * fa
                    disp[v][0] += (dx / dist) * fa
                    disp[v][1] += (dy / dist) * fa

            # Update coordinates
            for node_id in positions:
                d = disp[node_id]
                dl = math.sqrt(d[0]*d[0] + d[1]*d[1])
                if dl > 0.0:
                    limit = min(dl, 20.0) # max displacement step
                    positions[node_id][0] += (d[0] / dl) * limit
                    positions[node_id][1] += (d[1] / dl) * limit
                    
                # Constrain within bounding frame
                positions[node_id][0] = max(-width/2, min(width/2, positions[node_id][0]))
                positions[node_id][1] = max(-height/2, min(height/2, positions[node_id][1]))

        # Write positions back to database
        conn = self._get_connection()
        try:
            for node_id, pos in positions.items():
                conn.execute("UPDATE graph_nodes SET x = ?, y = ? WHERE id = ?", (pos[0], pos[1], node_id))
            conn.commit()
        finally:
            conn.close()

        return self.get_graph_json()

    # ── Graph Expansion (k-hop traversal) ────────────────────────────────────

    def expand_graph(self, seed_node: str, hops: int = 1) -> Dict[str, Any]:
        """Returns a subgraph containing nodes and edges within `hops` distance of `seed_node`."""
        conn = self._get_connection()
        try:
            # Load adjacency list
            edges = conn.execute("SELECT id, source, target, edge_type, properties FROM graph_edges").fetchall()
            nodes = conn.execute("SELECT id, node_type, label, properties, x, y FROM graph_nodes").fetchall()
        finally:
            conn.close()

        # Build map
        adj: Dict[str, List[Tuple[str, dict]]] = {}
        for edge in edges:
            s = edge["source"]
            t = edge["target"]
            if s not in adj: adj[s] = []
            if t not in adj: adj[t] = []
            adj[s].append((t, edge))
            adj[t].append((s, edge))

        # BFS expansion
        visited: Set[str] = {seed_node}
        queue: List[Tuple[str, int]] = [(seed_node, 0)]
        matched_edges: Set[str] = set()

        while queue:
            curr, curr_hop = queue.pop(0)
            if curr_hop < hops:
                for neighbor, edge in adj.get(curr, []):
                    matched_edges.add(edge["id"])
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, curr_hop + 1))

        # Build output objects
        node_map = {n["id"]: n for n in nodes}
        out_nodes = []
        for n_id in visited:
            if n_id in node_map:
                row = node_map[n_id]
                out_nodes.append({
                    "id": row["id"],
                    "type": row["node_type"],
                    "label": row["label"],
                    "x": row["x"],
                    "y": row["y"],
                    "properties": json.loads(row["properties"] or "{}")
                })

        out_edges = []
        for edge in edges:
            if edge["id"] in matched_edges:
                out_edges.append({
                    "id": edge["id"],
                    "source": edge["source"],
                    "target": edge["target"],
                    "type": edge["edge_type"],
                    "properties": json.loads(edge["properties"] or "{}")
                })

        return {"nodes": out_nodes, "edges": out_edges}

    # ── Investigation History Snapshotting ───────────────────────────────────

    def save_snapshot(self, action_name: str) -> str:
        """Saves current state snapshot of nodes and edges into investigation history."""
        graph_data = self.get_graph_json()
        import uuid
        from datetime import datetime, timezone
        snap_id = f"SNAP-{str(uuid.uuid4())[:8].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat() + "Z"

        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO investigation_history (id, timestamp, action, snapshot)
                VALUES (?, ?, ?, ?)
                """,
                (snap_id, timestamp, action_name, json.dumps(graph_data))
            )
            conn.commit()
        finally:
            conn.close()
        return snap_id

    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieve investigation snapshots."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT id, timestamp, action, snapshot FROM investigation_history ORDER BY timestamp ASC").fetchall()
            history = []
            for r in rows:
                history.append({
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "action": r["action"],
                    "snapshot": json.loads(r["snapshot"])
                })
            return history
        finally:
            conn.close()

    # ── Timeline Reconstruction ──────────────────────────────────────────────

    def reconstruct_timeline(self) -> List[Dict[str, Any]]:
        """Collects all edge events containing a timestamp and returns sorted timeline."""
        conn = self._get_connection()
        try:
            edges = conn.execute("SELECT source, target, edge_type, properties FROM graph_edges").fetchall()
        finally:
            conn.close()

        timeline = []
        for edge in edges:
            props = json.loads(edge["properties"] or "{}")
            timestamp = props.get("timestamp")
            if timestamp:
                timeline.append({
                    "timestamp": timestamp,
                    "event_type": edge["edge_type"],
                    "source": edge["source"],
                    "target": edge["target"],
                    "description": props.get("description", f"{edge['source']} {edge['edge_type']} {edge['target']}"),
                    "amount": props.get("amount"),
                    "currency": props.get("currency")
                })

        # Sort timeline chronologically
        return sorted(timeline, key=lambda x: x["timestamp"])

    # ── Helper ───────────────────────────────────────────────────────────────

    def get_graph_json(self) -> Dict[str, Any]:
        """Return entire graph nodes and edges as JSON."""
        conn = self._get_connection()
        try:
            nodes = conn.execute("SELECT * FROM graph_nodes").fetchall()
            edges = conn.execute("SELECT * FROM graph_edges").fetchall()
        finally:
            conn.close()

        out_nodes = []
        for n in nodes:
            out_nodes.append({
                "id": n["id"],
                "type": n["node_type"],
                "label": n["label"],
                "x": n["x"],
                "y": n["y"],
                "properties": json.loads(n["properties"] or "{}")
            })

        out_edges = []
        for e in edges:
            out_edges.append({
                "id": e["id"],
                "source": e["source"],
                "target": e["target"],
                "type": e["edge_type"],
                "properties": json.loads(e["properties"] or "{}")
            })

        return {"nodes": out_nodes, "edges": out_edges}
