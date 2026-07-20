#!/usr/bin/env python3
"""E2E Test Script for Point 5: Cyber Resilience Digital Twin Engine.

Tests:
  1. Digital Twin Topology Initialization & Graph Queries
  2. Red-Team Ransomware Cascade Attack Simulation
  3. Red-Team APT Stealth Lateral Movement Simulation
  4. What-If Defensive Intervention Validation (Micro-segmentation, MFA)
  5. Resilience Score Gain (+pts) & Blast Radius Mitigation
  6. Dashboard Summary Aggregation
"""

import sys
from pathlib import Path

# Ensure project root is in python path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from rakshastra_core.engines.digital_twin_engine import DigitalTwinEngine


def main():
    print("=" * 60)
    print("  POINT 5 E2E TEST: Cyber Resilience Digital Twin Engine")
    print("=" * 60)

    # Initialize engine in memory
    engine = DigitalTwinEngine(":memory:")

    # -------------------------------------------------------------------------
    # 1. Retrieve Graph Topology
    # -------------------------------------------------------------------------
    print("\n--- 1. Querying Digital Twin Topology ---")
    topo = engine.get_topology()
    print(f"Network Topology: {topo['nodes_count']} Nodes, {topo['edges_count']} Trust Edges")
    for node in topo["nodes"]:
        print(f"  - [{node['node_id']}] {node['name']} ({node['node_type']}) - Zone: {node['department']}")

    # -------------------------------------------------------------------------
    # 2. Simulate Ransomware Cascade Scenario
    # -------------------------------------------------------------------------
    print("\n--- 2. Simulating Ransomware Cascade Scenario ---")
    entry_node = "NODE-WORKSTATION-42"
    sim_ransomware = engine.simulate_attack("RANSOMWARE_CASCADE", entry_node_id=entry_node)

    print(f"Simulation ID: {sim_ransomware['sim_id']}")
    print(f"  Scenario: {sim_ransomware['scenario']}")
    print(f"  Entry Point: {sim_ransomware['entry_node']}")
    print(f"  Compromised Assets: {sim_ransomware['compromised_nodes_count']} / {sim_ransomware['total_network_nodes']}")
    print(f"  Blast Radius: {sim_ransomware['blast_radius_pct']}%")
    print(f"  Probability of Compromise (PoC): {sim_ransomware['probability_of_compromise']}")
    print(f"  Resilience Score Before Defense: {sim_ransomware['resilience_score']} / 100.0")

    assert sim_ransomware["compromised_nodes_count"] > 1
    assert sim_ransomware["resilience_score"] < 100.0

    # -------------------------------------------------------------------------
    # 3. Simulate APT Stealth Lateral Movement
    # -------------------------------------------------------------------------
    print("\n--- 3. Simulating APT Lateral Movement Scenario ---")
    sim_apt = engine.simulate_attack("APT_LATERAL_MOVEMENT", entry_node_id="NODE-DMZ-WEB")

    print(f"Simulation ID: {sim_apt['sim_id']}")
    print(f"  Scenario: {sim_apt['scenario']}")
    print(f"  Entry Point: {sim_apt['entry_node']}")
    print(f"  Compromised Assets: {sim_apt['compromised_nodes_count']} / {sim_apt['total_network_nodes']}")
    print(f"  Blast Radius: {sim_apt['blast_radius_pct']}%")
    print(f"  Resilience Score Before Defense: {sim_apt['resilience_score']} / 100.0")

    # -------------------------------------------------------------------------
    # 4. What-If Defensive Counter-Measure Validation
    # -------------------------------------------------------------------------
    print("\n--- 4. Applying What-If Defensive Counter-Measures ---")
    defense_controls = [
        {
            "action_type": "MICROSEGMENTATION",
            "source_id": "NODE-WORKSTATION-42",
            "target_id": "NODE-DC-01",
        },
        {
            "action_type": "ENFORCE_MFA",
            "node_id": "NODE-DC-01",
            "control": "MFA",
        },
        {
            "action_type": "ISOLATE_NODE",
            "node_id": "NODE-WORKSTATION-42",
        },
    ]

    whatif_res = engine.apply_defense_whatif(
        sim_id=sim_ransomware["sim_id"],
        defense_actions=defense_controls,
    )

    print(f"What-If Assessment for {whatif_res['sim_id']}:")
    print(f"  Applied Defensive Actions: {whatif_res['defense_actions_applied']}")
    print(f"  Compromised Nodes: {whatif_res['compromised_before']} -> {whatif_res['compromised_after']}")
    print(f"  Blast Radius: {whatif_res['blast_radius_before_pct']}% -> {whatif_res['blast_radius_after_pct']}%")
    print(f"  Resilience Score: {whatif_res['resilience_score_before']} -> {whatif_res['resilience_score_after']}")
    print(f"  Resilience Score Improvement: +{whatif_res['resilience_gain']} pts")
    print(f"  Is Defense Effective: {whatif_res['is_effective']}")

    assert whatif_res["is_effective"] is True
    assert whatif_res["resilience_score_after"] > whatif_res["resilience_score_before"]

    # -------------------------------------------------------------------------
    # 5. Dashboard Summary Metrics
    # -------------------------------------------------------------------------
    print("\n--- 5. Querying Digital Twin Dashboard Summary ---")
    summary = engine.get_summary()
    print(f"Digital Twin Graph Nodes: {summary['digital_twin_nodes']}")
    print(f"Digital Twin Trust Edges: {summary['digital_twin_edges']}")
    print(f"Simulations Executed: {summary['total_simulations_run']}")
    print(f"Average Resilience Before Defense: {summary['avg_resilience_before_defenses']}")
    print(f"Average Resilience After Defense: {summary['avg_resilience_after_defenses']}")
    print(f"Overall Network Resilience Score: {summary['resilience_score']} / 100.0")

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED — Point 5 Digital Twin Engine Ready!")
    print("=" * 60)


if __name__ == "__main__":
    main()
