#!/usr/bin/env python3
"""Cyber Resilience Digital Twin Tools (Point 5).

Registers agent-callable tools for digital twin topology modeling,
red-team attack simulations, blast radius analysis, and what-if defense validation:
  - Add & inspect topology nodes and network trust edges
  - Run simulated cyber attack scenarios (Ransomware, APT, Zero-Day, Exfiltration)
  - Compute simulated blast radius & Probability of Compromise (PoC)
  - Apply virtual What-If defense interventions (Microsegmentation, MFA, Isolation)
  - Query aggregate digital twin resilience summary
"""

from typing import Any, Dict, List, Optional

from rakshastra_constants import get_rakshastra_home
from tools.registry import registry, tool_error, tool_result

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from rakshastra_core.engines.digital_twin_engine import DigitalTwinEngine
        db_path = get_rakshastra_home() / "digital_twin.db"
        _engine = DigitalTwinEngine(db_path)
    return _engine


def check_digital_twin_requirements() -> bool:
    """Always available — stdlib SQLite backing."""
    return True


# =============================================================================
# Tool Handlers
# =============================================================================

def dt_add_node_handler(args: Dict[str, Any], **kwargs) -> str:
    """Add a node to the digital twin graph topology."""
    name = args.get("name", "")
    if not name:
        return tool_error("name is required")

    node_type = args.get("node_type", "HOST")
    department = args.get("department", "IT")
    ip_address = args.get("ip_address", "")
    security_controls = args.get("security_controls", [])
    vulnerability_count = args.get("vulnerability_count", 0)
    criticality_weight = args.get("criticality_weight", 1.0)
    node_id = args.get("node_id")

    try:
        engine = _get_engine()
        res = engine.add_node(
            name=name,
            node_type=node_type,
            department=department,
            ip_address=ip_address,
            security_controls=security_controls,
            vulnerability_count=vulnerability_count,
            criticality_weight=criticality_weight,
            node_id=node_id,
        )
        return tool_result(
            success=True,
            **res,
            message=f"Digital Twin Node '{name}' ({res['node_id']}) added to topology.",
        )
    except Exception as e:
        return tool_error(f"Failed to add Digital Twin node: {e}")


def dt_add_edge_handler(args: Dict[str, Any], **kwargs) -> str:
    """Add a network/trust edge between digital twin nodes."""
    source_id = args.get("source_id", "")
    target_id = args.get("target_id", "")
    if not source_id or not target_id:
        return tool_error("source_id and target_id are required")

    protocol = args.get("protocol", "TCP")
    port = args.get("port")
    trust_level = args.get("trust_level", 0.5)
    edge_id = args.get("edge_id")

    try:
        engine = _get_engine()
        res = engine.add_edge(
            source_id=source_id,
            target_id=target_id,
            protocol=protocol,
            port=port,
            trust_level=trust_level,
            edge_id=edge_id,
        )
        return tool_result(
            success=True,
            **res,
            message=f"Digital Twin Edge ({source_id} -> {target_id}) added on protocol {protocol}.",
        )
    except Exception as e:
        return tool_error(f"Failed to add Digital Twin edge: {e}")


def dt_get_topology_handler(args: Dict[str, Any], **kwargs) -> str:
    """Retrieve full digital twin graph topology."""
    try:
        engine = _get_engine()
        topology = engine.get_topology()
        return tool_result(success=True, **topology)
    except Exception as e:
        return tool_error(f"Failed to retrieve Digital Twin topology: {e}")


def dt_simulate_attack_handler(args: Dict[str, Any], **kwargs) -> str:
    """Simulate a red-team cyber attack scenario."""
    scenario_key = args.get("scenario_key", "")
    entry_node_id = args.get("entry_node_id", "")
    if not scenario_key or not entry_node_id:
        return tool_error("scenario_key and entry_node_id are required")

    try:
        engine = _get_engine()
        res = engine.simulate_attack(scenario_key=scenario_key, entry_node_id=entry_node_id)
        if "error" in res:
            return tool_error(res["error"])

        msg = (
            f"Attack Simulation '{res['sim_id']}' Complete:\n"
            f"  Scenario: {res['scenario']}\n"
            f"  Entry Point: {res['entry_node']}\n"
            f"  Compromised Assets: {res['compromised_nodes_count']} / {res['total_network_nodes']}\n"
            f"  Blast Radius: {res['blast_radius_pct']}%\n"
            f"  Probability of Compromise (PoC): {res['probability_of_compromise']}\n"
            f"  Network Resilience Score: {res['resilience_score']} / 100.0"
        )
        return tool_result(success=True, **res, message=msg)
    except Exception as e:
        return tool_error(f"Attack simulation failed: {e}")


def dt_apply_defense_whatif_handler(args: Dict[str, Any], **kwargs) -> str:
    """Validate virtual What-If defensive intervention against a simulation."""
    sim_id = args.get("sim_id", "")
    defense_actions = args.get("defense_actions", [])
    if not sim_id or not defense_actions:
        return tool_error("sim_id and defense_actions array are required")

    try:
        engine = _get_engine()
        res = engine.apply_defense_whatif(sim_id=sim_id, defense_actions=defense_actions)
        if "error" in res:
            return tool_error(res["error"])

        msg = (
            f"What-If Defensive Intervention Assessment ({res['sim_id']}):\n"
            f"  Scenario: {res['scenario']}\n"
            f"  Applied Controls: {res['defense_actions_applied']}\n"
            f"  Compromised Nodes: {res['compromised_before']} -> {res['compromised_after']}\n"
            f"  Blast Radius: {res['blast_radius_before_pct']}% -> {res['blast_radius_after_pct']}%\n"
            f"  Resilience Score: {res['resilience_score_before']} -> {res['resilience_score_after']} "
            f"(+{res['resilience_gain']} pts)"
        )
        return tool_result(success=True, **res, message=msg)
    except Exception as e:
        return tool_error(f"What-If defense assessment failed: {e}")


def dt_dashboard_summary_handler(args: Dict[str, Any], **kwargs) -> str:
    """Get aggregate Digital Twin summary metrics."""
    try:
        engine = _get_engine()
        summary = engine.get_summary()
        return tool_result(success=True, **summary)
    except Exception as e:
        return tool_error(f"Dashboard summary failed: {e}")


# =============================================================================
# OpenAI Function-Calling Schemas
# =============================================================================

DT_ADD_NODE_SCHEMA = {
    "name": "dt_add_node",
    "description": "Add a host, database, firewall, or domain controller to the Digital Twin graph topology.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Node name (e.g. 'Primary Citizen DB')."},
            "node_type": {
                "type": "string",
                "enum": ["HOST", "FIREWALL", "ROUTER", "DATABASE", "DOMAIN_CONTROLLER", "WORKSTATION", "CLOUD_STORAGE"],
                "description": "Node asset type.",
            },
            "department": {"type": "string", "description": "Department or network zone (e.g. 'DMZ', 'NIC', 'MoD')."},
            "ip_address": {"type": "string", "description": "Node IP address."},
            "security_controls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Active security controls (e.g. ['MFA', 'EDR', 'WAF']).",
            },
            "vulnerability_count": {"type": "integer", "description": "Unpatched vulnerability count."},
            "criticality_weight": {"type": "number", "description": "Asset criticality weight (1.0 to 3.0)."},
            "node_id": {"type": "string", "description": "Optional node ID override."},
        },
        "required": ["name"],
    },
}

DT_ADD_EDGE_SCHEMA = {
    "name": "dt_add_edge",
    "description": "Add a network protocol or trust connection edge between two Digital Twin nodes.",
    "parameters": {
        "type": "object",
        "properties": {
            "source_id": {"type": "string", "description": "Source node ID."},
            "target_id": {"type": "string", "description": "Target node ID."},
            "protocol": {"type": "string", "description": "Network protocol (e.g. 'HTTPS', 'SSH', 'SMB', 'KERBEROS')."},
            "port": {"type": "integer", "description": "Destination port."},
            "trust_level": {"type": "number", "description": "Trust level from 0.0 (untrusted) to 1.0 (highly trusted)."},
            "edge_id": {"type": "string", "description": "Optional edge ID override."},
        },
        "required": ["source_id", "target_id"],
    },
}

DT_GET_TOPOLOGY_SCHEMA = {
    "name": "dt_get_topology",
    "description": "Retrieve full digital twin graph topology including all nodes, edges, and security controls.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

DT_SIMULATE_ATTACK_SCHEMA = {
    "name": "dt_simulate_attack",
    "description": (
        "Run a simulated red-team cyber attack scenario across the Digital Twin graph. "
        "Calculates simulated blast radius %, Probability of Compromise (PoC), and network resilience score."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "scenario_key": {
                "type": "string",
                "enum": ["RANSOMWARE_CASCADE", "APT_LATERAL_MOVEMENT", "ZERO_DAY_CASCADE", "DATA_EXFILTRATION"],
                "description": "Attack scenario template key.",
            },
            "entry_node_id": {"type": "string", "description": "Target entry node ID where attack originates."},
        },
        "required": ["scenario_key", "entry_node_id"],
    },
}

DT_APPLY_DEFENSE_WHATIF_SCHEMA = {
    "name": "dt_apply_defense_whatif",
    "description": (
        "Validate virtual What-If defensive security controls against an attack simulation. "
        "Tests interventions (e.g. Microsegmentation, MFA enforcement, Node isolation) and measures resilience score gain."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "sim_id": {"type": "string", "description": "Simulation ID from a prior dt_simulate_attack run."},
            "defense_actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action_type": {
                            "type": "string",
                            "enum": ["MICROSEGMENTATION", "ENFORCE_MFA", "ISOLATE_NODE", "BLOCK_EDGE"],
                        },
                        "node_id": {"type": "string"},
                        "source_id": {"type": "string"},
                        "target_id": {"type": "string"},
                        "control": {"type": "string"},
                    },
                    "required": ["action_type"],
                },
                "description": "List of virtual defensive actions to evaluate.",
            },
        },
        "required": ["sim_id", "defense_actions"],
    },
}

DT_DASHBOARD_SUMMARY_SCHEMA = {
    "name": "dt_dashboard_summary",
    "description": "Get aggregate digital twin resilience metrics, total graph nodes/edges, and average resilience scores.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

# =============================================================================
# Register Tools
# =============================================================================

registry.register(
    name="dt_add_node",
    toolset="digital_twin",
    schema=DT_ADD_NODE_SCHEMA,
    handler=dt_add_node_handler,
    check_fn=check_digital_twin_requirements,
    emoji="🖥️",
)

registry.register(
    name="dt_add_edge",
    toolset="digital_twin",
    schema=DT_ADD_EDGE_SCHEMA,
    handler=dt_add_edge_handler,
    check_fn=check_digital_twin_requirements,
    emoji="🔗",
)

registry.register(
    name="dt_get_topology",
    toolset="digital_twin",
    schema=DT_GET_TOPOLOGY_SCHEMA,
    handler=dt_get_topology_handler,
    check_fn=check_digital_twin_requirements,
    emoji="🌐",
)

registry.register(
    name="dt_simulate_attack",
    toolset="digital_twin",
    schema=DT_SIMULATE_ATTACK_SCHEMA,
    handler=dt_simulate_attack_handler,
    check_fn=check_digital_twin_requirements,
    emoji="⚔️",
)

registry.register(
    name="dt_apply_defense_whatif",
    toolset="digital_twin",
    schema=DT_APPLY_DEFENSE_WHATIF_SCHEMA,
    handler=dt_apply_defense_whatif_handler,
    check_fn=check_digital_twin_requirements,
    emoji="🛡️",
)

registry.register(
    name="dt_dashboard_summary",
    toolset="digital_twin",
    schema=DT_DASHBOARD_SUMMARY_SCHEMA,
    handler=dt_dashboard_summary_handler,
    check_fn=check_digital_twin_requirements,
    emoji="📊",
)
