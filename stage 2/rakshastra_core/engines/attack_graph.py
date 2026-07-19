"""Attack Graph Engine — Graph AI for Attack Path Analysis.

Wraps InfrastructureGraph with attack path computation, lateral movement
detection, blast radius simulation, and chokepoint identification.
"""

import json
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

from rakshastra_core.engines.infrastructure_graph import InfrastructureGraph
from rakshastra_core.models import Asset, AssetRelation


class AttackGraphEngine:
    """Graph-based attack path analysis and lateral movement detection."""

    def __init__(self, infra_graph: InfrastructureGraph):
        self.graph = infra_graph

    def compute_attack_paths(
        self,
        entry_point_id: str,
        target_id: str,
        max_depth: int = 8,
    ) -> Dict[str, Any]:
        """Find all attack paths from entry_point to target using BFS.

        Returns paths ranked by difficulty (lower = easier to exploit).
        """
        conn = self.graph._get_connection()
        try:
            # Build adjacency from relations
            rel_rows = conn.execute("SELECT * FROM relations").fetchall()
            adj: Dict[str, List[Tuple[str, Dict]]] = {}
            for r in rel_rows:
                src = r["source_id"]
                tgt = r["target_id"]
                rel = {"id": r["id"], "type": r["relation_type"], "props": json.loads(r["properties"] or "{}")}
                adj.setdefault(src, []).append((tgt, rel))
                adj.setdefault(tgt, []).append((src, rel))  # Bidirectional
        finally:
            conn.close()

        # BFS to find all paths (limited by depth)
        all_paths: List[List[str]] = []
        queue: deque = deque([(entry_point_id, [entry_point_id])])
        visited_paths: Set[str] = set()

        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue

            if current == target_id and len(path) > 1:
                path_key = "->".join(path)
                if path_key not in visited_paths:
                    visited_paths.add(path_key)
                    all_paths.append(list(path))
                continue

            for neighbor, rel in adj.get(current, []):
                if neighbor not in path:  # Avoid cycles
                    queue.append((neighbor, path + [neighbor]))

        # Score and enrich paths
        scored_paths = []
        for path in all_paths:
            score = self._score_path(path)
            enriched_nodes = []
            for node_id in path:
                asset = self.graph.get_asset(node_id)
                enriched_nodes.append({
                    "id": node_id,
                    "name": asset.name if asset else node_id,
                    "type": asset.asset_type.value if asset else "unknown",
                })
            scored_paths.append({
                "path": enriched_nodes,
                "hop_count": len(path) - 1,
                "difficulty_score": score,
                "path_ids": path,
            })

        # Sort by difficulty (easiest first)
        scored_paths.sort(key=lambda x: x["difficulty_score"])

        return {
            "entry_point": entry_point_id,
            "target": target_id,
            "total_paths_found": len(scored_paths),
            "attack_paths": scored_paths[:20],  # Top 20
            "shortest_path_hops": min((p["hop_count"] for p in scored_paths), default=0),
            "easiest_path_score": scored_paths[0]["difficulty_score"] if scored_paths else None,
        }

    def simulate_blast_radius(self, compromised_asset_id: str) -> Dict[str, Any]:
        """Simulate the blast radius assuming an asset is fully compromised.

        Returns all reachable assets with their distance from the compromised asset.
        """
        visited: Dict[str, int] = {compromised_asset_id: 0}
        queue: deque = deque([(compromised_asset_id, 0)])
        affected_assets: List[Dict[str, Any]] = []

        conn = self.graph._get_connection()
        try:
            while queue:
                current, depth = queue.popleft()
                # Get downstream neighbors
                rows = conn.execute(
                    "SELECT target_id, relation_type FROM relations WHERE source_id = ?",
                    (current,),
                ).fetchall()
                for row in rows:
                    neighbor = row["target_id"]
                    if neighbor not in visited:
                        visited[neighbor] = depth + 1
                        queue.append((neighbor, depth + 1))

                # Also check reverse relations (bidirectional attack surface)
                rows2 = conn.execute(
                    "SELECT source_id, relation_type FROM relations WHERE target_id = ?",
                    (current,),
                ).fetchall()
                for row in rows2:
                    neighbor = row["source_id"]
                    if neighbor not in visited:
                        visited[neighbor] = depth + 1
                        queue.append((neighbor, depth + 1))
        finally:
            conn.close()

        # Enrich with asset details
        for asset_id, distance in visited.items():
            if asset_id == compromised_asset_id:
                continue
            asset = self.graph.get_asset(asset_id)
            affected_assets.append({
                "id": asset_id,
                "name": asset.name if asset else asset_id,
                "type": asset.asset_type.value if asset else "unknown",
                "distance": distance,
                "criticality": (asset.properties.get("criticality", "medium") if asset else "unknown"),
            })

        # Sort by distance then criticality
        crit_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        affected_assets.sort(key=lambda x: (x["distance"], crit_order.get(x["criticality"], 4)))

        # Compute summary
        compromised_asset = self.graph.get_asset(compromised_asset_id)
        return {
            "compromised_asset": {
                "id": compromised_asset_id,
                "name": compromised_asset.name if compromised_asset else compromised_asset_id,
                "type": compromised_asset.asset_type.value if compromised_asset else "unknown",
            },
            "total_affected": len(affected_assets),
            "affected_assets": affected_assets,
            "max_distance": max((a["distance"] for a in affected_assets), default=0),
            "critical_assets_affected": sum(1 for a in affected_assets if a["criticality"] in ("critical", "high")),
        }

    def detect_lateral_movement(
        self, anomaly_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Correlate anomalies across connected hosts to detect lateral movement chains.

        Looks for anomaly events on connected assets that indicate movement
        from one host to another.
        """
        # Group anomalies by entity
        entity_anomalies: Dict[str, List[Dict]] = {}
        for event in anomaly_events:
            eid = event.get("entity_id", "")
            entity_anomalies.setdefault(eid, []).append(event)

        # Find connected pairs
        lateral_chains: List[Dict[str, Any]] = []
        seen_pairs: Set[str] = set()

        entities = list(entity_anomalies.keys())
        for i, entity_a in enumerate(entities):
            for entity_b in entities[i + 1:]:
                pair_key = f"{entity_a}<->{entity_b}"
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Check if entities are connected in the infrastructure graph
                neighbors = self.graph.neighbors(entity_a, depth=2)
                neighbor_ids = set(neighbors.get("assets", {}).keys())

                if entity_b in neighbor_ids:
                    # Check for temporal correlation (both have anomalies)
                    a_categories = {e.get("category") for e in entity_anomalies[entity_a]}
                    b_categories = {e.get("category") for e in entity_anomalies[entity_b]}

                    # Lateral movement indicators
                    lateral_indicators = {
                        "LATERAL_MOVEMENT", "LOGIN_LOCATION", "PRIVILEGE_ESCALATION",
                        "COMMAND_ANOMALY", "PROCESS_ANOMALY"
                    }
                    a_lateral = a_categories & lateral_indicators
                    b_lateral = b_categories & lateral_indicators

                    if a_lateral or b_lateral:
                        chain_confidence = min(
                            0.3 + (len(a_lateral) + len(b_lateral)) * 0.15,
                            1.0
                        )
                        lateral_chains.append({
                            "source_entity": entity_a,
                            "target_entity": entity_b,
                            "confidence": round(chain_confidence, 3),
                            "source_anomaly_categories": sorted(a_categories),
                            "target_anomaly_categories": sorted(b_categories),
                            "source_anomaly_count": len(entity_anomalies[entity_a]),
                            "target_anomaly_count": len(entity_anomalies[entity_b]),
                        })

        lateral_chains.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "lateral_movement_detected": len(lateral_chains) > 0,
            "chains": lateral_chains,
            "total_entities_analyzed": len(entities),
            "connected_pairs_found": len(lateral_chains),
        }

    def find_chokepoints(self) -> List[Dict[str, Any]]:
        """Identify critical network nodes (articulation points).

        These are nodes whose removal would disconnect parts of the network,
        making them critical for both attack and defense.
        """
        conn = self.graph._get_connection()
        try:
            nodes = [r["id"] for r in conn.execute("SELECT id FROM assets").fetchall()]
            edges = conn.execute("SELECT source_id, target_id FROM relations").fetchall()
        finally:
            conn.close()

        if not nodes:
            return []

        # Build adjacency
        adj: Dict[str, Set[str]] = {n: set() for n in nodes}
        for e in edges:
            adj.setdefault(e["source_id"], set()).add(e["target_id"])
            adj.setdefault(e["target_id"], set()).add(e["source_id"])

        # Find articulation points using DFS
        visited: Set[str] = set()
        disc: Dict[str, int] = {}
        low: Dict[str, int] = {}
        parent: Dict[str, Optional[str]] = {}
        ap: Set[str] = set()
        timer = [0]

        def dfs(u: str):
            children = 0
            visited.add(u)
            disc[u] = low[u] = timer[0]
            timer[0] += 1

            for v in adj.get(u, set()):
                if v not in visited:
                    children += 1
                    parent[v] = u
                    dfs(v)
                    low[u] = min(low[u], low[v])

                    # u is an articulation point if:
                    # 1. u is root with 2+ children
                    if parent.get(u) is None and children > 1:
                        ap.add(u)
                    # 2. u is not root and low[v] >= disc[u]
                    if parent.get(u) is not None and low[v] >= disc[u]:
                        ap.add(u)
                elif v != parent.get(u):
                    low[u] = min(low[u], disc[v])

        for node in nodes:
            if node not in visited:
                parent[node] = None
                dfs(node)

        # Enrich chokepoints
        chokepoints = []
        for node_id in ap:
            asset = self.graph.get_asset(node_id)
            connections = len(adj.get(node_id, set()))
            chokepoints.append({
                "id": node_id,
                "name": asset.name if asset else node_id,
                "type": asset.asset_type.value if asset else "unknown",
                "connections": connections,
                "criticality": asset.properties.get("criticality", "medium") if asset else "unknown",
                "defensive_recommendation": f"Harden {asset.name if asset else node_id}: this is a critical chokepoint with {connections} connections.",
            })

        chokepoints.sort(key=lambda x: x["connections"], reverse=True)
        return chokepoints

    def _score_path(self, path: List[str]) -> float:
        """Score an attack path by difficulty (lower = easier to exploit)."""
        if len(path) <= 1:
            return 0.0

        score = 0.0
        for node_id in path:
            asset = self.graph.get_asset(node_id)
            if not asset:
                score += 0.5
                continue

            # More secure assets add more difficulty
            crit = asset.properties.get("criticality", "medium").lower()
            if crit == "critical":
                score += 0.3  # Harder to move through critical assets
            elif crit == "high":
                score += 0.2
            elif crit == "medium":
                score += 0.1
            else:
                score += 0.05  # Easy target

            # Check for security controls
            if asset.properties.get("mfa_enabled"):
                score += 0.3
            if asset.properties.get("edr_deployed"):
                score += 0.2
            if asset.properties.get("segmented"):
                score += 0.25

        return round(score, 3)

    def generate_attack_path_mermaid(self, paths_result: Dict[str, Any]) -> str:
        """Generate a Mermaid diagram of attack paths."""
        lines = ["graph LR"]
        seen_nodes = set()
        seen_edges = set()

        for i, path_data in enumerate(paths_result.get("attack_paths", [])[:5]):
            path_nodes = path_data.get("path", [])
            for j, node in enumerate(path_nodes):
                nid = node["id"].replace("-", "")[:12]
                if nid not in seen_nodes:
                    seen_nodes.add(nid)
                    label = f'{node["name"]} ({node["type"]})'
                    lines.append(f'    {nid}["{label}"]')

                if j > 0:
                    prev_nid = path_nodes[j - 1]["id"].replace("-", "")[:12]
                    edge_key = f"{prev_nid}->{nid}"
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        lines.append(f"    {prev_nid} -->|path {i+1}| {nid}")

        return "\n".join(lines)
