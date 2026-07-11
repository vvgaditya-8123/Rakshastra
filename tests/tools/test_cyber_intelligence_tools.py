"""Tests for the cyber intelligence tools module."""

import json
import pytest
from pathlib import Path
from tools.cyber_intelligence_tools import (
    cyber_collect_osint_handler,
    cyber_classify_drug_content_handler,
    cyber_detect_automation_handler,
    cyber_resolve_entities_handler,
    cyber_manage_intelligence_graph_handler,
    cyber_calculate_risk_and_prioritize_handler,
    cyber_log_audit_compliance_handler
)

class TestCyberIntelligenceTools:
    def test_collect_osint(self):
        # Telegram collector test
        res_str = cyber_collect_osint_handler({"source_type": "telegram", "target": "test_group"})
        res = json.loads(res_str)
        assert isinstance(res, list)
        assert res[0]["platform"] == "telegram"
        assert res[0]["channel"] == "test_group"

        # Instagram collector test
        res_str = cyber_collect_osint_handler({"source_type": "instagram", "target": "test_tag"})
        res = json.loads(res_str)
        assert isinstance(res, list)
        assert res[0]["platform"] == "instagram"
        assert res[0]["profile"] == "test_tag"

        # Invalid source_type
        res_str = cyber_collect_osint_handler({"source_type": "invalid", "target": "target"})
        res = json.loads(res_str)
        assert "error" in res

    def test_classify_drug_content(self):
        res_str = cyber_classify_drug_content_handler({"text": "Get ecstasy/molly DM for deal. Emojis: 💊"})
        res = json.loads(res_str)
        assert res["drug_probability_score"] > 0.0
        assert "mdma" in res["matched_slang"]
        assert "💊" in res["matched_emojis"]

    def test_detect_automation(self):
        res_str = cyber_detect_automation_handler({
            "messages": ["/start", "/help", "/start", "/start", "/help", "/help", "/buy", "/price"]
        })
        res = json.loads(res_str)
        assert res["automation_confidence"] >= 0.8
        assert res["is_automated"] is True

    def test_resolve_entities(self, tmp_path, monkeypatch):
        # Override RAKSHASTRA_HOME so it uses tmp_path for intelligence_graph.db
        monkeypatch.setenv("RAKSHASTRA_HOME", str(tmp_path))
        
        # Link entity_a and entity_b
        res_str = cyber_resolve_entities_handler({
            "action": "link",
            "entity_a": "@suspect_dealer",
            "entity_b": "+919999999999"
        })
        res = json.loads(res_str)
        assert res["success"] is True

        # Resolve Operator Profile
        res_str = cyber_resolve_entities_handler({
            "action": "resolve",
            "seed_entity": "@suspect_dealer"
        })
        res = json.loads(res_str)
        assert res["linked_nodes_count"] >= 2
        assert "@suspect_dealer" in res["usernames"]
        assert "+919999999999" in res["phone_numbers"]

    def test_manage_intelligence_graph(self, tmp_path, monkeypatch):
        monkeypatch.setenv("RAKSHASTRA_HOME", str(tmp_path))

        # Add node
        res_str = cyber_manage_intelligence_graph_handler({
            "action": "add_node",
            "node_id": "test_suspect",
            "node_type": "suspect",
            "display_name": "Test Target"
        })
        res = json.loads(res_str)
        assert res["success"] is True

        # Add relation
        res_str = cyber_manage_intelligence_graph_handler({
            "action": "add_relation",
            "source_id": "test_suspect",
            "target_id": "another_node",
            "relation_type": "owns"
        })
        res = json.loads(res_str)
        assert res["success"] is True

        # Get network
        res_str = cyber_manage_intelligence_graph_handler({
            "action": "get_network",
            "suspect_id": "test_suspect"
        })
        res = json.loads(res_str)
        assert len(res["nodes"]) > 0

    def test_calculate_risk_and_prioritize(self):
        res_str = cyber_calculate_risk_and_prioritize_handler({
            "action": "calculate_score",
            "drug_probability": 0.8,
            "automation_confidence": 0.9,
            "platform_count": 3,
            "network_size": 12,
            "has_financials": True
        })
        res = json.loads(res_str)
        assert res["intelligence_risk_score"] > 0.5
        assert res["severity"] in ["HIGH", "CRITICAL"]

        # Prioritize watchlist
        targets = [
            {"name": "target_a", "drug_probability": 0.3},
            {"name": "target_b", "drug_probability": 0.9}
        ]
        res_str = cyber_calculate_risk_and_prioritize_handler({
            "action": "prioritize_watchlist",
            "targets": targets
        })
        res = json.loads(res_str)
        assert res[0]["name"] == "target_b"

    def test_log_audit_compliance(self):
        res_str = cyber_log_audit_compliance_handler({
            "action": "log_action",
            "audit_action": "test_collect",
            "target": "test_target",
            "source_data": "raw_log"
        })
        res = json.loads(res_str)
        assert res["lawfulness_status"] == "VERIFIED_PUBLIC_OSINT"
        assert res["target"] == "test_target"
