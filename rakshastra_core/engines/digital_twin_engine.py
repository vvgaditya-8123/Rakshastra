#!/usr/bin/env python3
"""Cyber Resilience Digital Twin Engine (Point 5).

Provides a virtual graph-based simulation model of target infrastructure:
  - Infrastructure Graph Topology (Hosts, SCADA, Cloud Services, DBs, Firewalls, IAM Roles)
  - Red-Team Cyber Attack Simulations (Ransomware, APT Lateral Movement, Zero-Day Cascade, Exfiltration)
  - Simulated Blast Radius & Probability of Compromise (PoC)
  - What-If Defensive Intervention Validation (Micro-segmentation, MFA, Isolation)
  - Quantitative Resilience Score (0 - 100) before & after counter-measures
"""

import json
import logging
import math
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Predefined Attack Templates
ATTACK_TEMPLATES = {
    "RANSOMWARE_CASCADE": {
        "name": "Ransomware Lateral Propagation & Encryption Cascade",
        "description": "Simulates worm-like ransomware (e.g. NotPetya, WannaCry) spreading via SMB/WinRM and encrypting network shares.",
        "initial_vector": "PHISHING_PAYLOAD",
        "target_node_types": ["HOST", "FILE_SERVER", "DATABASE"],
        "propagation_probability": 0.85,
        "base_severity": "CRITICAL",
    },
    "APT_LATERAL_MOVEMENT": {
        "name": "APT Nation-State Stealth Lateral Movement",
        "description": "Simulates stealthy APT privilege escalation, Kerberoasting, and domain controller takeover.",
        "initial_vector": "COMPROMISED_CREDENTIALS",
        "target_node_types": ["DOMAIN_CONTROLLER", "IAM_ROLE", "DATABASE"],
        "propagation_probability": 0.65,
        "base_severity": "HIGH",
    },
    "ZERO_DAY_CASCADE": {
        "name": "Unpatched Zero-Day Remote Code Execution Cascade",
        "description": "Simulates zero-day RCE on edge firewalls/VPN gateways expanding into internal DMZ and core subnets.",
        "initial_vector": "VPN_EXPLOIT",
        "target_node_types": ["FIREWALL", "ROUTER", "APPLICATION_SERVER"],
        "propagation_probability": 0.90,
        "base_severity": "CRITICAL",
    },
    "DATA_EXFILTRATION": {
        "name": "Insider / Compromised Service Data Exfiltration",
        "description": "Simulates unauthorized exfiltration of sensitive DB records via encrypted DNS/HTTPS tunnels.",
        "initial_vector": "INSIDER_THREAT",
        "target_node_types": ["DATABASE", "CLOUD_STORAGE"],
        "propagation_probability": 0.70,
        "base_severity": "HIGH",
    },
}


class DigitalTwinEngine:
    """Graph AI & Simulation Engine for Cyber Resilience Digital Twin."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            from rakshastra_constants import get_rakshastra_home
            self.db_path = get_rakshastra_home() / "digital_twin.db"
        else:
            self.db_path = Path(db_path)

        self._persistent_conn: Optional[sqlite3.Connection] = None
        if str(self.db_path) == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._persistent_conn.row_factory = sqlite3.Row

        self._init_db()
        self._seed_default_templates()

    def _conn(self) -> sqlite3.Connection:
        if self._persistent_conn is not None:
            return self._persistent_conn
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _close_conn(self, conn: sqlite3.Connection) -> None:
        if self._persistent_conn is None:
            conn.close()

    def _init_db(self) -> None:
        conn = self._conn()
        try:
            cur = conn.cursor()
            # Topology Nodes table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dt_nodes (
                    node_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    department TEXT NOT NULL,
                    ip_address TEXT,
                    security_controls TEXT, -- JSON array (e.g. ["MFA", "EDR", "WAF"])
                    vulnerability_count INTEGER DEFAULT 0,
                    criticality_weight REAL DEFAULT 1.0,
                    is_compromised BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Topology Edges (Network / Trust connections) table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dt_edges (
                    edge_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    protocol TEXT NOT NULL,
                    port INTEGER,
                    trust_level REAL DEFAULT 0.5, -- 0.0 (untrusted) to 1.0 (fully trusted)
                    is_blocked BOOLEAN DEFAULT 0,
                    FOREIGN KEY(source_id) REFERENCES dt_nodes(node_id),
                    FOREIGN KEY(target_id) REFERENCES dt_nodes(node_id)
                )
            """)

            # Attack Simulations table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dt_simulations (
                    sim_id TEXT PRIMARY KEY,
                    scenario_type TEXT NOT NULL,
                    scenario_name TEXT NOT NULL,
                    entry_node_id TEXT NOT NULL,
                    compromised_nodes TEXT NOT NULL, -- JSON array of node_ids
                    affected_count INTEGER NOT NULL,
                    total_nodes INTEGER NOT NULL,
                    blast_radius_pct REAL NOT NULL,
                    probability_of_compromise REAL NOT NULL,
                    resilience_score_before REAL NOT NULL,
                    resilience_score_after REAL,
                    applied_defenses TEXT, -- JSON array of applied what-if controls
                    created_at TEXT NOT NULL
                )
            """)

            conn.commit()
        finally:
            self._close_conn(conn)

    def _seed_default_templates(self) -> None:
        """Seed sample network topology if table is empty."""
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM dt_nodes")
            if cur.fetchone()[0] == 0:
                sample_nodes = [
                    ("NODE-FW-01", "Edge Perimeter Firewall", "FIREWALL", "INFRA", "103.14.10.1", '["WAF"]', 1, 2.0),
                    ("NODE-DMZ-WEB", "DMZ Public Web Server", "HOST", "NIC", "10.0.1.10", '["EDR"]', 3, 1.5),
                    ("NODE-APP-01", "Core Application Middleware", "HOST", "NIC", "10.0.2.20", '["EDR", "MFA"]', 2, 1.8),
                    ("NODE-DB-PRIMARY", "Primary Citizen Database", "DATABASE", "NIC", "10.0.3.50", '["ENCRYPTION", "EDR"]', 1, 2.5),
                    ("NODE-DC-01", "Active Directory Domain Controller", "DOMAIN_CONTROLLER", "INFRA", "10.0.2.5", '["MFA", "AUDIT"]', 2, 3.0),
                    ("NODE-WORKSTATION-42", "Finance Admin Workstation", "WORKSTATION", "FINANCE", "10.0.4.100", '["ANTIVIRUS"]', 4, 1.0),
                ]
                cur.executemany("""
                    INSERT INTO dt_nodes (node_id, name, node_type, department, ip_address, security_controls, vulnerability_count, criticality_weight, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, sample_nodes)

                sample_edges = [
                    ("EDGE-01", "NODE-FW-01", "NODE-DMZ-WEB", "HTTPS", 443, 0.3),
                    ("EDGE-02", "NODE-DMZ-WEB", "NODE-APP-01", "CUSTOM_API", 8080, 0.6),
                    ("EDGE-03", "NODE-APP-01", "NODE-DB-PRIMARY", "POSTGRESQL", 5432, 0.8),
                    ("EDGE-04", "NODE-WORKSTATION-42", "NODE-APP-01", "HTTPS", 443, 0.5),
                    ("EDGE-05", "NODE-WORKSTATION-42", "NODE-DC-01", "KERBEROS", 88, 0.9),
                    ("EDGE-06", "NODE-APP-01", "NODE-DC-01", "LDAP", 389, 0.7),
                ]
                cur.executemany("""
                    INSERT INTO dt_edges (edge_id, source_id, target_id, protocol, port, trust_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, sample_edges)

                conn.commit()
        finally:
            self._close_conn(conn)

    # =========================================================================
    # Topology Management API
    # =========================================================================

    def add_node(
        self,
        name: str,
        node_type: str = "HOST",
        department: str = "IT",
        ip_address: str = "",
        security_controls: Optional[List[str]] = None,
        vulnerability_count: int = 0,
        criticality_weight: float = 1.0,
        node_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a node to the digital twin graph topology."""
        if not node_id:
            node_id = f"NODE-{uuid.uuid4().hex[:8].upper()}"

        controls = json.dumps(security_controls or [])
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dt_nodes (node_id, name, node_type, department, ip_address, security_controls, vulnerability_count, criticality_weight, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (node_id, name, node_type.upper(), department, ip_address, controls, vulnerability_count, criticality_weight))
            conn.commit()
            return {
                "node_id": node_id,
                "name": name,
                "node_type": node_type.upper(),
                "department": department,
                "ip_address": ip_address,
                "security_controls": security_controls or [],
                "vulnerability_count": vulnerability_count,
                "criticality_weight": criticality_weight,
            }
        finally:
            self._close_conn(conn)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        protocol: str = "TCP",
        port: Optional[int] = None,
        trust_level: float = 0.5,
        edge_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a network/trust edge between topology nodes."""
        if not edge_id:
            edge_id = f"EDGE-{uuid.uuid4().hex[:8].upper()}"

        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dt_edges (edge_id, source_id, target_id, protocol, port, trust_level)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (edge_id, source_id, target_id, protocol, port, trust_level))
            conn.commit()
            return {
                "edge_id": edge_id,
                "source_id": source_id,
                "target_id": target_id,
                "protocol": protocol,
                "port": port,
                "trust_level": trust_level,
            }
        finally:
            self._close_conn(conn)

    def get_topology(self) -> Dict[str, Any]:
        """Retrieve full digital twin network graph topology."""
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM dt_nodes")
            nodes = []
            for row in cur.fetchall():
                nodes.append({
                    "node_id": row["node_id"],
                    "name": row["name"],
                    "node_type": row["node_type"],
                    "department": row["department"],
                    "ip_address": row["ip_address"],
                    "security_controls": json.loads(row["security_controls"] or "[]"),
                    "vulnerability_count": row["vulnerability_count"],
                    "criticality_weight": row["criticality_weight"],
                    "is_compromised": bool(row["is_compromised"]),
                })

            cur.execute("SELECT * FROM dt_edges")
            edges = []
            for row in cur.fetchall():
                edges.append({
                    "edge_id": row["edge_id"],
                    "source_id": row["source_id"],
                    "target_id": row["target_id"],
                    "protocol": row["protocol"],
                    "port": row["port"],
                    "trust_level": row["trust_level"],
                    "is_blocked": bool(row["is_blocked"]),
                })

            return {
                "nodes_count": len(nodes),
                "edges_count": len(edges),
                "nodes": nodes,
                "edges": edges,
            }
        finally:
            self._close_conn(conn)

    # =========================================================================
    # Cyber Attack Scenario Simulation & Blast Radius Engine
    # =========================================================================

    def list_attack_templates(self) -> List[Dict[str, Any]]:
        """List available Red-Team cyber attack simulation scenario templates."""
        return [{"scenario_key": key, **value} for key, value in ATTACK_TEMPLATES.items()]

    def simulate_attack(
        self,
        scenario_key: str,
        entry_node_id: str,
    ) -> Dict[str, Any]:
        """Simulate a red-team cyber attack starting at entry_node_id across the digital twin graph."""
        scenario = ATTACK_TEMPLATES.get(scenario_key.upper())
        if not scenario:
            scenario = {
                "name": f"Custom Attack Scenario ({scenario_key})",
                "description": "Custom simulated attack path analysis.",
                "propagation_probability": 0.75,
                "base_severity": "HIGH",
            }

        topology = self.get_topology()
        nodes_dict = {n["node_id"]: n for n in topology["nodes"]}
        if entry_node_id not in nodes_dict:
            return {"error": f"Entry node '{entry_node_id}' not found in Digital Twin topology."}

        # Build adjacency graph
        adj: Dict[str, List[Tuple[str, float]]] = {n: [] for n in nodes_dict}
        for edge in topology["edges"]:
            if not edge["is_blocked"]:
                adj[edge["source_id"]].append((edge["target_id"], edge["trust_level"]))
                # Bidirectional connectivity for network propagation
                adj[edge["target_id"]].append((edge["source_id"], edge["trust_level"]))

        # Graph BFS / Propagation simulation
        compromised: Set[str] = {entry_node_id}
        queue = [entry_node_id]
        propagation_probs: Dict[str, float] = {entry_node_id: 1.0}

        base_prob = scenario.get("propagation_probability", 0.75)

        while queue:
            curr = queue.pop(0)
            curr_prob = propagation_probs[curr]

            for neighbor, trust in adj.get(curr, []):
                if neighbor not in compromised:
                    neighbor_node = nodes_dict[neighbor]
                    controls = neighbor_node.get("security_controls", [])

                    # Security controls mitigation factor
                    control_mitigation = 1.0
                    if "MFA" in controls:
                        control_mitigation *= 0.5
                    if "EDR" in controls:
                        control_mitigation *= 0.6
                    if "MICROSEGMENTATION" in controls:
                        control_mitigation *= 0.3
                    if "WAF" in controls and neighbor_node["node_type"] == "FIREWALL":
                        control_mitigation *= 0.4

                    # Risk factor increase by vulnerability count
                    vuln_factor = 1.0 + (neighbor_node.get("vulnerability_count", 0) * 0.15)

                    prob = curr_prob * base_prob * trust * control_mitigation * vuln_factor
                    prob = min(0.99, max(0.05, prob))

                    if prob >= 0.35:  # Infection threshold
                        compromised.add(neighbor)
                        propagation_probs[neighbor] = round(prob, 3)
                        queue.append(neighbor)

        total_nodes = len(nodes_dict)
        affected_count = len(compromised)
        blast_radius_pct = round((affected_count / total_nodes) * 100.0, 2) if total_nodes > 0 else 0.0

        # Weighted Probability of Compromise (PoC)
        weighted_comp_sum = sum(nodes_dict[n]["criticality_weight"] * propagation_probs.get(n, 1.0) for n in compromised)
        total_weight_sum = sum(n["criticality_weight"] for n in nodes_dict.values())
        poc_score = round(weighted_comp_sum / total_weight_sum, 3) if total_weight_sum > 0 else 0.0

        # Resilience score calculation (0 - 100)
        # Higher blast radius & higher PoC lowers resilience score
        resilience_score = max(0.0, round(100.0 - (blast_radius_pct * 0.6 + poc_score * 40.0), 2))

        sim_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        sim_record = {
            "sim_id": sim_id,
            "scenario_type": scenario_key,
            "scenario_name": scenario["name"],
            "entry_node_id": entry_node_id,
            "compromised_nodes": list(compromised),
            "affected_count": affected_count,
            "total_nodes": total_nodes,
            "blast_radius_pct": blast_radius_pct,
            "probability_of_compromise": poc_score,
            "resilience_score_before": resilience_score,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save simulation record
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dt_simulations (
                    sim_id, scenario_type, scenario_name, entry_node_id, compromised_nodes,
                    affected_count, total_nodes, blast_radius_pct, probability_of_compromise,
                    resilience_score_before, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sim_id, scenario_key, scenario["name"], entry_node_id,
                json.dumps(list(compromised)), affected_count, total_nodes,
                blast_radius_pct, poc_score, resilience_score, sim_record["created_at"]
            ))
            conn.commit()
        finally:
            self._close_conn(conn)

        # Highlighting compromised critical assets
        compromised_assets_detail = [
            {
                "node_id": nid,
                "name": nodes_dict[nid]["name"],
                "node_type": nodes_dict[nid]["node_type"],
                "department": nodes_dict[nid]["department"],
                "infection_probability": propagation_probs.get(nid, 1.0),
            }
            for nid in compromised
        ]

        return {
            "sim_id": sim_id,
            "scenario": scenario["name"],
            "entry_node": nodes_dict[entry_node_id]["name"],
            "total_network_nodes": total_nodes,
            "compromised_nodes_count": affected_count,
            "blast_radius_pct": blast_radius_pct,
            "probability_of_compromise": poc_score,
            "resilience_score": resilience_score,
            "compromised_assets": compromised_assets_detail,
        }

    # =========================================================================
    # What-If Defensive Intervention Validation
    # =========================================================================

    def apply_defense_whatif(
        self,
        sim_id: str,
        defense_actions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Apply virtual What-If security controls to validate resilience score improvement.

        defense_actions example:
          [
            {"action_type": "MICROSEGMENTATION", "source_id": "NODE-DMZ-WEB", "target_id": "NODE-APP-01"},
            {"action_type": "ENFORCE_MFA", "node_id": "NODE-DC-01"},
            {"action_type": "ISOLATE_NODE", "node_id": "NODE-WORKSTATION-42"}
          ]
        """
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM dt_simulations WHERE sim_id = ?", (sim_id,))
            sim_row = cur.fetchone()
            if not sim_row:
                return {"error": f"Simulation record '{sim_id}' not found."}

            scenario_key = sim_row["scenario_type"]
            entry_node_id = sim_row["entry_node_id"]
            resilience_before = sim_row["resilience_score_before"]

            # Perform temporary in-memory modifications based on defense_actions
            topology = self.get_topology()
            nodes_dict = {n["node_id"]: n for n in topology["nodes"]}

            blocked_edges = set()
            for action in defense_actions:
                atype = action.get("action_type", "").upper()
                if atype == "MICROSEGMENTATION" or atype == "BLOCK_EDGE":
                    src = action.get("source_id")
                    tgt = action.get("target_id")
                    for e in topology["edges"]:
                        if (e["source_id"] == src and e["target_id"] == tgt) or (e["source_id"] == tgt and e["target_id"] == src):
                            blocked_edges.add(e["edge_id"])
                elif atype == "ISOLATE_NODE":
                    nid = action.get("node_id")
                    for e in topology["edges"]:
                        if e["source_id"] == nid or e["target_id"] == nid:
                            blocked_edges.add(e["edge_id"])
                elif atype == "ENFORCE_MFA" or atype == "ADD_CONTROL":
                    nid = action.get("node_id")
                    if nid in nodes_dict:
                        ctrls = set(nodes_dict[nid].get("security_controls", []))
                        ctrls.add(action.get("control", "MFA"))
                        nodes_dict[nid]["security_controls"] = list(ctrls)

            # Re-run simulation with modified virtual topology
            scenario = ATTACK_TEMPLATES.get(scenario_key.upper(), {})
            base_prob = scenario.get("propagation_probability", 0.75)

            adj: Dict[str, List[Tuple[str, float]]] = {n: [] for n in nodes_dict}
            for edge in topology["edges"]:
                if not edge["is_blocked"] and edge["edge_id"] not in blocked_edges:
                    adj[edge["source_id"]].append((edge["target_id"], edge["trust_level"]))
                    adj[edge["target_id"]].append((edge["source_id"], edge["trust_level"]))

            compromised: Set[str] = {entry_node_id}
            queue = [entry_node_id]
            propagation_probs: Dict[str, float] = {entry_node_id: 1.0}

            while queue:
                curr = queue.pop(0)
                curr_prob = propagation_probs[curr]

                for neighbor, trust in adj.get(curr, []):
                    if neighbor not in compromised:
                        neighbor_node = nodes_dict[neighbor]
                        controls = neighbor_node.get("security_controls", [])

                        control_mitigation = 1.0
                        if "MFA" in controls:
                            control_mitigation *= 0.5
                        if "EDR" in controls:
                            control_mitigation *= 0.6
                        if "MICROSEGMENTATION" in controls:
                            control_mitigation *= 0.3
                        if "WAF" in controls and neighbor_node["node_type"] == "FIREWALL":
                            control_mitigation *= 0.4

                        vuln_factor = 1.0 + (neighbor_node.get("vulnerability_count", 0) * 0.15)
                        prob = curr_prob * base_prob * trust * control_mitigation * vuln_factor
                        prob = min(0.99, max(0.05, prob))

                        if prob >= 0.35:
                            compromised.add(neighbor)
                            propagation_probs[neighbor] = round(prob, 3)
                            queue.append(neighbor)

            total_nodes = len(nodes_dict)
            affected_count = len(compromised)
            blast_radius_pct = round((affected_count / total_nodes) * 100.0, 2) if total_nodes > 0 else 0.0

            weighted_comp_sum = sum(nodes_dict[n]["criticality_weight"] * propagation_probs.get(n, 1.0) for n in compromised)
            total_weight_sum = sum(n["criticality_weight"] for n in nodes_dict.values())
            poc_score = round(weighted_comp_sum / total_weight_sum, 3) if total_weight_sum > 0 else 0.0

            resilience_after = max(0.0, round(100.0 - (blast_radius_pct * 0.6 + poc_score * 40.0), 2))
            resilience_gain = round(resilience_after - resilience_before, 2)

            # Update DB simulation row
            cur.execute("""
                UPDATE dt_simulations
                SET resilience_score_after = ?, applied_defenses = ?
                WHERE sim_id = ?
            """, (resilience_after, json.dumps(defense_actions), sim_id))
            conn.commit()

            return {
                "sim_id": sim_id,
                "scenario": sim_row["scenario_name"],
                "defense_actions_applied": len(defense_actions),
                "compromised_before": sim_row["affected_count"],
                "compromised_after": affected_count,
                "blast_radius_before_pct": sim_row["blast_radius_pct"],
                "blast_radius_after_pct": blast_radius_pct,
                "resilience_score_before": resilience_before,
                "resilience_score_after": resilience_after,
                "resilience_gain": resilience_gain,
                "is_effective": resilience_gain > 0,
            }
        finally:
            self._close_conn(conn)

    # =========================================================================
    # Summary Dashboard
    # =========================================================================

    def get_summary(self) -> Dict[str, Any]:
        """Aggregate digital twin summary metrics."""
        topology = self.get_topology()
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM dt_simulations")
            sim_count = cur.fetchone()[0]

            cur.execute("SELECT AVG(resilience_score_before), AVG(resilience_score_after) FROM dt_simulations")
            avg_row = cur.fetchone()
            avg_before = round(avg_row[0] or 0.0, 2)
            avg_after = round(avg_row[1] or avg_before, 2)

            return {
                "digital_twin_nodes": topology["nodes_count"],
                "digital_twin_edges": topology["edges_count"],
                "total_simulations_run": sim_count,
                "avg_resilience_before_defenses": avg_before,
                "avg_resilience_after_defenses": avg_after,
                "resilience_score": avg_after,
            }
        finally:
            self._close_conn(conn)
