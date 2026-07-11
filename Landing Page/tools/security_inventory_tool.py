import json
from pathlib import Path
from rakshastra_constants import get_rakshastra_home
from rakshastra_core.models import Asset, AssetRelation, AssetType
from rakshastra_core.engines import InfrastructureGraph
from tools.registry import registry, tool_result, tool_error

import uuid
import os
from datetime import datetime
from rakshastra_core.engines.workflow import SecurityWorkflowEngine
from rakshastra_core.models.workflow import WorkflowStep

def check_security_requirements() -> bool:
    return True

def _get_infrastructure_graph() -> InfrastructureGraph:
    db_path = get_rakshastra_home() / "security.db"
    return InfrastructureGraph(db_path)

def _handle_security_inventory(args: dict, **kwargs) -> str:
    session_id = kwargs.get("session_id") or os.environ.get("RAKSHASTRA_SESSION_ID", "default_session")
    db_path = get_rakshastra_home() / "security.db"
    wf_engine = SecurityWorkflowEngine(db_path)
    current_wf_phase = wf_engine.get_active_phase(session_id)
    action = args.get("action", "unknown")

    res = _handle_security_inventory_inner(args, **kwargs)

    status = "completed" if "error" not in str(res) else "failed"
    step = WorkflowStep(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow().isoformat() + "Z",
        session_id=session_id,
        phase=current_wf_phase,
        command=f"security_inventory(action={action})",
        status=status,
        duration=0.0,
        output_summary=f"Executed inventory action: {action}."
    )
    wf_engine.log_step(step)
    return res

def _handle_security_inventory_inner(args: dict, **kwargs) -> str:
    action = args.get("action")
    graph = _get_infrastructure_graph()

    try:
        if action == "add_asset":
            asset_data = args.get("asset")
            if not asset_data or not isinstance(asset_data, dict):
                return tool_error("Missing or invalid 'asset' details for add_asset action.")
            
            atype_str = asset_data.get("asset_type", "host")
            try:
                asset_type = AssetType(atype_str.lower())
            except ValueError:
                asset_type = AssetType.HOST
                
            asset = Asset(
                name=asset_data.get("name", "Unnamed Asset"),
                asset_type=asset_type,
                hostname=asset_data.get("hostname"),
                ip_address=asset_data.get("ip_address"),
                properties=asset_data.get("properties", {}),
                tags=asset_data.get("tags", [])
            )
            if "id" in asset_data:
                asset.id = asset_data["id"]
            
            aid = graph.add_asset(asset)
            return tool_result(success=True, asset_id=aid, message=f"Asset '{asset.name}' added successfully.")

        elif action == "add_relation":
            rel_data = args.get("relation")
            if not rel_data or not isinstance(rel_data, dict):
                return tool_error("Missing or invalid 'relation' details for add_relation action.")
            
            relation = AssetRelation(
                source_id=rel_data.get("source_id", ""),
                target_id=rel_data.get("target_id", ""),
                relation_type=rel_data.get("relation_type", "connects_to"),
                properties=rel_data.get("properties", {})
            )
            rid = graph.add_relation(relation)
            return tool_result(success=True, relation_id=rid, message="Asset relation added successfully.")

        elif action == "list_assets":
            assets = graph.find_assets()
            return tool_result(success=True, assets=[a.to_dict() for a in assets])

        elif action == "find_assets":
            query = args.get("query")
            assets = graph.find_assets(query=query)
            return tool_result(success=True, assets=[a.to_dict() for a in assets])

        elif action == "neighbors":
            asset_id = args.get("asset_id")
            if not asset_id:
                return tool_error("Missing 'asset_id' for neighbors action.")
            depth = args.get("depth", 1)
            result = graph.neighbors(asset_id, depth=depth)
            return tool_result(success=True, **result)

        elif action == "attack_surface":
            asset_id = args.get("asset_id")
            if not asset_id:
                return tool_error("Missing 'asset_id' for attack_surface action.")
            reachable = graph.attack_surface(asset_id)
            return tool_result(success=True, attack_surface=[a.to_dict() for a in reachable])

        elif action == "visualize_mermaid":
            asset_id = args.get("asset_id")
            asset_ids = None
            if asset_id:
                asset_ids = [asset_id]
                n_info = graph.neighbors(asset_id, depth=1)
                asset_ids.extend(list(n_info["assets"].keys()))
            
            mermaid_str = graph.to_mermaid(asset_ids=asset_ids)
            return tool_result(success=True, mermaid=mermaid_str)

        else:
            return tool_error(f"Unknown inventory action: {action}")

    except Exception as e:
        return tool_error(f"Failed to execute security inventory action: {str(e)}")

SECURITY_INVENTORY_SCHEMA = {
    "name": "security_inventory",
    "description": "Manage security assets and relations in the Asset Graph.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add_asset", "add_relation", "list_assets", "find_assets", "neighbors", "attack_surface", "visualize_mermaid"],
                "description": "The inventory action to perform."
            },
            "asset": {
                "type": "object",
                "description": "Asset attributes for add_asset action. Keys: name, asset_type, hostname, ip_address, properties (dict), tags (array), id (optional)."
            },
            "relation": {
                "type": "object",
                "description": "Relation attributes for add_relation action. Keys: source_id, target_id, relation_type, properties (dict)."
            },
            "query": {
                "type": "string",
                "description": "Search query for find_assets action."
            },
            "asset_id": {
                "type": "string",
                "description": "Asset ID for neighbors, attack_surface, or visualization."
            },
            "depth": {
                "type": "integer",
                "default": 1,
                "description": "Graph traversal depth for neighbors search."
            }
        },
        "required": ["action"]
    }
}

registry.register(
    name="security_inventory",
    toolset="security",
    schema=SECURITY_INVENTORY_SCHEMA,
    handler=_handle_security_inventory,
    check_fn=check_security_requirements,
    emoji="🛡️"
)
