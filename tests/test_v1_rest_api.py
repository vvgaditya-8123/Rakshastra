import pytest
from fastapi.testclient import TestClient
from rakshastra_cli.web_server import app

client = TestClient(app)

def test_api_v1_status():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NOMINAL"
    assert data["api_version"] == "v1"

def test_api_v1_threat_analyze_text():
    payload = {
        "text": "need party stamps for weekend dm for MDMA rates",
        "has_image": True,
        "ocr_text": "contact telegram @DirectMedsExpress"
    }
    response = client.post("/api/v1/threat/analyze-text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "drug_probability_score" in data
    assert "reasons" in data
    assert "requires_investigation" in data
    assert data["drug_probability_score"] > 0.0

def test_api_v1_entity_correlate_link():
    payload = {
        "action": "link",
        "entity_a": "@DirectMedsExpress",
        "entity_b": "+919893212345"
    }
    response = client.post("/api/v1/entity/correlate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Linked @DirectMedsExpress" in data["message"]

def test_api_v1_entity_correlate_resolve():
    # Link first to make sure there is something to resolve
    client.post("/api/v1/entity/correlate", json={
        "action": "link",
        "entity_a": "@DirectMedsExpress",
        "entity_b": "+919893212345"
    })
    
    payload = {
        "action": "resolve",
        "seed_entity": "@DirectMedsExpress"
    }
    response = client.post("/api/v1/entity/correlate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "operator_id" in data
    assert "@DirectMedsExpress" in data["usernames"] or "@DirectMedsExpress" in data["resolved_identifiers"]

def test_api_v1_chat_analyze():
    payload = {
        "messages": [
            "/start",
            "bot online",
            "click start to buy ecstasy",
            "bot online"
        ]
    }
    response = client.post("/api/v1/chat/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "automation_confidence" in data
    assert "indicators" in data
    assert data["automation_confidence"] >= 0.6
    assert data["is_automated"] is True

def test_api_v1_ocr_analyze():
    payload = {
        "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    }
    response = client.post("/api/v1/ocr/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "ocr_text" in data
    assert "confidence" in data
    assert len(data["ocr_text"]) > 0

def test_api_v1_report_generate():
    payload = {
        "title": "Incident Intelligence Report",
        "report_type": "DRUG_TRAFFICKING",
        "executive_summary": "Detected drug trafficking operation on Telegram.",
        "findings": [{"id": "E1", "finding": "MDMA sales"}],
        "risk_summary": {"score": 0.85, "severity": "HIGH"},
        "recommendations": ["Report to law enforcement"]
    }
    response = client.post("/api/v1/report/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Incident Intelligence Report"
    assert data["report_type"] == "DRUG_TRAFFICKING"
    assert "generated_at" in data

def test_api_v1_risk_score():
    payload = {
        "drug_probability": 0.8,
        "automation_confidence": 0.7,
        "platform_count": 3,
        "network_size": 12,
        "has_financials": True
    }
    response = client.post("/api/v1/risk/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "intelligence_risk_score" in data
    assert "severity" in data
    assert data["intelligence_risk_score"] > 0.5

def test_api_v1_investigation_start():
    payload = {
        "session_id": "test_session_123"
    }
    response = client.post("/api/v1/investigation/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session_123"
    assert data["status"] == "started"
    assert data["current_phase"] == "recon"
    assert "guidance" in data
