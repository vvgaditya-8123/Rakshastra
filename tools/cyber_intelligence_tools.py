#!/usr/bin/env python3
"""
Cyber Intelligence & Drug Network Detection Tools

Exposes OSINT connectors, slang analysis, bot detection, entity resolution,
intelligence graph modeling, threat prioritization, and audit logging.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from rakshastra_constants import get_rakshastra_home

# Import core intelligence engines
from rakshastra_core.intelligence import (
    IntelligenceCollector,
    DrugSlangEngine,
    DrugIntelligenceEngine,
    BotDetector,
    EntityResolutionEngine,
    IntelligenceGraph,
    ThreatPrioritizationEngine,
    AuditComplianceEngine
)

from tools.registry import registry, tool_error, tool_result

# Lazy/global instantiations
_collector = None
_slang_engine = None
_drug_engine = None
_bot_detector = None
_entity_engine = None
_graph = None
_threat_engine = None
_audit_engine = None

def _get_collector():
    global _collector
    if _collector is None:
        _collector = IntelligenceCollector()
    return _collector

def _get_slang_engine():
    global _slang_engine
    if _slang_engine is None:
        _slang_engine = DrugSlangEngine()
    return _slang_engine

def _get_drug_engine():
    global _drug_engine
    if _drug_engine is None:
        _drug_engine = DrugIntelligenceEngine()
    return _drug_engine

def _get_bot_detector():
    global _bot_detector
    if _bot_detector is None:
        _bot_detector = BotDetector()
    return _bot_detector

def _get_entity_engine():
    global _entity_engine
    if _entity_engine is None:
        _entity_engine = EntityResolutionEngine()
    return _entity_engine

def _get_graph():
    global _graph
    if _graph is None:
        db_path = get_rakshastra_home() / "intelligence_graph.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _graph = IntelligenceGraph(db_path)
    return _graph

def _get_threat_engine():
    global _threat_engine
    if _threat_engine is None:
        _threat_engine = ThreatPrioritizationEngine()
    return _threat_engine

def _get_audit_engine():
    global _audit_engine
    if _audit_engine is None:
        _audit_engine = AuditComplianceEngine()
    return _audit_engine


# =============================================================================
# Tool Handlers
# =============================================================================

def cyber_collect_osint_handler(args: Dict[str, Any], **kwargs) -> str:
    source_type = args.get("source_type", "")
    target = args.get("target", "")
    
    collector = _get_collector()
    try:
        if source_type == "telegram":
            result = collector.collect_telegram(target)
        elif source_type == "instagram":
            result = collector.collect_instagram(target)
        elif source_type == "whatsapp":
            result = collector.collect_whatsapp_invites(target)
        elif source_type == "website":
            result = collector.collect_websites_and_pastes(target)
        else:
            return tool_error(f"Invalid source_type: {source_type}. Supported: telegram, instagram, whatsapp, website")
        
        # Log to audit compliance
        audit = _get_audit_engine()
        audit.log_action(
            investigator=kwargs.get("session_id", "system_agent"),
            action=f"collect_{source_type}",
            target=target,
            source_data=f"OSINT collection via {source_type}"
        )
        return tool_result(result)
    except Exception as e:
        return tool_error(f"Failed to collect OSINT: {e}")


def cyber_classify_drug_content_handler(args: Dict[str, Any], **kwargs) -> str:
    text = args.get("text", "")
    has_image = args.get("has_image", False)
    ocr_text = args.get("ocr_text", "")
    
    engine = _get_drug_engine()
    try:
        result = engine.analyze_content(text, has_image, ocr_text)
        return tool_result(result)
    except Exception as e:
        return tool_error(f"Failed to classify drug content: {e}")


def cyber_detect_automation_handler(args: Dict[str, Any], **kwargs) -> str:
    messages = args.get("messages", [])
    if not isinstance(messages, list):
        return tool_error("messages must be a list of strings")
        
    detector = _get_bot_detector()
    try:
        result = detector.detect_bot_behavior(messages)
        return tool_result(result)
    except Exception as e:
        return tool_error(f"Failed to detect bot behavior: {e}")


def cyber_resolve_entities_handler(args: Dict[str, Any], **kwargs) -> str:
    action = args.get("action", "")
    entity_engine = _get_entity_engine()
    
    try:
        # Sync identity links with DB
        graph = _get_graph()
        conn = graph._get_connection()
        try:
            rows = conn.execute("SELECT source_id, target_id FROM intelligence_relations").fetchall()
            for r in rows:
                entity_engine.link_entities(r["source_id"], r["target_id"])
        except Exception:
            pass
        finally:
            conn.close()

        if action == "link":
            entity_a = args.get("entity_a", "")
            entity_b = args.get("entity_b", "")
            if not entity_a or not entity_b:
                return tool_error("entity_a and entity_b are required for linking")
            entity_engine.link_entities(entity_a, entity_b)
            
            # Save relation to graph DB for persistence
            import hashlib
            rel_id = hashlib.sha256(f"{entity_a}-{entity_b}".encode()).hexdigest()[:12]
            graph.add_intelligence_relation(
                relation_id=f"R-{rel_id.upper()}",
                source_id=entity_a,
                target_id=entity_b,
                relation_type="links_to",
                properties={"source": "entity_resolution_linking"}
            )
            
            # Add nodes if they don't exist
            def _node_type(val):
                if val.startswith("@") or len(val) < 8: return "telegram"
                if val.startswith("+") or (val.isdigit() and len(val) >= 10): return "phone"
                if val.startswith("0x") or val.startswith("bc1") or len(val) >= 30: return "wallet"
                if "@" in val: return "upi"
                return "suspect"
            
            graph.add_intelligence_node(entity_a, _node_type(entity_a), entity_a, {})
            graph.add_intelligence_node(entity_b, _node_type(entity_b), entity_b, {})

            # Log to audit compliance
            audit = _get_audit_engine()
            audit.log_action(
                investigator=kwargs.get("session_id", "system_agent"),
                action="link_entities",
                target=f"{entity_a}<->{entity_b}",
                source_data="Entity Resolution linkage"
            )

            return tool_result({"success": True, "message": f"Linked {entity_a} to {entity_b}"})
            
        elif action == "resolve":
            seed_entity = args.get("seed_entity", "")
            if not seed_entity:
                return tool_error("seed_entity is required for resolution")
            profile = entity_engine.resolve_operator(seed_entity)
            return tool_result(profile)
        else:
            return tool_error("action must be 'link' or 'resolve'")
    except Exception as e:
        return tool_error(f"Failed to resolve entities: {e}")


def cyber_manage_intelligence_graph_handler(args: Dict[str, Any], **kwargs) -> str:
    action = args.get("action", "")
    graph = _get_graph()
    
    try:
        if action == "add_node":
            node_id = args.get("node_id", "")
            node_type = args.get("node_type", "")
            display_name = args.get("display_name", "")
            properties = args.get("properties", {})
            if not node_id or not node_type:
                return tool_error("node_id and node_type are required to add node")
            graph.add_intelligence_node(node_id, node_type, display_name or node_id, properties)
            return tool_result({"success": True, "message": f"Added node {node_id}"})
            
        elif action == "add_relation":
            relation_id = args.get("relation_id", "")
            source_id = args.get("source_id", "")
            target_id = args.get("target_id", "")
            relation_type = args.get("relation_type", "")
            properties = args.get("properties", {})
            if not source_id or not target_id or not relation_type:
                return tool_error("source_id, target_id, and relation_type are required to add relation")
            if not relation_id:
                import hashlib
                relation_id = f"R-{hashlib.sha256(f'{source_id}-{target_id}-{relation_type}'.encode()).hexdigest()[:12].upper()}"
            graph.add_intelligence_relation(relation_id, source_id, target_id, relation_type, properties)
            return tool_result({"success": True, "message": f"Added relation {relation_id}"})
            
        elif action == "get_network":
            suspect_id = args.get("suspect_id", "")
            if not suspect_id:
                return tool_error("suspect_id is required to get network")
            network = graph.get_criminal_network(suspect_id)
            return tool_result(network)
        else:
            return tool_error("action must be 'add_node', 'add_relation', or 'get_network'")
    except Exception as e:
        return tool_error(f"Failed to manage graph: {e}")


def cyber_calculate_risk_and_prioritize_handler(args: Dict[str, Any], **kwargs) -> str:
    action = args.get("action", "")
    threat_engine = _get_threat_engine()
    
    try:
        if action == "calculate_score":
            drug_probability = args.get("drug_probability", 0.0)
            automation_confidence = args.get("automation_confidence", 0.0)
            platform_count = args.get("platform_count", 0)
            network_size = args.get("network_size", 0)
            has_financials = args.get("has_financials", False)
            result = threat_engine.calculate_risk_score(
                drug_probability, automation_confidence, platform_count, network_size, has_financials
            )
            return tool_result(result)
            
        elif action == "prioritize_watchlist":
            targets = args.get("targets", [])
            if not isinstance(targets, list):
                return tool_error("targets must be a list of objects")
            result = threat_engine.prioritize_watchlist(targets)
            return tool_result(result)
        else:
            return tool_error("action must be 'calculate_score' or 'prioritize_watchlist'")
    except Exception as e:
        return tool_error(f"Failed to run threat engine: {e}")


def cyber_log_audit_compliance_handler(args: Dict[str, Any], **kwargs) -> str:
    action = args.get("action", "")
    audit = _get_audit_engine()
    
    try:
        if action == "log_action":
            investigator = args.get("investigator", "") or kwargs.get("session_id", "system_agent")
            audit_action = args.get("audit_action", "")
            target = args.get("target", "")
            source_data = args.get("source_data", "")
            if not audit_action or not target:
                return tool_error("audit_action and target are required")
            result = audit.log_action(investigator, audit_action, target, source_data)
            return tool_result(result)
            
        elif action == "verify_evidence":
            resolved_profile = args.get("resolved_profile", {})
            source_transcripts = args.get("source_transcripts", [])
            if not resolved_profile or not source_transcripts:
                return tool_error("resolved_profile and source_transcripts are required")
            result = audit.verify_evidence_trail(resolved_profile, source_transcripts)
            return tool_result(result)
        else:
            return tool_error("action must be 'log_action' or 'verify_evidence'")
    except Exception as e:
        return tool_error(f"Failed to log audit/compliance: {e}")


def cyber_train_dataset_handler(args: Dict[str, Any], **kwargs) -> str:
    csv_path = args.get("csv_path", "")
    dataset_type = args.get("dataset_type", "twitter")

    if not csv_path:
        return tool_error("csv_path is required")

    import os
    if not os.path.exists(csv_path):
        return tool_error(f"CSV file not found: {csv_path}")

    try:
        from scripts.train_drug_classifier import train
        stats = train(csv_path)

        # Reset cached engines so they reload learned data
        global _slang_engine, _drug_engine
        _slang_engine = None
        _drug_engine = None

        # Log to audit
        audit = _get_audit_engine()
        audit.log_action(
            investigator=kwargs.get("session_id", "system_agent"),
            action="train_dataset",
            target=csv_path,
            source_data=f"Trained from {dataset_type} dataset: {stats.get('total_rows_processed', 0)} rows"
        )

        return tool_result({
            "success": True,
            "message": f"Training complete. Processed {stats.get('total_rows_processed', 0)} rows.",
            "stats": stats,
        })
    except Exception as e:
        return tool_error(f"Training failed: {e}")


def cyber_get_vocabulary_stats_handler(args: Dict[str, Any], **kwargs) -> str:
    engine = _get_slang_engine()
    try:
        stats = engine.get_vocabulary_stats()
        return tool_result(stats)
    except Exception as e:
        return tool_error(f"Failed to get vocabulary stats: {e}")


# =============================================================================
# OpenAI Function-Calling Schemas
# =============================================================================

CYBER_COLLECT_OSINT_SCHEMA = {
    "name": "cyber_collect_osint",
    "description": (
        "Collect publicly available OSINT data from online platforms "
        "(Telegram, Instagram, WhatsApp invite text, or specific website/paste links)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "source_type": {
                "type": "string",
                "enum": ["telegram", "instagram", "whatsapp", "website"],
                "description": "The OSINT data source platform to query."
            },
            "target": {
                "type": "string",
                "description": (
                    "The specific target reference. For telegram: channel/group name; "
                    "for instagram: hashtag or profile; for whatsapp: text block containing invite links; "
                    "for website: the target paste site or forum URL."
                )
            }
        },
        "required": ["source_type", "target"]
    }
}

CYBER_CLASSIFY_DRUG_CONTENT_SCHEMA = {
    "name": "cyber_classify_drug_content",
    "description": (
        "Analyze a text message or OCR text to detect drug trafficking code words, "
        "slang, emojis, and Hinglish phrases. Computes a Drug Probability Score."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The primary message body or caption text to analyze."
            },
            "has_image": {
                "type": "boolean",
                "description": "Set to true if there is an image attachment associated with the text."
            },
            "ocr_text": {
                "type": "string",
                "description": "Optical Character Recognition (OCR) text extracted from any attached media."
            }
        },
        "required": ["text"]
    }
}

CYBER_DETECT_AUTOMATION_SCHEMA = {
    "name": "cyber_detect_automation",
    "description": (
        "Scan a list of channel/group messages to detect bot behaviors, automated commands, "
        "or template-based spam forwards. Returns an Automation Confidence Score."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of recent message strings to analyze."
            }
        },
        "required": ["messages"]
    }
}

CYBER_RESOLVE_ENTITIES_SCHEMA = {
    "name": "cyber_resolve_entities",
    "description": (
        "Cross-reference identities, usernames, UPIs, crypto wallets, and phone numbers "
        "to link disparate footprints into a Unified Operator Profile."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["link", "resolve"],
                "description": "link: register a connection between two nodes; resolve: trace all linked profiles from a seed."
            },
            "entity_a": {
                "type": "string",
                "description": "First entity token to link (required for action='link')."
            },
            "entity_b": {
                "type": "string",
                "description": "Second entity token to link (required for action='link')."
            },
            "seed_entity": {
                "type": "string",
                "description": "The target identity token to resolve Operator Profile for (required for action='resolve')."
            }
        },
        "required": ["action"]
    }
}

CYBER_MANAGE_INTELLIGENCE_GRAPH_SCHEMA = {
    "name": "cyber_manage_intelligence_graph",
    "description": (
        "Insert nodes, define relationships (e.g. owns, forwards_to, mentions), or query "
        "and traverse mapped criminal networks."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add_node", "add_relation", "get_network"],
                "description": "The graph management operation to perform."
            },
            "node_id": {
                "type": "string",
                "description": "Unique identifier for the node (required for action='add_node')."
            },
            "node_type": {
                "type": "string",
                "enum": ["telegram", "instagram", "wallet", "upi", "phone", "suspect"],
                "description": "Type classification of the node (required for action='add_node')."
            },
            "display_name": {
                "type": "string",
                "description": "Friendly name for UI visualization."
            },
            "properties": {
                "type": "object",
                "description": "Arbitrary metadata properties to bind to the node or relation."
            },
            "relation_id": {
                "type": "string",
                "description": "Unique identifier for the relation link (optional)."
            },
            "source_id": {
                "type": "string",
                "description": "Source node ID for the relation link (required for action='add_relation')."
            },
            "target_id": {
                "type": "string",
                "description": "Target node ID for the relation link (required for action='add_relation')."
            },
            "relation_type": {
                "type": "string",
                "description": "Relationship type (e.g., owns, forwards_to, mentions, shares_media) (required for action='add_relation')."
            },
            "suspect_id": {
                "type": "string",
                "description": "The seed suspect node ID to trace network nodes and edges from (required for action='get_network')."
            }
        },
        "required": ["action"]
    }
}

CYBER_CALCULATE_RISK_AND_PRIORITIZE_SCHEMA = {
    "name": "cyber_calculate_risk_and_prioritize",
    "description": (
        "Compute intelligence risk severity scores or sort target watchlists by severity prioritization."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["calculate_score", "prioritize_watchlist"],
                "description": "The threat analysis action to run."
            },
            "drug_probability": {
                "type": "number",
                "description": "Drug Probability Score (0.0 to 1.0) (required for action='calculate_score')."
            },
            "automation_confidence": {
                "type": "number",
                "description": "Automation Confidence Score (0.0 to 1.0) (required for action='calculate_score')."
            },
            "platform_count": {
                "type": "integer",
                "description": "Number of platforms where the target footprint is monitored (required for action='calculate_score')."
            },
            "network_size": {
                "type": "integer",
                "description": "Count of resolved network nodes (required for action='calculate_score')."
            },
            "has_financials": {
                "type": "boolean",
                "description": "True if cryptocurrency wallets or UPI details were mapped (required for action='calculate_score')."
            },
            "targets": {
                "type": "array",
                "items": {
                    "type": "object"
                },
                "description": "List of targets to compute scores and prioritize (required for action='prioritize_watchlist')."
            }
        },
        "required": ["action"]
    }
}

CYBER_LOG_AUDIT_COMPLIANCE_SCHEMA = {
    "name": "cyber_log_audit_compliance",
    "description": (
        "Manage OSINT action audit logging or verify evidentiary compliance trails back to raw transcripts."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["log_action", "verify_evidence"],
                "description": "The audit compliance operation to perform."
            },
            "investigator": {
                "type": "string",
                "description": "ID/Name of the investigator or agent session."
            },
            "audit_action": {
                "type": "string",
                "description": "The action being audited (e.g. 'collect_telegram') (required for action='log_action')."
            },
            "target": {
                "type": "string",
                "description": "The entity or group targeted in the action (required for action='log_action')."
            },
            "source_data": {
                "type": "string",
                "description": "Origins/reference of public data used (required for action='log_action')."
            },
            "resolved_profile": {
                "type": "object",
                "description": "The resolved Unified Operator Profile (required for action='verify_evidence')."
            },
            "source_transcripts": {
                "type": "array",
                "items": {
                    "type": "object"
                },
                "description": "Raw transcript logs containing the matching identifiers (required for action='verify_evidence')."
            }
        },
        "required": ["action"]
    }
}


CYBER_TRAIN_DATASET_SCHEMA = {
    "name": "cyber_train_dataset",
    "description": (
        "Train the drug content classifier from a labeled CSV dataset. "
        "Extracts drug vocabulary, slang, handle patterns, and transaction phrases "
        "from labeled data to improve classification accuracy."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "csv_path": {
                "type": "string",
                "description": "Absolute path to the CSV file. Must have columns: url, label (T=drug, F=non-drug)."
            },
            "dataset_type": {
                "type": "string",
                "enum": ["twitter", "telegram", "instagram"],
                "description": "Type of dataset being ingested. Default: twitter."
            }
        },
        "required": ["csv_path"]
    }
}

CYBER_GET_VOCABULARY_STATS_SCHEMA = {
    "name": "cyber_get_vocabulary_stats",
    "description": (
        "Get statistics about the drug classifier's loaded vocabulary, "
        "including learned terms, flagged handles, and pattern counts."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}


# =============================================================================
# Register Tools
# =============================================================================

registry.register(
    name="cyber_collect_osint",
    toolset="cyber_intelligence",
    schema=CYBER_COLLECT_OSINT_SCHEMA,
    handler=cyber_collect_osint_handler,
    check_fn=lambda: True,
    emoji="\U0001f4e1",
)

registry.register(
    name="cyber_train_dataset",
    toolset="cyber_intelligence",
    schema=CYBER_TRAIN_DATASET_SCHEMA,
    handler=cyber_train_dataset_handler,
    check_fn=lambda: True,
    emoji="\ud83c\udfeb",
)

registry.register(
    name="cyber_get_vocabulary_stats",
    toolset="cyber_intelligence",
    schema=CYBER_GET_VOCABULARY_STATS_SCHEMA,
    handler=cyber_get_vocabulary_stats_handler,
    check_fn=lambda: True,
    emoji="\ud83d\udcca",
)

registry.register(
    name="cyber_classify_drug_content",
    toolset="cyber_intelligence",
    schema=CYBER_CLASSIFY_DRUG_CONTENT_SCHEMA,
    handler=cyber_classify_drug_content_handler,
    check_fn=lambda: True,
    emoji="🔬",
)

registry.register(
    name="cyber_detect_automation",
    toolset="cyber_intelligence",
    schema=CYBER_DETECT_AUTOMATION_SCHEMA,
    handler=cyber_detect_automation_handler,
    check_fn=lambda: True,
    emoji="🤖",
)

registry.register(
    name="cyber_resolve_entities",
    toolset="cyber_intelligence",
    schema=CYBER_RESOLVE_ENTITIES_SCHEMA,
    handler=cyber_resolve_entities_handler,
    check_fn=lambda: True,
    emoji="🔗",
)

registry.register(
    name="cyber_manage_intelligence_graph",
    toolset="cyber_intelligence",
    schema=CYBER_MANAGE_INTELLIGENCE_GRAPH_SCHEMA,
    handler=cyber_manage_intelligence_graph_handler,
    check_fn=lambda: True,
    emoji="🕸️",
)

registry.register(
    name="cyber_calculate_risk_and_prioritize",
    toolset="cyber_intelligence",
    schema=CYBER_CALCULATE_RISK_AND_PRIORITIZE_SCHEMA,
    handler=cyber_calculate_risk_and_prioritize_handler,
    check_fn=lambda: True,
    emoji="⚖️",
)

registry.register(
    name="cyber_log_audit_compliance",
    toolset="cyber_intelligence",
    schema=CYBER_LOG_AUDIT_COMPLIANCE_SCHEMA,
    handler=cyber_log_audit_compliance_handler,
    check_fn=lambda: True,
    emoji="📜",
)
